#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财报超预期策略 - 演示程序
使用 baostock 多数据源获取真实财报数据

用法:
    python3 run_demo.py [--stock CODE] [--top N] [--year Y] [--quarter Q]
"""
import sys
import os

# 添加 scripts 目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'skills', 'scripts'))

from earnings_fetcher_multi import MultiSourceEarningsFetcher
from risk_assessor import RiskAssessor
from datetime import datetime
import argparse


def get_signal(score):
    if score >= 80: return '🔥 强烈推荐', '强烈买入'
    if score >= 70: return '✅ 推荐', '买入'
    if score >= 60: return '👀 关注', '观望'
    return '❌ 暂缓', '观望'


def calc_score(e: dict) -> float:
    """综合评分（复用 fetcher 的评分逻辑）"""
    surprise_score = 0
    yoy = e.get('net_profit_yoy', 0)
    if yoy >= 50: surprise_score = 100
    elif yoy >= 30: surprise_score = 85
    elif yoy >= 20: surprise_score = 70
    elif yoy >= 10: surprise_score = 55
    elif yoy >= 0: surprise_score = 40
    else: surprise_score = 20

    quality_score = 0
    roe = e.get('roe', 0)
    gm = e.get('gross_margin', 0)
    if roe >= 20 and gm >= 30: quality_score = 100
    elif roe >= 15 and gm >= 20: quality_score = 80
    elif roe >= 10: quality_score = 65
    elif roe >= 5: quality_score = 50
    else: quality_score = 30

    revenue_score = 50
    ryoy = e.get('revenue_yoy', 0)
    if ryoy >= 30: revenue_score = 100
    elif ryoy >= 20: revenue_score = 80
    elif ryoy >= 10: revenue_score = 60

    eps_score = 50
    eps = e.get('eps', 0)
    if eps > 1: eps_score = 100
    elif eps >= 0.5: eps_score = 70

    total = (surprise_score * 0.30 + quality_score * 0.25 +
             revenue_score * 0.20 + eps_score * 0.15 + 75 * 0.10)
    return round(total, 2)


def analyze_single(fetcher: MultiSourceEarningsFetcher, stock_code: str, year: int, quarter: int):
    """分析单只股票"""
    print(f"\n{'='*60}")
    print(f"📊 {stock_code} 财报分析")
    print(f"{'='*60}")

    earnings = fetcher.get_earnings(stock_code, year, quarter)
    if not earnings:
        print(f"  无法获取 {stock_code} 的财报数据")
        return None

    price = fetcher.get_realtime_price(stock_code)
    if price:
        earnings['current_price'] = price

    score = calc_score(earnings)
    sig_emoji, sig_text = get_signal(score)

    print(f"  股票: {earnings['stock_name']}({stock_code})")
    print(f"  财报期: {earnings['year']}Q{earnings['quarter']} (披露日: {earnings['pub_date']})")
    print(f"  综合评分: {score}分 {sig_emoji}")
    print()
    print(f"  📈 业绩超预期:")
    print(f"     净利润YOY: {earnings['net_profit_yoy']:+.2f}%")
    print(f"     营收YOY:   {earnings['revenue_yoy']:+.2f}%")
    print(f"     EPS(TTM): {earnings['eps']:.2f} 元")
    print(f"  📐 增长质量:")
    print(f"     ROE:      {earnings['roe']:.2f}%")
    print(f"     毛利率:   {earnings['gross_margin']:.2f}%")
    print(f"     净利率:   {earnings['net_margin']:.2f}%")
    print(f"  💰 实时价格: {price if price else '获取失败'}")
    print(f"  数据来源: {earnings['source']}")

    # 风险评估
    risk = RiskAssessor()
    stock_data = {
        'current_price': price or 100,
        'market_cap': 1000,
        'avg_volume': 1000000,
        'volatility': 0.25
    }
    risk_result = risk.assess(stock_data)
    print(f"  ⚠️ 风险: {risk.get_risk_level_name(risk_result['risk_level'])} | 建议仓位: {risk_result['suggested_position']*100:.0f}%")

    return {'earnings': earnings, 'score': score, 'signal': sig_text}


def scan_demo(fetcher: MultiSourceEarningsFetcher, year: int, quarter: int, top_n: int):
    """演示扫描模式 - 扫描代表性股票"""
    print(f"\n{'='*60}")
    print(f"🔍 财报超预期扫描 - {year}Q{quarter}")
    print(f"{'='*60}")

    # A股代表性股票池
    demo_stocks = [
        ('600519', '贵州茅台'), ('000858', '五粮液'), ('000001', '平安银行'),
        ('600036', '招商银行'), ('002594', '比亚迪'), ('300750', '宁德时代'),
        ('601318', '中国平安'), ('600276', '恒瑞医药'), ('002415', '海康威视'),
        ('300059', '东方财富'), ('600900', '长江电力'), ('601012', '隆基绿能'),
        ('603259', '药明康德'), ('600585', '海螺水泥'), ('000333', '美的集团'),
        ('002236', '大华股份'), ('300015', '爱尔眼科'), ('600028', '中国石化'),
        ('601398', '工商银行'), ('600050', '中国联通'),
    ]

    results = []
    print(f"\n开始分析 {len(demo_stocks)} 只代表性股票...\n")

    for code, name in demo_stocks:
        sys.stdout.write(f"  分析 {name}({code})... ")
        sys.stdout.flush()
        e = fetcher.get_earnings(code, year, quarter)
        if e:
            price = fetcher.get_realtime_price(code)
            if price:
                e['current_price'] = price
            score = calc_score(e)
            sys.stdout.write(f"{score}分\n")
            sys.stdout.flush()
            results.append({**e, 'total_score': score})
        else:
            sys.stdout.write("无数据\n")
            sys.stdout.flush()

    results.sort(key=lambda x: x['total_score'], reverse=True)

    print(f"\n{'='*60}")
    print(f"📊 财报超预期策略 - {year}Q{quarter} 分析结果")
    print(f"{'='*60}")

    strong = sum(1 for r in results if r['total_score'] >= 75)
    buy = sum(1 for r in results if 70 <= r['total_score'] < 75)
    watch = sum(1 for r in results if 60 <= r['total_score'] < 70)
    print(f"  强烈推荐(≥75分): {strong}只 | 推荐(70-74分): {buy}只 | 关注(60-69分): {watch}只")
    print()

    for i, r in enumerate(results[:top_n], 1):
        emoji, _ = get_signal(r['total_score'])
        price_str = f"${r.get('current_price', 'N/A')}" if r.get('current_price') else 'N/A'
        print(f"{emoji} {i}. {r['stock_name']}({r['stock_code']})")
        print(f"   综合: {r['total_score']}分 | {r['year']}Q{r['quarter']} | 现价:{price_str}")
        print(f"   净利润YOY: {r['net_profit_yoy']:+.2f}% | 营收YOY: {r['revenue_yoy']:+.2f}% | EPS: {r['eps']:.2f}")
        print(f"   ROE: {r['roe']:.2f}% | 毛利率: {r['gross_margin']:.2f}% | 净利率: {r['net_margin']:.2f}%")
        print()


def main():
    parser = argparse.ArgumentParser(description='财报超预期策略')
    parser.add_argument('--stock', type=str, help='单只股票代码')
    parser.add_argument('--year', type=int, default=2024, help='财报年度')
    parser.add_argument('--quarter', type=int, default=4, help='季度(1-4)')
    parser.add_argument('--top', type=int, default=10, help='显示前N名')
    parser.add_argument('--scan', action='store_true', help='扫描演示股票池')
    args = parser.parse_args()

    print("=" * 60)
    print("📈 财报超预期策略 - 多数据源版")
    print(f"📅 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    fetcher = MultiSourceEarningsFetcher()
    print(f"\n✅ 数据源就绪: {', '.join(fetcher.available_sources) or '无可用数据源'}")
    if not fetcher.available_sources:
        print("❌ 没有可用的数据源，无法继续")
        return

    if args.stock:
        analyze_single(fetcher, args.stock, args.year, args.quarter)
    else:
        scan_demo(fetcher, args.year, args.quarter, args.top)

    print("\n✅ 分析完成")


if __name__ == '__main__':
    main()
