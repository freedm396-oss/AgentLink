#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财报超预期策略 - 全市场扫描入口
使用 baostock 多数据源获取真实财报数据

用法:
    python3 run_scanner.py --scan [--year Y] [--quarter Q] [--top N] [--min-score N]
    python3 run_scanner.py --stock CODE [--year Y] [--quarter Q]
    python3 run_scanner.py --demo  # 演示模式（20只代表性股票）
"""
import sys
import os

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

    return round(surprise_score * 0.30 + quality_score * 0.25 +
                 revenue_score * 0.20 + eps_score * 0.15 + 75 * 0.10, 2)


def scan_market(fetcher: MultiSourceEarningsFetcher, year: int, quarter: int,
                top_n: int, min_score: float):
    """全市场扫描"""
    print(f"\n{'='*60}")
    print(f"🔍 财报超预期 - 全市场扫描 {year}Q{quarter}")
    print(f"{'='*60}")
    print(f"  数据源: {', '.join(fetcher.available_sources)}")
    print(f"  最低评分: {min_score}分")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = fetcher.scan_market(year=year, quarter=quarter,
                                  top_n=200, min_score=min_score)

    if not results:
        print("  ❌ 未发现符合条件的股票")
        return

    print(f"\n{'='*60}")
    print(f"📊 扫描结果 (共 {len(results)} 只，评分≥{min_score})")
    print(f"{'='*60}")

    strong = [r for r in results if r['total_score'] >= 80]
    buy = [r for r in results if 70 <= r['total_score'] < 80]
    watch = [r for r in results if 60 <= r['total_score'] < 70]
    print(f"  🔥 强烈推荐(≥80分): {len(strong)}只")
    print(f"  ✅ 推荐(70-79分):   {len(buy)}只")
    print(f"  👀 关注(60-69分):   {len(watch)}只")
    print()

    print("【TOP20 榜单】")
    print("-" * 60)
    for i, r in enumerate(results[:top_n], 1):
        emoji, _ = get_signal(r['total_score'])
        price = r.get('current_price')
        price_str = f"{price:.2f}元" if price else 'N/A'
        print(f"{emoji} {i:2d}. {r['stock_name']}({r['stock_code']})")
        print(f"      评分: {r['total_score']}分 | {r['year']}Q{r['quarter']} | 现价: {price_str}")
        print(f"      净利润YOY: {r['net_profit_yoy']:+.2f}% | 营收YOY: {r['revenue_yoy']:+.2f}% | EPS: {r['eps']:.2f}")
        print(f"      ROE: {r['roe']:.2f}% | 毛利率: {r['gross_margin']:.2f}% | 净利率: {r['net_margin']:.2f}%")
        print()


def analyze_single(fetcher: MultiSourceEarningsFetcher, stock_code: str,
                  year: int, quarter: int):
    """单股分析"""
    earnings = fetcher.get_earnings(stock_code, year, quarter)
    if not earnings:
        print(f"  ❌ 无法获取 {stock_code} 财报数据（数据源无数据）")
        return

    price = fetcher.get_realtime_price(stock_code)
    if price:
        earnings['current_price'] = price

    score = calc_score(earnings)
    emoji, sig = get_signal(score)

    print(f"\n{'='*60}")
    print(f"📊 {stock_code} 财报分析 {emoji}")
    print(f"{'='*60}")
    print(f"  股票名称: {earnings['stock_name']}")
    print(f"  财报期:   {earnings['year']}Q{earnings['quarter']} (披露日: {earnings['pub_date']})")
    print(f"  综合评分: {score}分 / 信号: {sig}")
    print()
    print(f"  📈 业绩超预期:")
    print(f"     净利润YOY: {earnings['net_profit_yoy']:+.2f}%")
    print(f"     营收YOY:   {earnings['revenue_yoy']:+.2f}%")
    print(f"     EPS(TTM): {earnings['eps']:.2f} 元")
    print()
    print(f"  📐 增长质量:")
    print(f"     ROE:      {earnings['roe']:.2f}%")
    print(f"     毛利率:   {earnings['gross_margin']:.2f}%")
    print(f"     净利率:   {earnings['net_margin']:.2f}%")
    print(f"  💰 实时价格: {price if price else 'N/A'}")
    print(f"  数据来源: {earnings['source']}")
    print()


def main():
    parser = argparse.ArgumentParser(description='财报超预期策略 - 全市场扫描')
    parser.add_argument('--scan', action='store_true', help='全市场扫描')
    parser.add_argument('--demo', action='store_true', help='演示模式（20只代表性股票）')
    parser.add_argument('--stock', type=str, help='单只股票分析')
    parser.add_argument('--year', type=int, default=2024, help='财报年度 (默认2024)')
    parser.add_argument('--quarter', type=int, default=4, help='季度 1-4 (默认4)')
    parser.add_argument('--top', type=int, default=20, help='显示前N名 (默认20)')
    parser.add_argument('--min-score', type=float, default=60.0, help='最低评分 (默认60)')
    args = parser.parse_args()

    print("=" * 60)
    print("📈 财报超预期策略 - 多数据源版 (baostock)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    fetcher = MultiSourceEarningsFetcher()

    if not fetcher.available_sources:
        print("❌ 没有可用的数据源！")
        print("  baostock 需要能访问其服务器")
        print("  akshare 财报接口在当前环境被墙")
        return

    print(f"✅ 可用数据源: {', '.join(fetcher.available_sources)}")

    if args.stock:
        analyze_single(fetcher, args.stock, args.year, args.quarter)
    elif args.scan:
        scan_market(fetcher, args.year, args.quarter, args.top, args.min_score)
    elif args.demo:
        # 演示模式
        from run_demo import scan_demo
        scan_demo(fetcher, args.year, args.quarter, args.top)
    else:
        print("\n用法:")
        print("  python3 run_scanner.py --scan                      # 全市场扫描")
        print("  python3 run_scanner.py --demo                     # 演示模式（20只代表性股）")
        print("  python3 run_scanner.py --stock 600519             # 单股分析")
        print("  python3 run_scanner.py --stock 600519 --year 2024 --quarter 4")

    print()


if __name__ == '__main__':
    main()
