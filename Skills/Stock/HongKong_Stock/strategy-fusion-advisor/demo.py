#!/usr/bin/env python3
"""
港股策略融合投资顾问 - 演示脚本
HK Strategy Fusion Advisor Demo
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from fusion_advisor import HKStrategyFusionAdvisor


def main():
    print("=" * 70)
    print("港股策略融合投资顾问 - 演示")
    print("=" * 70)
    print()

    advisor = HKStrategyFusionAdvisor()

    # 打印策略列表
    print("【融合策略列表】")
    print("-" * 70)
    for i, s in enumerate(advisor.strategies, 1):
        enabled = "✅" if s.get('enabled', True) else "❌"
        print(f"  {i:2d}. {s['display_name']:<20s} 胜率: {s['win_rate']*100:.0f}%  权重: {s['weight']:.2f} {enabled}")

    print()
    print("=" * 70)

    # 生成推荐
    result = advisor.generate_daily_recommendation()
    advisor.print_summary(result)

    print()
    print("演示完成!")


if __name__ == "__main__":
    main()
