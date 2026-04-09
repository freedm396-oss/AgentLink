#!/usr/bin/env python3
"""
港股分红除权博弈策略 - 演示脚本
HK Dividend Ex-Right Strategy Demo
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from hk_dividend_exright_analyzer import HKDividendExrightAnalyzer


def main():
    analyzer = HKDividendExrightAnalyzer()

    test_stocks = [
        ('0005.HK', '汇丰控股'),
        ('0011.HK', '恒生银行'),
        ('0016.HK', '新鸿基地产'),
    ]

    print("=" * 60)
    print("港股分红除权博弈策略 - 演示")
    print("=" * 60)

    for code, name in test_stocks:
        print(f"\n分析: {code} {name}")
        print("-" * 40)
        try:
            result = analyzer.analyze_stock(code, name)
            if result:
                print(f"  股息率: {result.get('dividend_yield', 0):.2f}% {'✅' if result.get('yield_ok') else '❌'}")
                print(f"  连续分红: {result.get('consecutive_years', 0)}年 {'✅' if result.get('history_ok') else '❌'}")
                print(f"  距除权日: {result.get('days_to_exright', 0)}日 {'✅' if result.get('timing_ok') else '❌'}")
                print(f"  预期涨幅: {result.get('expected_gain', 0):.2f}%")
                print(f"  市场状态: {result.get('market_status', 'N/A')} {'✅' if result.get('market_ok') else '❌'}")
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
