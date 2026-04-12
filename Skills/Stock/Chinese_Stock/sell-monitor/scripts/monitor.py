#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓实时监控 - 核心脚本 v3
基于策略类型的差异化止盈/止损
三层过滤：技术面 → 消息面 → 宏观确认
信号类型：减仓 / 加仓 / 持有
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# ── 代理清除 ───────────────────────────────────────────
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

import pandas as pd
import numpy as np
import akshare as ak

# ── 路径设置（相对路径，基于脚本所在目录）────────────────────
# monitor.py 位于 Chinese_Stock/sell-monitor/scripts/
# dirname ×2 → Chinese_Stock/
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))  # Chinese_Stock/
DEFAULT_PORTFOLIO_FILE = os.path.join(_BASE_DIR, 'my_holdings', 'portfolio.json')

def _get_latest_holdings_file() -> str:
    """获取最新的持仓文件（YYYYMMDD_holdings.json）"""
    import glob
    pattern = os.path.join(_BASE_DIR, 'my_holdings', '*_holdings.json')
    files = glob.glob(pattern)
    if files:
        return max(files, key=os.path.getmtime)
    # fallback: 回退到 holdings.json
    return os.path.join(_BASE_DIR, 'my_holdings', 'holdings.json')

# ── 本地模块 ────────────────────────────────────────────
sys.path.insert(0, _SCRIPT_DIR)

from indicators import calculate_rsi, calculate_macd, check_volume_anomaly
from news_sentiment import fetch_news_sentiment
from market_env import get_market_status
from strategy_config import (
    get_strategy_class,
    get_stop_loss,
    get_position_size_limit,
    calculate_profit_take,
    calculate_stop_loss_action,
    get_rsi_threshold,
    STRATEGY_CLASS,
    MARKET_STATUS_CONFIG,
)


def get_realtime_quote(stock_code: str) -> Optional[Dict]:
    """获取个股实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == stock_code]
        if row.empty:
            return None
        r = row.iloc[0]
        return {
            'code': stock_code,
            'name': r['名称'],
            'price': float(r['最新价']),
            'change_pct': float(r['涨跌幅']),
            'volume': float(r['成交量']),
            'amount': float(r['成交额']),
            'high': float(r['最高']),
            'low': float(r['最低']),
            'open': float(r['今开']),
            'pre_close': float(r['昨收']),
        }
    except Exception as e:
        print(f"[WARN] 获取 {stock_code} 实时行情失败: {e}")
        return None


def get_daily_indicators(stock_code: str) -> Optional[Dict]:
    """获取日线数据并计算技术指标"""
    try:
        end = datetime.now()
        start = (end - pd.Timedelta(days=60)).strftime('%Y%m%d')
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period='daily',
            start_date=start,
            end_date=end.strftime('%Y%m%d'),
            adjust=''
        )
        if df is None or len(df) < 30:
            return None
        df = df.tail(30).reset_index(drop=True)
        closes = df['收盘'].astype(float).values

        rsi = calculate_rsi(closes)
        macd_result = calculate_macd(closes)
        vol_anomaly = check_volume_anomaly(df)

        recent_high = df['最高'].astype(float).max()
        price_high_idx = df['最高'].astype(float).idxmax()
        macd_at_high = macd_result['dif'][price_high_idx] if price_high_idx < len(macd_result['dif']) else None

        return {
            'rsi': rsi,
            'macd': macd_result,
            'volume_anomaly': vol_anomaly,
            'recent_high': recent_high,
            'macd_at_high': macd_at_high,
            'closes': closes,
        }
    except Exception as e:
        print(f"[WARN] 计算 {stock_code} 日线指标失败: {e}")
        return None


def layer1_technical(trade_data: Dict, indicators: Dict) -> Dict:
    """第一层：技术面触发"""
    signals = {}

    # RSI
    rsi = indicators.get('rsi', 50)
    if rsi > 90:
        rsi_score = 100
    elif rsi > 85:
        rsi_score = 85
    elif rsi > 80:
        rsi_score = 70
    elif rsi > 70:
        rsi_score = 50
    else:
        rsi_score = 0

    # MACD
    macd_data = indicators.get('macd', {})
    dif = macd_data.get('dif', 0)
    dea = macd_data.get('dea', 0)
    macd_hist = macd_data.get('hist', 0)

    macd_dead_cross = (dif < dea) and (dif > 0) and (dea > 0)

    price_now = trade_data['price']
    recent_high = indicators.get('recent_high', price_now)
    macd_at_high = indicators.get('macd_at_high', dif)
    price_new_high = price_now > recent_high * 0.98
    macd_not_confirm = (macd_at_high is not None) and (dif < macd_at_high * 0.95)
    macd_bearish_div = price_new_high and macd_not_confirm

    macd_score = 100 if (macd_dead_cross or macd_bearish_div) else (50 if rsi > 70 else 0)

    # 成交量
    vol_anomaly = indicators.get('volume_anomaly', 'normal')
    vol_score = 80 if vol_anomaly == 'high_volume_top' else (60 if vol_anomaly == 'price_up_volume_down' else 0)

    signals['rsi'] = {'value': rsi, 'score': rsi_score}
    signals['macd'] = {
        'dif': round(dif, 4), 'dea': round(dea, 4), 'hist': round(macd_hist, 4),
        'dead_cross': macd_dead_cross, 'bearish_div': macd_bearish_div,
        'score': macd_score
    }
    signals['volume'] = {'status': vol_anomaly, 'score': vol_score}
    signals['total'] = round(rsi_score * 0.35 + macd_score * 0.30 + vol_score * 0.20 + 0 * 0.15, 2)

    return signals


def layer2_news(code: str, name: str) -> Dict:
    """第二层：消息面确认"""
    return fetch_news_sentiment(code, name)


def layer3_market() -> Dict:
    """第三层：宏观大盘确认"""
    return get_market_status()


def compute_action(
    trade_data: Dict,
    holding: Dict,
    indicators: Dict,
    news_signals: Dict,
    market: Dict
) -> Dict:
    """
    综合决策：结合止盈/止损 + 技术信号 + 消息面 + 大盘
    返回操作建议
    """
    code = holding['code']
    name = holding['name']
    buy_price = holding['buy_price']
    buy_reason = holding.get('buy_reason', 'default')
    strategy_cls = get_strategy_class(buy_reason)
    strategy_note = STRATEGY_CLASS.get(buy_reason, STRATEGY_CLASS['default'])['note']

    current_price = trade_data['price']
    profit_pct = (current_price - buy_price) / buy_price * 100
    loss_pct = -profit_pct if profit_pct < 0 else 0

    # ── Step 1: 止损检查（优先级最高）─────────────────────
    stop_action, stop_desc = calculate_stop_loss_action(loss_pct, buy_reason, current_price, buy_price)
    if stop_action:
        return {
            'signal': '🚨 止损',
            'action': stop_desc,
            'op_pct': int(stop_action * 100),
            'profit_pct': round(profit_pct, 2),
            'reason': '硬性止损',
            'strategy': strategy_note,
            'rsi': indicators.get('rsi', 0),
        }

    # ── Step 2: 止盈检查（盈利优先）───────────────────────
    rsi = indicators.get('rsi', 50)
    macd = indicators.get('macd', {})
    macd_bearish = macd.get('bearish_div', False)
    macd_dead_cross = macd.get('dead_cross', False)

    sell_pct, profit_desc = calculate_profit_take(profit_pct, buy_reason, rsi)

    if sell_pct > 0:
        action_desc = f"止盈：{profit_desc}"
        if macd_bearish or macd_dead_cross:
            action_desc += ' + MACD见顶信号'
        return {
            'signal': '💰 止盈建议',
            'action': action_desc,
            'op_pct': int(sell_pct * 100),
            'profit_pct': round(profit_pct, 2),
            'reason': f'盈利{profit_pct:.1f}%，{strategy_note}',
            'strategy': strategy_note,
            'rsi': rsi,
        }

    # ── Step 3: 加仓信号（仅保守/稳健策略）────────────────
    if strategy_cls in ('conservative', 'moderate'):
        vol_status = indicators.get('volume', {}).get('status', 'normal')
        volume_shrink = vol_status in ['price_up_volume_down']
        price_stabilizing = abs(trade_data['change_pct']) < 1.5

        if rsi < 30 and volume_shrink and price_stabilizing and loss_pct > 0:
            if loss_pct > 8:
                return {
                    'signal': '🟢 强烈加仓',
                    'action': f'浮亏{loss_pct:.1f}%+RSI<30+缩量，加仓摊薄成本',
                    'op_pct': -50,
                    'profit_pct': round(profit_pct, 2),
                    'reason': f'认可{strategy_note}逻辑，下跌加仓',
                    'strategy': strategy_note,
                    'rsi': rsi,
                }
            elif loss_pct > 3:
                return {
                    'signal': '🟢 加仓',
                    'action': f'浮亏{loss_pct:.1f}%+RSI<30，适量加仓',
                    'op_pct': -30,
                    'profit_pct': round(profit_pct, 2),
                    'reason': f'{strategy_note}，回调加仓',
                    'strategy': strategy_note,
                    'rsi': rsi,
                }

        # 趋势确认加仓（浮盈 + 趋势良好）
        if 50 <= rsi <= 65 and profit_pct > 5 and not macd_dead_cross:
            if profit_pct <= 15:
                return {
                    'signal': '🟢 趋势加仓',
                    'action': f'浮盈{profit_pct:.1f}%+RSI适中，适度加仓',
                    'op_pct': -20,
                    'profit_pct': round(profit_pct, 2),
                    'reason': f'{strategy_note}趋势确认',
                    'strategy': strategy_note,
                    'rsi': rsi,
                }

    # ── Step 4: 减仓信号（无盈利时看RSI/MACD）─────────────
    # 获取该策略的RSI阈值（已在顶层导入 get_rsi_threshold）
    rsi_threshold_warning = get_rsi_threshold(buy_reason)  # 触发减仓警告的RSI值
    rsi_threshold_attention = rsi_threshold_warning - 5  # 轻度注意的RSI值（比警告低5）

    if rsi > rsi_threshold_warning or (rsi > rsi_threshold_attention and (macd_bearish or macd_dead_cross)):
        return {
            'signal': '🔴 减仓警告',
            'action': f'RSI={rsi:.1f}（>{rsi_threshold_warning:.0f}），{"MACD顶背离" if macd_bearish else "MACD死叉"}',
            'op_pct': 30,
            'profit_pct': round(profit_pct, 2),
            'reason': f'{strategy_note}，但RSI过高',
            'strategy': strategy_note,
            'rsi': rsi,
        }

    if rsi > rsi_threshold_attention:
        return {
            'signal': '🟡 轻度注意',
            'action': f'RSI={rsi:.1f}（>{rsi_threshold_attention:.0f}），关注是否转空',
            'op_pct': 0,
            'profit_pct': round(profit_pct, 2),
            'reason': 'RSI偏高，继续持有需密切关注',
            'strategy': strategy_note,
            'rsi': rsi,
        }

    # ── Step 5: 继续持有 ─────────────────────────────────
    return {
        'signal': '🟢 继续持有',
        'action': '暂无特殊信号，安心持有',
        'op_pct': 0,
        'profit_pct': round(profit_pct, 2),
        'reason': f'{strategy_note}，状态正常',
        'strategy': strategy_note,
        'rsi': rsi,
    }


def calculate_portfolio_overview(holdings: List[Dict], results: Dict, market_status: str = 'neutral') -> Dict:
    """
    计算持仓组合概览
    market_status: strong / bullish / neutral / bearish / weak
    """
    from strategy_config import MARKET_STATUS_CONFIG

    # 计算当前总仓位（按成本价估算）
    total_cost = sum(h.get('position_value', 0) for h in holdings)
    total_value = sum(results.get(h['code'], {}).get('price', h['buy_price']) * h.get('shares', 0) for h in holdings)

    # 按成本计算仓位占比（假设position_ratio已记录在持仓中）
    current_position_ratio = sum(h.get('position_ratio', 0) for h in holdings)

    # 大盘允许的总仓位
    max_total_ratio = MARKET_STATUS_CONFIG.get(market_status, 0.50)

    # 可用仓位
    available_ratio = max(0, max_total_ratio - current_position_ratio)

    # 账户盈亏
    if total_cost > 0:
        profit_pct = (total_value - total_cost) / total_cost * 100
    else:
        profit_pct = 0.0

    # 各策略类型统计
    by_strategy = {}
    for h in holdings:
        reason = h.get('buy_reason', 'default')
        cls = get_strategy_class(reason)
        by_strategy[cls] = by_strategy.get(cls, 0) + h.get('position_ratio', 0)

    return {
        'holdings_count': len(holdings),
        'current_position_ratio': round(current_position_ratio * 100, 1),
        'max_total_ratio': round(max_total_ratio * 100, 1),
        'available_ratio': round(available_ratio * 100, 1),
        'profit_pct': round(profit_pct, 2),
        'market_status': market_status,
        'by_strategy': {k: round(v * 100, 1) for k, v in by_strategy.items()},
    }


def generate_portfolio_block(overview: Dict) -> str:
    """生成账户总览区块"""
    lines = []
    status_emoji = {
        'strong': '🟢',
        'bullish': '🟡',
        'neutral': '🟡',
        'bearish': '🟠',
        'weak': '🔴',
    }
    status_text = {
        'strong': '强势',
        'bullish': '震荡偏多',
        'neutral': '震荡',
        'bearish': '震荡偏空',
        'weak': '弱势',
    }

    emoji = status_emoji.get(overview['market_status'], '🟡')
    status = status_text.get(overview['market_status'], '震荡')

    lines.append(f"📊 账户总览  {emoji} 大盘：{status}")
    lines.append(f"总仓位：{overview['current_position_ratio']}%  /  上限：{overview['max_total_ratio']}%")
    lines.append(f"可用仓位：{overview['available_ratio']}%  |  持仓股票：{overview['holdings_count']}只")

    # 按策略类型显示仓位
    if overview['by_strategy']:
        strat_parts = []
        for cls, ratio in sorted(overview['by_strategy'].items()):
            strat_parts.append(f"{cls}:{ratio}%")
        lines.append(f"仓位分布：{', '.join(strat_parts)}")

    # 整体盈亏
    profit = overview['profit_pct']
    if profit >= 0:
        lines.append(f"持仓组合盈亏：{'+' if profit >= 0 else ''}{profit}%")
    else:
        lines.append(f"持仓组合盈亏：🔴{profit}%")

    return '  '.join(lines)


def generate_report(holdings: List[Dict], results: Dict, current_time: str, market_status: str = 'neutral') -> str:
    """生成格式化监控报告"""
    lines = []
    lines.append(f"🕐 {current_time} 持仓监控报告")
    lines.append("=" * 52)

    # 账户总览
    overview = calculate_portfolio_overview(holdings, results, market_status)
    lines.append(generate_portfolio_block(overview))
    lines.append("")

    # 信号汇总
    total = len(holdings)
    sell_signals = sum(1 for r in results.values() if '止盈' in r.get('signal', '') or '减仓' in r.get('signal', '') or '止损' in r.get('signal', ''))
    add_signals = sum(1 for r in results.values() if '加仓' in r.get('signal', ''))
    hold_signals = total - sell_signals - add_signals

    lines.append(f"持仓股票：{total}只  |  {add_signals}个加仓  |  {sell_signals}个减仓/止损  |  {hold_signals}个持有")
    lines.append("")

    for h in holdings:
        code = h['code']
        name = h['name']
        buy_price = h['buy_price']
        r = results.get(code, {})

        current_price = r.get('price', 0)
        change_pct = r.get('change_pct', 0)
        profit_pct = r.get('profit_pct', 0)
        strategy = r.get('strategy', '未知')

        lines.append("━" * 52)
        sig = r.get('signal', '数据获取中')
        emoji = '📌' if sig.startswith('🟢') else '⚠️'
        lines.append(f"{emoji} {name}({code})  [{strategy}]")
        lines.append(f"   现价: {current_price}  |  今日涨跌: {change_pct:+.2f}%  |  浮盈亏: {profit_pct:+.2f}%")
        lines.append(f"   持仓成本: {buy_price}  |  {'+' if profit_pct >= 0 else ''}{profit_pct:.2f}%")

        lines.append(f"\n   信号: {sig}")
        lines.append(f"   RSI(14): {r.get('rsi', 'N/A'):.1f}" if isinstance(r.get('rsi'), (int, float)) else f"   RSI(14): N/A")

        macd = r.get('technical', {}).get('macd', {}) if isinstance(r.get('technical'), dict) else {}
        if macd.get('dead_cross'):
            lines.append(f"   MACD: 🔴高位死叉")
        elif macd.get('bearish_div'):
            lines.append(f"   MACD: 🔴顶背离")
        else:
            lines.append(f"   MACD: DIF={macd.get('dif', 0):.2f} DEA={macd.get('dea', 0):.2f}")

        vol = r.get('technical', {}).get('volume', {}).get('status', 'N/A') if isinstance(r.get('technical'), dict) else 'N/A'
        lines.append(f"   成交量: {vol}")

        action = r.get('action', '暂无建议')
        op_pct = r.get('op_pct', 0)
        if op_pct > 0:
            lines.append(f"\n   ▶️ 建议: {action}（减仓 {op_pct}%）")
        elif op_pct < 0:
            lines.append(f"\n   ▶️ 建议: {action}（加仓 {abs(op_pct)}%）")
        else:
            lines.append(f"\n   ▶️ 建议: {action}")

        lines.append(f"   理由: {r.get('reason', '')}")

    lines.append("\n" + "=" * 52)
    lines.append("⚠️ 仅供参考，不构成投资建议")
    return '\n'.join(lines)


def monitor_holdings(holdings: List[Dict]) -> Dict:
    """主监控逻辑"""
    results = {}
    market = layer3_market()

    for h in holdings:
        code = h['code']
        name = h['name']

        trade_data = get_realtime_quote(code)
        if not trade_data:
            results[code] = {'error': '获取行情失败'}
            continue

        indicators = get_daily_indicators(code)
        news_signals = layer2_news(code, name)

        action_result = compute_action(trade_data, h, indicators or {}, news_signals, market)

        results[code] = {
            'price': trade_data['price'],
            'change_pct': trade_data['change_pct'],
            'technical': indicators or {},
            'news': news_signals,
            'market': market,
            **action_result,
        }

    return results


def load_portfolio_config() -> dict:
    """加载组合配置文件（手动覆盖）"""
    default = {'market_status': None}  # None表示自动判断
    if not os.path.exists(DEFAULT_PORTFOLIO_FILE):
        return default
    try:
        with open(DEFAULT_PORTFOLIO_FILE) as f:
            cfg = json.load(f)
        return cfg
    except Exception:
        return default


def main():
    parser = argparse.ArgumentParser(description='持仓实时监控 v3')
    parser.add_argument('--holdings', type=str, help='持仓JSON字符串')
    parser.add_argument('--holdings-file', type=str, help='持仓文件路径(JSON)')
    parser.add_argument('--market-status', type=str, choices=['strong','bullish','neutral','bearish','weak'],
                        help='大盘状态（strong/bullish/neutral/bearish/weak），覆盖自动判断')
    args = parser.parse_args()

    # 加载持仓
    if args.holdings:
        holdings = json.loads(args.holdings)
    elif args.holdings_file:
        with open(args.holdings_file) as f:
            holdings = json.load(f)
    else:
        holdings_file = _get_latest_holdings_file()
        if os.path.exists(holdings_file):
            with open(holdings_file) as f:
                holdings = json.load(f)
        else:
            print("❌ 未找到持仓文件，请先录入：")
            print("   python3 Chinese_Stock/my_holdings/scripts/holdings_editor.py")
            return

    if not holdings:
        print("🟢 持仓为空，无需监控")
        return

    # ── 大盘状态：优先用手动指定，其次用配置文件，最后自动判断 ───
    portfolio_config = load_portfolio_config()
    manual_status = args.market_status or portfolio_config.get('market_status')

    if manual_status:
        market_status = manual_status
        print(f"🔍 开始监控 {len(holdings)} 只持仓股票...")
        print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   大盘状态: {market_status} （手动设置）")
    else:
        print(f"🔍 开始监控 {len(holdings)} 只持仓股票...")
        print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   正在自动判断大盘状态...")
        from market_env import auto_market_status
        market_status = auto_market_status()
        print(f"   大盘状态: {market_status} （自动判断）")

    results = monitor_holdings(holdings)
    current_time = datetime.now().strftime('%H:%M')
    report = generate_report(holdings, results, current_time, market_status)
    print(report)

    # 保存结果
    output_path = '/tmp/sell_monitor_last_run.json'
    with open(output_path, 'w') as f:
        json.dump({'time': datetime.now().isoformat(), 'results': results}, f, ensure_ascii=False, indent=2)
    print(f"\n📄 结果已保存至 {output_path}")


if __name__ == '__main__':
    main()
