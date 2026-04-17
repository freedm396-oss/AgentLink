#!/usr/bin/env python3
"""
缩量回踩重要均线策略 - 主扫描程序
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
import json

from skills.scripts.analyzer import VolumeRetraceAnalyzer
import yaml
import os


def scan_all_stocks(analyzer: VolumeRetraceAnalyzer, top_n: int = 20) -> List[Dict]:
    """扫描全市场"""
    print(f"开始扫描全市场股票... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"使用数据源: {analyzer.data_adapter.source}")
    
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
        if result and result['score'] >= 70:
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


def analyze_sector(analyzer: VolumeRetraceAnalyzer, sector_name: str) -> List[Dict]:
    """分析指定板块（预定义板块）"""
    sectors = {
        '科技': ['000938', '000977', '002230', '002236', '002415', '300033', '300059', '600570', '600584', '603019'],
        '医药': ['000538', '000623', '000999', '002001', '002007', '300003', '300015', '600276', '600436', '603259'],
        '金融': ['000001', '000002', '600000', '600016', '600030', '600036', '600837', '601318', '601398', '601628'],
        '新能源': ['002074', '002129', '002202', '002594', '300014', '300124', '600438', '601012', '601727', '603806'],
        '半导体': ['002049', '002156', '300046', '300223', '300661', '600360', '600584', '603005', '603501', '688008'],
        '存储': ['002049', '300223', '300661', '600667', '603501', '688008', '688018', '688123', '688256', '688525'],
        '创新药': ['002422', '002653', '300003', '300142', '300558', '600196', '600276', '688180', '688266', '688331'],
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
        if result and result['score'] >= 70:
            candidates.append(result)
            print(f"✅ {result['score']}分")
        else:
            print("❌")
    
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates


def analyze_watchlist(analyzer: VolumeRetraceAnalyzer, sector: str = None, top_n: int = 20) -> List[Dict]:
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
            if result and result['score'] >= 70:
                result['sector'] = sector_name
                result['is_core'] = (name, code) in data.get('core', [])
                candidates.append(result)
                print(f"  ✅ [{tag}{sector_name}] {name}({code}): {result['score']}分")

    candidates.sort(key=lambda x: x['score'], reverse=True)
    print(f"\n分析完成，共发现 {len(candidates)} 只符合条件的股票")
    return candidates[:top_n]


def print_report(results: List[Dict], title: str = "扫描报告"):
    """打印报告"""
    print("\n" + "="*80)
    print(f"缩量回踩重要均线策略 - {title}")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()
    
    if not results:
        print("未发现符合条件的股票")
        return
    
    print(f"发现 {len(results)} 只符合条件的股票")
    print()
    
    for i, r in enumerate(results, 1):
        emoji = '🔥' if r['score'] >= 80 else '✅' if r['score'] >= 70 else '👀'
        print(f"{emoji} {i}. {r['stock_name']}({r['stock_code']})")
        print(f"   综合得分: {r['score']}分 | 信号: {r['signal']}")
        print(f"   当前价: {r['current_price']}元")
        print(f"   回踩均线: {r['retrace_ma']} ({r['ma_price']}元)")
        print(f"   回调幅度: {r['retrace_pct']}%")
        print(f"   缩量程度: {r['volume_shrink']}% (前5日均量)")
        print(f"   止跌信号: {r['stop_signal']}")
        print()
    
    print("="*80)


def main():
    parser = argparse.ArgumentParser(description='缩量回踩重要均线策略')
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
    print("缩量回踩重要均线策略")
    print("="*80)
    print()
    
    # 创建分析器
    try:
        analyzer = VolumeRetraceAnalyzer(data_source=args.source)
    except RuntimeError as e:
        print(f"错误: {e}")
        print("\n请安装数据源:")
        print("  pip install akshare  # 推荐")
        print("  pip install baostock")
        return
    
    if args.scan:
        # 全市场扫描
        results = scan_all_stocks(analyzer, top_n=args.top)
        print_report(results, "全市场扫描")
    
    elif args.sector:
        results = analyze_sector(analyzer, args.sector)
        print_report(results, f"{args.sector}板块分析")
    
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
        print_report(results, f"自选股池-{args.pool}板块" if args.pool != 'all' else "全自选股池")
    
    elif args.stock:
        # 单只股票分析
        result = analyzer.analyze_stock(args.stock, args.name)
        if result:
            print_report([result], "单股分析")
        else:
            print(f"{args.stock} 不符合缩量回踩条件")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
