#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RSI超卖反弹全市场扫描器
"""

import sys
import os



# ── 路径设置（相对路径，基于脚本所在目录）────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)
_SKILL_ROOT = os.path.dirname(_SKILL_DIR)
_BASE_DIR = os.path.dirname(_SKILL_ROOT)

if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import argparse
from datetime import datetime
from typing import List, Dict

from skills.scripts.analyzer import RSIOversoldAnalyzer
import yaml
import os


def scan_all_stocks(analyzer: RSIOversoldAnalyzer, top_n: int = 20) -> List[Dict]:
    """扫描全市场"""
    print(f"开始扫描全市场RSI超卖股票...")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"使用数据源: {analyzer.data_adapter.source}")
    print("-" * 60)
    
    # 获取股票列表
    try:
        stock_list = analyzer.data_adapter.get_stock_list()
        if stock_list is None or stock_list.empty:
            print("获取股票列表失败")
            return []
        print(f"获取到{len(stock_list)}只股票")
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return []
    
    candidates = []
    total = len(stock_list)
    
    for idx, (_, row) in enumerate(stock_list.iterrows(), 1):
        stock_code = row['code']
        stock_name = row.get('name', stock_code)
        
        # 进度显示
        if idx % 100 == 0:
            print(f"进度: {idx}/{total} ({idx/total*100:.1f}%)")
        
        # 分析
        result = analyzer.analyze_stock(stock_code, stock_name)
        if result and result['score'] >= 65:
            candidates.append(result)
            print(f"  ✅ {stock_name}({stock_code}): {result['score']}分")
    
    # 排序
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n扫描完成，发现{len(candidates)}只符合条件的股票")
    return candidates[:top_n]


def _load_watchlist():
    """加载自选股池"""
    path = os.path.join(_BASE_DIR, 'my_stock_pool', 'watchlist.yaml')
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get('watchlist', {})


def analyze_sector(analyzer: RSIOversoldAnalyzer, sector_name: str) -> List[Dict]:
    """分析指定板块（预定义板块）"""
    sectors = {
        '科技': ['000938', '000977', '002230', '002236', '002415', '300033', '300059', '600570', '600584', '603019'],
        '医药': ['000538', '000623', '000999', '002001', '002007', '300003', '300015', '600276', '600436', '603259'],
        '金融': ['000001', '000002', '600000', '600016', '600030', '600036', '600837', '601318', '601398', '601628'],
        '新能源': ['002074', '002129', '002202', '002594', '300014', '300124', '600438', '601012', '601727', '603806'],
        '半导体': ['002049', '002156', '300046', '300223', '300661', '600360', '600584', '603005', '603501', '688008'],
    }
    
    if sector_name not in sectors:
        print(f"未知板块: {sector_name}")
        print(f"可用板块: {', '.join(sectors.keys())}")
        return []
    
    stocks = sectors[sector_name]
    print(f"分析 {sector_name} 板块 ({len(stocks)}只股票)...")
    
    candidates = []
    for stock_code in stocks:
        print(f"  分析 {stock_code}...", end=' ')
        result = analyzer.analyze_stock(stock_code)
        if result and result['score'] >= 65:
            candidates.append(result)
            print(f"✅ {result['score']}分")
        else:
            print("❌")
    
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates


def analyze_watchlist(analyzer: RSIOversoldAnalyzer, sector: str = None, top_n: int = 20) -> List[Dict]:
    """分析自选股池，支持指定板块或全部"""
    watchlist = _load_watchlist()
    if not watchlist:
        print("❌ 无法加载自选股池 watchlist.yaml")
        return []

    if sector:
        sectors_to_scan = {sector: watchlist.get(sector, {'core': [], 'focus': []})}
    else:
        sectors_to_scan = watchlist

    print(f"📋 开始分析{'自选股池' + ('-' + sector if sector else '')}...")
    total_core = sum(len(d.get('core', [])) for d in sectors_to_scan.values())
    total_focus = sum(len(d.get('focus', [])) for d in sectors_to_scan.values())
    print(f"   core 标的: {total_core}只 | focus 标的: {total_focus}只")
    print(f"   数据源: {analyzer.data_adapter.source}")
    print("-" * 60)

    candidates = []
    seen_codes = set()
    stock_count = 0
    for sector_name, data in sectors_to_scan.items():
        all_stocks = data.get('core', []) + data.get('focus', [])
        tag = '⭐' if data.get('core') else '○'
        for name, code in all_stocks:
            stock_count += 1
            if stock_count % 20 == 0:
                print(f"  进度: {stock_count}只已分析...")
            if code in seen_codes:
                continue
            seen_codes.add(code)
            result = analyzer.analyze_stock(code, name)
            if result and result['score'] >= 65:
                result['sector'] = sector_name
                result['is_core'] = (name, code) in data.get('core', [])
                candidates.append(result)
                print(f"  ✅ [{tag}{sector_name}] {name}({code}): {result['score']}分")

    candidates.sort(key=lambda x: x['score'], reverse=True)
    print(f"\n分析完成，共发现 {len(candidates)} 只符合条件的股票")
    return candidates[:top_n]


def print_results(results: List[Dict], title: str = "扫描结果", market_env=None):
    """打印结果"""
    print("\n" + "="*80)
    print(f"RSI超卖反弹策略 - {title}")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if market_env:
        summary = market_env.get_summary()
        index_str = ', '.join([f"{n}{g:+.2f}%" for n, g in summary.get('指数涨跌', [])])
        print(f"📊 市场环境: 涨停{summary['涨停家数']}家 | 市场评分{summary['总分']}分 | {index_str}")
    
    print("="*80)
    print()
    
    if not results:
        print("未发现符合条件的股票（阈值: 65分）")
        print()
        print("说明：")
        print("  - 当前市场无RSI超卖股票")
        print("  - RSI值未低于30（超卖阈值）")
        print("  - 未出现止跌信号")
        return
    
    print(f"发现 {len(results)} 只符合条件的股票（阈值: 65分）")
    print()
    
    for i, r in enumerate(results, 1):
        emoji = '🔥' if r['score'] >= 78 else '✅' if r['score'] >= 65 else '👀'
        print(f"{emoji} {i}. {r['stock_name']}({r['stock_code']})")
        print(f"   综合得分: {r['score']}分 | 信号: {r['signal']}")
        print(f"   当前价: {r['current_price']}元 (今日{r['price_change_pct']:+.2f}%)")
        print(f"   RSI: {r['current_rsi']} ({r['rsi_status']}) | 价格偏离: -{r['price_deviation']}%")
        print(f"   量能变化: {r['volume_shrink']:+.1f}% | 止跌信号: {r['stability_signal']}")
        sd = r.get('score_details', {})
        mkt = sd.get('market_environment', '?')
        w = {'rsi_oversold': 0.25, 'price_recovery': 0.20, 'volume_confirm': 0.20, 'trend_reversal': 0.15, 'market_environment': 0.20}
        rsi_raw  = sd.get('rsi', 0)        # RSI综合原始分(0-100)
        pr_raw   = sd.get('price_recovery', 0)
        vol_raw  = sd.get('volume', 0)
        tr_raw   = sd.get('trend_reversal', 0)
        rsi_s  = rsi_raw * w['rsi_oversold']
        pr_s   = pr_raw * w['price_recovery']
        vol_s  = vol_raw * w['volume_confirm']
        tr_s   = tr_raw * w['trend_reversal']
        mk_s   = (mkt * w['market_environment']) if isinstance(mkt, (int, float)) else 0
        print(f"   原始分: RSI={rsi_raw:.0f} 反弹={pr_raw:.0f} 量能={vol_raw:.0f} 趋势={tr_raw:.0f} 市场={mkt:.0f}")
        print(f"   加权贡献: RSI:{rsi_s:.1f} + 反弹:{pr_s:.1f} + 量能:{vol_s:.1f} + 趋势:{tr_s:.1f} + 市场:{mk_s:.1f} = {rsi_s+pr_s+vol_s+tr_s+mk_s:.1f}")
        print()
    
    print("="*80)


def main():
    parser = argparse.ArgumentParser(description='RSI超卖反弹策略')
    parser.add_argument('--scan', action='store_true', help='扫描全市场')
    parser.add_argument('--stock', type=str, help='分析单只股票')
    parser.add_argument('--name', type=str, help='股票名称')
    parser.add_argument('--sector', type=str, help='分析板块（预定义板块）')
    parser.add_argument('--pool', type=str, default=None, const='all', nargs='?',
                       help='分析自选股池（my_stock_pool），可选：板块名或 all（全部）')
    parser.add_argument('--list-pools', action='store_true', help='列出所有自选股池板块')
    parser.add_argument('--top', type=int, default=20, help='显示前N名')
    parser.add_argument('--source', type=str, default='auto',
                       choices=['auto', 'akshare', 'tushare', 'baostock', 'yfinance'],
                       help='数据源选择')
    
    args = parser.parse_args()
    
    print("="*80)
    print("RSI超卖反弹策略")
    print("="*80)
    print()
    
    # 创建分析器
    try:
        analyzer = RSIOversoldAnalyzer(data_source=args.source)
    except RuntimeError as e:
        print(f"错误: {e}")
        print("\n请安装数据源:")
        print("  pip install akshare  # 推荐")
        print("  pip install baostock")
        return
    
    if args.scan:
        # 全市场扫描
        results = scan_all_stocks(analyzer, top_n=args.top)
        print_results(results, "全市场扫描", analyzer.market_env)
    
    elif args.sector:
        results = analyze_sector(analyzer, args.sector)
        print_results(results, f"{args.sector}板块分析", analyzer.market_env)
    
    elif args.list_pools:
        watchlist = _load_watchlist()
        if watchlist:
            print("📋 自选股池板块列表：")
            for s, d in watchlist.items():
                print(f"   {s}: core={len(d.get('core',[]))}, focus={len(d.get('focus',[]))}")
        else:
            print("❌ 无法加载自选股池")
    
    elif args.pool is not None:
        if args.pool == 'all':
            results = analyze_watchlist(analyzer, sector=None, top_n=args.top)
        else:
            results = analyze_watchlist(analyzer, sector=args.pool, top_n=args.top)
        print_results(results, f"自选股池-{args.pool}板块" if args.pool != 'all' else "全自选股池", analyzer.market_env)
    
    elif args.stock:
        # 单只股票分析
        result = analyzer.analyze_stock(args.stock, args.name)
        if result:
            print_results([result], "单股分析", analyzer.market_env)
        else:
            print(f"{args.stock} 未检测到RSI超卖信号")
            print()
            print("RSI超卖条件：")
            print("  1. RSI值 ≤ 30（超卖）")
            print("  2. 价格偏离20日均线 ≥ 8%")
            print("  3. 成交量明显萎缩")
            print("  4. 出现止跌信号")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
