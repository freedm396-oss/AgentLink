#!/usr/bin/env python3
"""
港股回购公告跟进策略 - 演示脚本
HK Buyback Follow Strategy Demo
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from hk_buyback_analyzer import HKBuybackAnalyzer


def main():
    analyzer = HKBuybackAnalyzer()

    test_stocks = [
        ('0700.HK', '腾讯控股'),
        ('9988.HK', '阿里巴巴'),
        ('3690.HK', '美团-W'),
    ]

    print("=" * 60)
    print("港股回购公告跟进策略 - 演示")
    print("=" * 60)

    for code, name in test_stocks:
        print(f"\n分析: {code} {name}")
        print("-" * 40)
        try:
            result = analyzer.analyze_stock(code, name)
            if result:
                print(f"  回购均价: {result.get('buyback_avg_price', 0):.2f}")
                print(f"  当前价: {result.get('current_price', 0):.2f}")
                print(f"  偏离度: {result.get('price_discount', 0):.2f}% {'✅' if result.get('discount_ok') else '❌'}")
                print(f"  回购规模: {result.get('buyback_ratio', 0):.3f}% {'✅' if result.get('scale_ok') else '❌'}")
                print(f"  历史次数: {result.get('historical_count', 0)}次 {'✅' if result.get('history_ok') else '❌'}")
                print(f"  公告时效: {result.get('days_since_announce', 0)}日内 {'✅' if result.get('timing_ok') else '❌'}")
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
