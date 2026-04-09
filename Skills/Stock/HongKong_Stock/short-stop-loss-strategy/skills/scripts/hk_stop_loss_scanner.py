#!/usr/bin/env python3
"""
港股做空止损策略 - 批量扫描器
HK Stop Loss Scanner
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from hk_stop_loss_analyzer import HKStopLossAnalyzer


# 模拟持仓列表（实际应从持仓管理读取）
PORTFOLIOS = [
    {'symbol': '0700.HK', 'name': '腾讯控股', 'entry': 480.0, 'current': 450.0, 'holding_days': 5, 'daily_pnl': -0.03, 'weekly_pnl': -0.06},
    {'symbol': '9988.HK', 'name': '阿里巴巴', 'entry': 120.0, 'current': 115.0, 'holding_days': 3, 'daily_pnl': -0.015, 'weekly_pnl': -0.03},
    {'symbol': '3690.HK', 'name': '美团-W', 'entry': 95.0, 'current': 85.0, 'holding_days': 8, 'daily_pnl': -0.04, 'weekly_pnl': -0.08},
    {'symbol': '0941.HK', 'name': '中国移动', 'entry': 72.0, 'current': 68.0, 'holding_days': 15, 'daily_pnl': -0.02, 'weekly_pnl': -0.05},
    {'symbol': '0992.HK', 'name': '联想集团', 'entry': 10.5, 'current': 9.2, 'holding_days': 22, 'daily_pnl': -0.06, 'weekly_pnl': -0.12},
]


def scan_all_positions():
    """批量检查所有持仓"""
    analyzer = HKStopLossAnalyzer()
    alerts = []
    safe = []

    print(f"\n开始扫描 {len(PORTFOLIOS)} 个持仓止损状态...")
    print("=" * 60)

    for pos in PORTFOLIOS:
        try:
            result = analyzer.check_position(
                pos['symbol'], pos['entry'], pos['current'],
                pos['holding_days'], pos['daily_pnl'], pos['weekly_pnl']
            )
            if result['action'] in ['SELL', 'LIQUIDATE_ALL', 'REDUCE', 'FORCE_EXIT']:
                alerts.append(result)
                print(f"\n🚨 {pos['symbol']} {pos['name']}: {result['action_desc']}")
                print(f"   亏损: {result['pnl_pct']:.1f}% | 动作: {result['reason']}")
            else:
                safe.append(result)
                print(f"\n✅ {pos['symbol']} {pos['name']}: 安全持仓")
                print(f"   亏损: {result['pnl_pct']:.1f}% | 持仓: {result['holding_days']}日")
        except Exception as e:
            print(f"\n⚠️ {pos['symbol']}: 错误 {e}")

    print("\n" + "=" * 60)
    print(f"扫描汇总: 🚨 {len(alerts)} 个需处理 | ✅ {len(safe)} 个安全持仓")

    if alerts:
        print("\n需处理持仓:")
        for r in alerts:
            print(f"  - {r['symbol']}: {r['action_desc']} | {r['reason']} | 紧迫度: {r['urgency']}/100")

    return alerts, safe


def main():
    scan_all_positions()


if __name__ == "__main__":
    main()
