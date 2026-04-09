#!/usr/bin/env python3
"""
港股沽空比率反转策略 - 演示脚本
HK Short Interest Reversal Strategy Demo
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from hk_short_reversal_analyzer import HKShortReversalAnalyzer


def main():
    analyzer = HKShortReversalAnalyzer()

    test_stocks = [
        ('0700.HK', '腾讯控股'),
        ('9988.HK', '阿里巴巴'),
        ('3690.HK', '美团-W'),
    ]

    print("=" * 60)
    print("港股沽空比率反转策略 - 演示")
    print("=" * 60)

    for code, name in test_stocks:
        print(f"\n分析: {code} {name}")
        print("-" * 40)
        try:
            result = analyzer.analyze_stock(code, name)
            if result:
                print(f"  当前沽空比率: {result.get('short_ratio', 0):.2f}%")
                print(f"  3日高沽空: {result.get('high_short_days', 0)}日")
                print(f"  连续下降: {result.get('consecutive_down_days', 0)}日")
                print(f"  量能倍数: {result.get('volume_ratio', 0):.2f}x MA20")
                print(f"  市值: {result.get('market_cap_b', 0):.1f}亿港元 {'✅' if result.get('market_cap_ok') else '❌'}")
                print(f"  综合评分: {result.get('score', 0)}")
                print(f"  信号: {result.get('signal', 'N/A')}")
                print(f"  入场价: {result.get('entry_price', 0):.2f}")
                print(f"  止损价: {result.get('stop_loss', 0):.2f}")
                print(f"  建议: {result.get('suggestion', 'N/A')}")
            else:
                print(f"  未能获取数据或不符合策略条件")
        except Exception as e:
            print(f"  错误: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
