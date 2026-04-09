#!/usr/bin/env python3
"""
港股做空止损策略 - 演示脚本
HK Short Stop Loss Strategy Demo
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'scripts'))

from hk_stop_loss_analyzer import HKStopLossAnalyzer


def main():
    analyzer = HKStopLossAnalyzer()

    # 模拟持仓场景
    test_positions = [
        {'symbol': '0700.HK', 'name': '腾讯控股', 'entry': 480.0, 'current': 450.0, 'holding_days': 5, 'daily_pnl': -0.03, 'weekly_pnl': -0.06},
        {'symbol': '9988.HK', 'name': '阿里巴巴', 'entry': 120.0, 'current': 115.0, 'holding_days': 3, 'daily_pnl': -0.015, 'weekly_pnl': -0.03},
        {'symbol': '3690.HK', 'name': '美团-W', 'entry': 95.0, 'current': 85.0, 'holding_days': 8, 'daily_pnl': -0.04, 'weekly_pnl': -0.08},
        {'symbol': '0941.HK', 'name': '中国移动', 'entry': 72.0, 'current': 68.0, 'holding_days': 15, 'daily_pnl': -0.02, 'weekly_pnl': -0.05},
        {'symbol': '0992.HK', 'name': '联想集团', 'entry': 10.5, 'current': 9.2, 'holding_days': 22, 'daily_pnl': -0.06, 'weekly_pnl': -0.12},
    ]

    print("=" * 60)
    print("港股做空止损策略 - 演示")
    print("=" * 60)

    for pos in test_positions:
        print(f"\n持仓检查: {pos['symbol']} {pos['name']}")
        print(f"  入场价: {pos['entry']} | 当前价: {pos['current']} | 持仓: {pos['holding_days']}日")
        print(f"  累计亏损: {(pos['current']/pos['entry']-1)*100:.1f}%")
        try:
            result = analyzer.check_position(
                pos['symbol'], pos['entry'], pos['current'],
                pos['holding_days'], pos['daily_pnl'], pos['weekly_pnl']
            )
            print(f"  动作: {result['action']} | 原因: {result['reason']}")
            print(f"  建议: {result['suggestion']}")
        except Exception as e:
            print(f"  错误: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
