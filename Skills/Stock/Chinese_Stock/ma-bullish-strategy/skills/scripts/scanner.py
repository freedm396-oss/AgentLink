#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
均线多头排列策略 - 主扫描程序
支持自选股池扫描
"""

import sys
import os
sys.path.insert(0, '/home/qinliming/.npm-global/lib/node_modules/openclaw/skills/Stock/Chinese_Stock/ma-bullish-strategy')

import argparse
from datetime import datetime
from typing import List, Dict

from skills.scripts.analyzer import MABullishAnalyzer
from skills.scripts.sector_analyzer import SectorAnalyzer
import yaml


def _load_watchlist():
    """加载自选股池"""
    path = '/home/qinliming/.npm-global/lib/node_modules/openclaw/skills/Stock/Chinese_Stock/my_stock_pool/watchlist.yaml'
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get('watchlist', {})


def scan_all_stocks(analyzer: MABullishAnalyzer, top_n: int = 20) -> List[Dict]:
    """扫描全市场"""
    print(f"开始扫描全市场均线多头排列股票...")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"使用数据源: {analyzer.data_adapter.source}")
    print("-" * 60)

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

        if idx % 100 == 0:
            print(f"进度: {idx}/{total} ({idx/total*100:.1f}%)")

        result = analyzer.analyze_stock(stock_code, stock_name)
        if result and result.get('is_bullish') and result['score'] >= 70:
            candidates.append(result)
            print(f"  ✅ {stock_name}({stock_code}): {result['score']}分")

    candidates.sort(key=lambda x: x['score'], reverse=True)
    print(f"\n扫描完成，发现{len(candidates)}只符合条件的股票")
    return candidates[:top_n]


def analyze_watchlist(analyzer: MABullishAnalyzer, sector: str = None, top_n: int = 20) -> List[Dict]:
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
    total_core = sum(len(d['core']) for d in sectors_to_scan.values())
    total_focus = sum(len(d['focus']) for d in sectors_to_scan.values())
    print(f"   core 标的: {total_core}只 | focus 标的: {total_focus}只")
    print(f"   数据源: {analyzer.data_adapter.source}")
    print("-" * 60)

    candidates = []
    stock_count = 0
    for sector_name, data in sectors_to_scan.items():
        all_stocks = data.get('core', []) + data.get('focus', [])
        tag = '⭐' if data.get('core') else '○'
        for name, code in all_stocks:
            stock_count += 1
            if stock_count % 20 == 0:
                print(f"  进度: {stock_count}只已分析...")
            result = analyzer.analyze_stock(code, name)
            if result and result.get('is_bullish') and result['score'] >= 70:
                result['sector'] = sector_name
                result['is_core'] = (name, code) in data.get('core', [])
                candidates.append(result)
                print(f"  ✅ [{tag}{sector_name}] {name}({code}): {result['score']}分")

    candidates.sort(key=lambda x: x['score'], reverse=True)
    print(f"\n分析完成，共发现 {len(candidates)} 只符合条件的股票")
    return candidates[:top_n]


def print_results(results: List[Dict], title: str = "扫描结果"):
    """打印结果"""
    print("\n" + "="*80)
    print(f"均线多头排列策略 - {title}")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()

    if not results:
        print("未发现符合条件的股票")
        print()
        print("说明：")
        print("  - 当前市场无均线多头排列股票")
        print("  - 均线排列不符合要求")
        return

    print(f"发现 {len(results)} 只符合条件的股票")
    print()

    for i, r in enumerate(results, 1):
        emoji = '🔥' if r['score'] >= 85 else '✅' if r['score'] >= 75 else '👀'
        sector_tag = f"[{r.get('sector','?')}]" if 'sector' in r else ''
        core_tag = '⭐' if r.get('is_core') else ''
        print(f"{emoji} {i}. {r['name']}({r['code']}) {core_tag}{sector_tag}")
        print(f"   综合得分: {r['score']}分 | 信号: {r.get('signal', '多头排列')}")
        print(f"   当前价: {r.get('current_price', 'N/A')}元")
        print(f"   均线状态: {r.get('ma_status', 'N/A')}")
        print(f"   趋势强度: {r.get('trend_strength', 'N/A')}")
        print()

    print("="*80)


def main():
    parser = argparse.ArgumentParser(description='均线多头排列策略')
    parser.add_argument('--scan', action='store_true', help='扫描全市场')
    parser.add_argument('--stock', type=str, help='分析单只股票')
    parser.add_argument('--name', type=str, help='股票名称')
    parser.add_argument('--sector', type=str, help='分析预定义板块')
    parser.add_argument('--pool', type=str, default=None, const='all', nargs='?',
                       help='分析自选股池（my_stock_pool），可选：板块名或 all（全部）')
    parser.add_argument('--list-pools', action='store_true', help='列出所有自选股池板块')
    parser.add_argument('--top', type=int, default=20, help='显示前N名')
    parser.add_argument('--source', type=str, default='auto',
                       choices=['auto', 'akshare', 'tushare', 'baostock', 'yfinance'],
                       help='数据源选择')

    args = parser.parse_args()

    print("="*80)
    print("均线多头排列策略")
    print("="*80)
    print()

    try:
        analyzer = MABullishAnalyzer(data_source=args.source)
    except RuntimeError as e:
        print(f"错误: {e}")
        print("\n请安装数据源:")
        print("  pip install akshare  # 推荐")
        print("  pip install baostock")
        return

    if args.scan:
        results = scan_all_stocks(analyzer, top_n=args.top)
        print_results(results, "全市场扫描")

    elif args.sector:
        sector_analyzer = SectorAnalyzer(analyzer)
        results = sector_analyzer.analyze_sector(args.sector)
        results = [r for r in results if r.get('is_bullish')]
        print_results(results, f"{args.sector}板块分析")

    elif args.stock:
        result = analyzer.analyze_stock(args.stock, args.name)
        if result:
            print_results([result], "单股分析")
        else:
            print(f"{args.stock} 不符合均线多头排列条件")

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
        print_results(results, f"自选股池-{args.pool}板块" if args.pool != 'all' else "全自选股池")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
