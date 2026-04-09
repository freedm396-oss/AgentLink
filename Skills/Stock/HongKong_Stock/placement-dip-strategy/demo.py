#!/usr/bin/env python3
"""
港股配股砸盘抄底策略 - 演示脚本
HK Placement Dip Strategy Demo
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from hk_placement_analyzer import HKPlacementAnalyzer


def main():
    analyzer = HKPlacementAnalyzer()

    test_stocks = [
        ('0700.HK', '腾讯控股'),
        ('9988.HK', '阿里巴巴'),
        ('3690.HK', '美团-W'),
    ]

    print("=" * 60)
    print("港股配股砸盘抄底策略 - 演示")
    print("=" * 60)

    for code, name in test_stocks:
        print(f"\n分析: {code} {name}")
        print("-" * 40)
        try:
            result = analyzer.analyze_stock(code, name)
            if result:
                print(f"  配股折价: {result.get('placement_discount', 0):.2f}% {'✅' if result.get('discount_ok') else '❌'}")
                print(f"  公告日跌幅: {result.get('drop_magnitude', 0):.2f}% {'✅' if result.get('drop_ok') else '❌'}")
                print(f"  资金用途: {result.get('fund_usage', 'N/A')} {'✅' if result.get('usage_ok') else '❌'}")
                print(f"  机构参与: {result.get('institutional_count', 0)}家 {'✅' if result.get('inst_ok') else '❌'}")
                print(f"  综合评分: {result.get('score', 0)}")
                print(f"  信号: {result.get('signal', 'N/A')}")
                print(f"  入场价: {result.get('entry_price', 0):.2f}")
                print(f"  止损价: {result.get('stop_loss', 0):.2f}")
                print(f"  止盈: +12% 或 {result.get('max_days', 0)}日")
                print(f"  建议: {result.get('suggestion', 'N/A')}")
            else:
                print(f"  未能获取数据或不符合策略条件")
        except Exception as e:
            print(f"  错误: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
