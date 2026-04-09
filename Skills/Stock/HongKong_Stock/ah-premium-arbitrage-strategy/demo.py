#!/usr/bin/env python3
"""
港股AH溢价套利策略 - 演示脚本
HK AH Premium Arbitrage Strategy Demo
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from hk_ah_arbitrage_analyzer import HKAHPremiumAnalyzer


def main():
    analyzer = HKAHPremiumAnalyzer()

    # A+H股示例：代码为港股代码，A股代码通过规则映射
    test_stocks = [
        ('0700', '腾讯控股', '00700'),   # 腾讯无A股，直接模拟
        ('0992', '联想集团', '00992'),   # 联想无A股，直接模拟
        ('3869', '中国化工', '600028'),  # 中国石化 A+H
    ]

    print("=" * 60)
    print("港股AH溢价套利策略 - 演示")
    print("=" * 60)

    for hk_code, name, a_code in test_stocks:
        print(f"\n分析: {hk_code} {name} (A股:{a_code})")
        print("-" * 40)
        try:
            result = analyzer.analyze_stock(hk_code, name, a_code)
            if result:
                print(f"  AH溢价率: {result.get('ah_premium', 0):.2f}%")
                print(f"  H股价格: {result.get('h_price', 0):.2f} 港元")
                print(f"  A股价格: {result.get('a_price', 0):.2f} 人民币")
                print(f"  H股量能: {result.get('h_volume_m', 0):.1f}M 港元 {'✅' if result.get('h_volume_ok') else '❌'}")
                print(f"  A股量能: {result.get('a_volume_m', 0):.1f}M 人民币 {'✅' if result.get('a_volume_ok') else '❌'}")
                print(f"  行业趋势: {result.get('sector_trend', 'N/A')} {'✅' if result.get('sector_ok') else '❌'}")
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
