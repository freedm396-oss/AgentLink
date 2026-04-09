#!/usr/bin/env python3
"""
港股流动性过滤策略 - 演示脚本
HK Liquidity Filter Strategy Demo
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from hk_liquidity_analyzer import HKLiquidityAnalyzer


def main():
    analyzer = HKLiquidityAnalyzer()

    test_stocks = [
        ('0700.HK', '腾讯控股'),
        ('0981.HK', '中芯国际'),
        ('0999.HK', '泡泡玛特'),
        ('0003.HK', '中华煤气'),
        ('0823.HK', '领展房产基金'),
    ]

    print("=" * 60)
    print("港股流动性过滤策略 - 演示")
    print("=" * 60)

    for code, name in test_stocks:
        print(f"\n检查: {code} {name}")
        print("-" * 40)
        try:
            result = analyzer.check_stock(code, name)
            if result['allowed']:
                print(f"  ✅ 允许交易")
                print(f"    日均成交额: {result['avg_volume_m']:.1f}M 港元")
                print(f"    换手率: {result['turnover_rate']:.3f}%")
                print(f"    买卖价差: {result['bid_ask_spread']:.3f}%")
                print(f"    市值: {result['market_cap_b']:.1f}B 港元")
                print(f"    综合评分: {result['score']}")
            else:
                print(f"  ❌ 拒绝交易")
                for reason in result['reject_reasons']:
                    print(f"    - {reason}")
                print(f"    综合评分: {result['score']}")
        except Exception as e:
            print(f"  错误: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
