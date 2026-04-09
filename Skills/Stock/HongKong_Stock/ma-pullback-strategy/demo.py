# skills/scripts/demo.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
港股缩量回踩均线策略演示脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from hk_ma_pullback_analyzer import HKMaPullbackAnalyzer
from hk_ma_pullback_scanner import HKMaPullbackScanner
import json


def demo_single_stock():
    """演示单只港股分析"""
    print("\n" + "=" * 60)
    print("演示1：单只港股分析")
    print("=" * 60)
    
    analyzer = HKMaPullbackAnalyzer()
    result = analyzer.analyze_stock('00700', '腾讯控股')
    
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("当前无回踩信号")


def demo_scanner():
    """演示扫描功能"""
    print("\n" + "=" * 60)
    print("演示2：港股全市场扫描")
    print("=" * 60)
    
    scanner = HKMaPullbackScanner()
    results = scanner.scan_all(top_n=5)
    
    print(f"\n发现 {len(results)} 只港股回踩机会")


def demo_hk_parameters():
    """演示港股特化参数"""
    print("\n" + "=" * 60)
    print("演示3：港股特化参数")
    print("=" * 60)
    
    analyzer = HKMaPullbackAnalyzer()
    
    print(f"20日均线周期: {analyzer.ma_period}")
    print(f"缩量阈值: {analyzer.shrink_ratio} (成交量<60%均量)")
    print(f"最小成交额: {analyzer.min_avg_volume/10000:.0f}万港元")
    print(f"最小股价: {analyzer.min_price}港元（排除仙股）")
    print(f"最小市值: {analyzer.min_market_cap/1e8:.0f}亿港元")
    print(f"止损幅度: 7%")
    print(f"止盈目标: 8% / 12% / 15%")


def demo_liquidity_filter():
    """演示流动性过滤"""
    print("\n" + "=" * 60)
    print("演示4：港股流动性过滤条件")
    print("=" * 60)
    
    print("\n合格条件:")
    print("  ✅ 股价 > 1港元（排除仙股）")
    print("  ✅ 市值 > 100亿港元（机构股）")
    print("  ✅ 日均成交额 > 2000万港元（流动性好）")
    print("  ✅ 20日线斜率向上（上升趋势）")
    
    print("\n不合格示例:")
    print("  ❌ 股价0.5港元 - 仙股，流动性差")
    print("  ❌ 成交额500万港元 - 流动性不足")
    print("  ❌ 20日线向下 - 下跌趋势")


if __name__ == '__main__':
    print("港股缩量回踩均线策略演示")
    print("-" * 60)
    
    demo_hk_parameters()
    demo_liquidity_filter()
    demo_single_stock()
    demo_scanner()
    
    print("\n✅ 演示完成")
    print("\n使用说明:")
    print("  1. 分析个股: python hk_ma_pullback_analyzer.py --stock 00700 --name 腾讯控股")
    print("  2. 全市场扫描: python hk_ma_pullback_scanner.py")