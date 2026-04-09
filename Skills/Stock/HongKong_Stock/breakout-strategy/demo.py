#!/usr/bin/env python3
"""
港股突破高点策略 - 演示脚本
HK Breakout Strategy Demo
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from hk_breakout_analyzer import HKBreakoutAnalyzer


def main():
    analyzer = HKBreakoutAnalyzer()

    test_stocks = [
        ('0700.HK', '腾讯控股'),
        ('9988.HK', '阿里巴巴'),
        ('3690.HK', '美团-W'),
    ]

    print("=" * 60)
    print("港股突破高点策略 - 演示")
    print("=" * 60)

    for code, name in test_stocks:
        print(f"\n分析: {code} {name}")
        print("-" * 40)
        try:
            result = analyzer.analyze_stock(code, name)
            if result:
                print(f"  突破状态: {result.get('break_status', 'N/A')}")
                print(f"  60日最高价: {result.get('highest_60d', 0):.2f}")
                print(f"  量能倍数: {result.get('volume_ratio', 0):.2f}x")
                print(f"  RSI(14): {result.get('rsi', 0):.1f}")
                print(f"  回踩状态: {result.get('pullback_status', 'N/A')}")
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
