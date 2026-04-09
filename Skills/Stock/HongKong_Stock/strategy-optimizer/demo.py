#!/usr/bin/env python3
"""
港股策略优化器 - 演示脚本
HK Strategy Optimizer Demo
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from strategy_optimizer import StrategyOptimizer


def print_header():
    print("=" * 80)
    print("港股策略优化器 - 演示")
    print("=" * 80)
    print(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def print_strategy_list():
    strategies = [
        ("ma-bullish-strategy", "均线多头排列策略", "65%"),
        ("breakout-strategy", "突破高点策略", "58%"),
        ("short-interest-reversal-strategy", "沽空比率反转策略", "70%"),
        ("ah-premium-arbitrage-strategy", "AH溢价套利策略", "74%"),
        ("buyback-follow-strategy", "回购公告跟进策略", "62%"),
        ("placement-dip-strategy", "配股砸盘抄底策略", "60%"),
        ("dividend-exright-strategy", "分红除权博弈策略", "67%"),
        ("liquidity-filter-strategy", "流动性过滤策略", "风控"),
        ("short-stop-loss-strategy", "做空止损策略", "风控"),
        ("ma-pullback-strategy", "均线回踩策略", "待测"),
    ]

    print("=" * 80)
    print("可优化的港股策略列表 (10个)")
    print("=" * 80)
    for i, (name, desc, winrate) in enumerate(strategies, 1):
        print(f"  {i:2d}. {desc:<20s} | 胜率: {winrate:<6s} | {name}")
    print()
    print("=" * 80)


def print_optimization_example():
    print("=" * 80)
    print("优化过程示例 - ma-bullish-strategy")
    print("=" * 80)
    print()

    print("步骤1: 加载回测数据")
    print("  ✅ 加载120条模拟港股交易记录")
    print()

    print("步骤2: 分析当前表现")
    print("  📊 胜率: 63.00%")
    print("  📊 夏普比率: 1.35")
    print("  📊 最大回撤: 8.20%")
    print("  📊 盈亏比: 1.80")
    print()

    print("步骤3: 执行参数优化 (网格搜索)")
    print("  🔍 生成48个参数组合")
    print("  📈 最佳得分: 72.50")
    print()

    print("步骤4: 优化参数建议")
    print("  📋 ma_spread_threshold: 0.06 (原0.05)")
    print("  📋 southbound_min: 0.06 (原0.05)")
    print("  📋 volume_ratio: 1.3 (原1.2)")
    print()

    print("步骤5: 验证优化效果")
    print("  ✅ 胜率提升: +3.20%")
    print("  ✅ 夏普提升: +0.15")
    print("  ✅ 回撤降低: -1.50%")
    print()

    print("=" * 80)


def print_all_results():
    print("=" * 80)
    print("优化结果摘要 (模拟)")
    print("=" * 80)
    print(f"{'策略名称':<35} {'状态':<6} {'组合数':<8} {'最佳得分':<10}")
    print("-" * 80)

    results = [
        ("ma-bullish-strategy", "✅", "48", "72.50"),
        ("breakout-strategy", "✅", "36", "68.30"),
        ("short-interest-reversal-strategy", "✅", "32", "75.10"),
        ("ah-premium-arbitrage-strategy", "✅", "24", "70.20"),
        ("buyback-follow-strategy", "✅", "40", "65.40"),
        ("placement-dip-strategy", "✅", "36", "67.80"),
        ("dividend-exright-strategy", "✅", "28", "73.60"),
        ("liquidity-filter-strategy", "⚙️", "-", "风控层"),
        ("short-stop-loss-strategy", "⚙️", "-", "风控层"),
        ("ma-pullback-strategy", "❌", "-", "待创建"),
    ]

    for name, status, combos, score in results:
        print(f"{name:<35} {status:<6} {combos:<8} {score:<10}")

    print()
    success = sum(1 for _, s, _, _ in results if s == "✅")
    print(f"统计: 成功优化 {success}/10 个策略")
    print("=" * 80)


def print_usage():
    print("\n使用方法:")
    print("  1. 优化所有策略:")
    print("     python3 skills/scripts/strategy_optimizer.py --all")
    print()
    print("  2. 优化单个策略:")
    print("     python3 skills/scripts/strategy_optimizer.py --strategy ma-bullish-strategy")
    print()
    print("  3. 优化评分权重:")
    print("     python3 skills/scripts/strategy_optimizer.py --weights ma-bullish-strategy")
    print()


def main():
    print_header()
    print_strategy_list()
    print_optimization_example()
    print_all_results()
    print_usage()
    print("演示完成!")


if __name__ == "__main__":
    main()
