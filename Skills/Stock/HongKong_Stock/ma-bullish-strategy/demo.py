#!/usr/bin/env python3
"""
港股均线多头排列策略 - 演示脚本
HK MA Bullish Strategy Demo
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from hk_ma_bullish_analyzer import HKBullishAnalyzer


def main():
    analyzer = HKBullishAnalyzer()

    # 演示用股票代码（可替换为实际代码）
    test_stocks = [
        ('0700.HK', '腾讯控股'),
        ('9988.HK', '阿里巴巴'),
        ('3690.HK', '美团-W'),
    ]

    print("=" * 60)
    print("港股均线多头排列策略 - 演示")
    print("=" * 60)

    for code, name in test_stocks:
        print(f"\n分析: {code} {name}")
        print("-" * 40)
        try:
            result = analyzer.analyze_stock(code, name)
            if result:
                print(f"  均线排列: {result.get('ma_arrangement', 'N/A')}")
                print(f"  发散度: {result.get('ma_spread', 0):.2%}")
                print(f"  港股通持股: {result.get('southbound_holding', 0):.2%}")
                print(f"  量能状态: {result.get('volume_status', 'N/A')}")
                print(f"  综合评分: {result.get('score', 0)}")
                print(f"  信号: {result.get('signal', 'N/A')}")
                print(f"  建议: {result.get('suggestion', 'N/A')}")
            else:
                print(f"  未能获取数据或不符合策略条件")
        except Exception as e:
            print(f"  错误: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
