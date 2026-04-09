#!/usr/bin/env python3
"""
港股财报超预期策略 - 演示脚本
HK Earnings Surprise Strategy Demo
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from hk_earnings_analyzer import HKEarningsAnalyzer


def main():
    analyzer = HKEarningsAnalyzer()

    test_stocks = [
        ('0700.HK', '腾讯控股'),
        ('9988.HK', '阿里巴巴'),
        ('3690.HK', '美团-W'),
        ('0941.HK', '中国移动'),
        ('0939.HK', '建设银行'),
    ]

    print("=" * 60)
    print("港股财报超预期策略 - 演示")
    print("=" * 60)

    for code, name in test_stocks:
        print(f"\n分析: {code} {name}")
        print("-" * 40)
        try:
            result = analyzer.analyze_stock(code, name)
            if result:
                print(f"  净利润增长: {result.get('net_profit_yoy', 0):.1f}%")
                print(f"  营收增长: {result.get('revenue_yoy', 0):.1f}%")
                print(f"  EPS超预期: {result.get('eps_surprise', 0):.1f}%")
                print(f"  超预期评分: {result.get('surprise_score', 0):.0f}/100")
                print(f"  增长质量: {result.get('quality_level', 'N/A')}")
                print(f"  市场反应: {result.get('reaction_level', 'N/A')}")
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
