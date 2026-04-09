#!/usr/bin/env python3
"""
港股做空止损策略 - 核心分析器
HK Short Stop Loss Analyzer
"""

import os
import sys
import yaml
from datetime import datetime


class HKStopLossAnalyzer:
    """止损分析器"""

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "config", "strategy_config.yaml"
            )
        self.config = self._load_config(config_path)

    def _load_config(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def calculate_pnl(self, entry_price, current_price):
        """计算盈亏比例"""
        if entry_price <= 0:
            return 0.0
        return (current_price - entry_price) / entry_price

    def check_hard_stop(self, pnl):
        """第1层：检查是否触及硬止损（-7%）"""
        threshold = self.config['stop_loss']['hard_stop_loss_pct']
        return pnl <= -threshold

    def check_daily_reduce(self, daily_pnl):
        """第2层：检查单日亏损是否触发减仓（-3%）"""
        threshold = self.config['stop_loss']['daily_loss_pct']
        return daily_pnl <= -threshold

    def check_weekly_stop(self, weekly_pnl):
        """第3层：检查周止损（-10%）"""
        threshold = self.config['stop_loss']['weekly_loss_pct']
        return weekly_pnl <= -threshold

    def check_max_holding(self, holding_days):
        """检查是否超过最大持仓期限"""
        max_days = self.config['holding']['max_days']
        return holding_days >= max_days

    def determine_action(self, pnl, daily_pnl, weekly_pnl, holding_days):
        """综合判断止损动作"""
        reasons = []

        # 第1优先级：硬止损
        if self.check_hard_stop(pnl):
            return 'SELL', '触及硬止损（亏损7%）', '立即市价卖出'

        # 第2优先级：周止损
        if self.check_weekly_stop(weekly_pnl):
            return 'LIQUIDATE_ALL', '周亏损超过10%', '清仓所有持仓'

        # 第3优先级：减仓
        if self.check_daily_reduce(daily_pnl):
            reduce_pct = self.config['stop_loss']['reduce_position_pct']
            return 'REDUCE', f'单日亏损超过3%，减仓{int(reduce_pct*100)}%', f'减仓{int(reduce_pct*100)}%，保留{int((1-reduce_pct)*100)}%'

        # 第4优先级：到期强制平仓
        if self.check_max_holding(holding_days):
            return 'FORCE_EXIT', f'持仓{holding_days}日到期', '到期强制平仓'

        # 安全持仓
        return 'HOLD', '未触及任何止损条件', '继续持有'

    def calculate_urgency(self, pnl, daily_pnl, weekly_pnl, holding_days):
        """计算止损紧迫度评分"""
        score = 0
        cfg = self.config['stop_loss']

        # 亏损深度
        if pnl <= -cfg['hard_stop_loss_pct']:
            score += 40
        elif pnl <= -0.05:
            score += 30
        elif pnl <= -0.03:
            score += 20
        elif pnl <= -0.01:
            score += 10

        # 单日亏损
        if daily_pnl <= -cfg['daily_loss_pct']:
            score += 25
        elif daily_pnl <= -0.02:
            score += 15
        elif daily_pnl <= -0.01:
            score += 8

        # 持仓期限
        if holding_days >= self.config['holding']['max_days']:
            score += 20
        elif holding_days >= 15:
            score += 12
        elif holding_days >= 10:
            score += 6

        # 周亏损
        if weekly_pnl <= -cfg['weekly_loss_pct']:
            score += 15
        elif weekly_pnl <= -0.07:
            score += 10
        elif weekly_pnl <= -0.05:
            score += 5

        return min(score, 100)

    def get_action_description(self, action):
        """获取动作描述"""
        descriptions = {
            'SELL': '⚠️ 立即止损卖出',
            'LIQUIDATE_ALL': '🚨 清仓所有持仓',
            'REDUCE': '⚡ 减仓保护',
            'FORCE_EXIT': '⏰ 到期强制平仓',
            'HOLD': '✅ 安全持仓',
            'WATCH': '👀 密切观察',
        }
        return descriptions.get(action, action)

    def check_position(self, symbol, entry_price, current_price,
                      holding_days, daily_pnl, weekly_pnl):
        """检查单个持仓的止损状态"""
        print(f"\n检查 {symbol} 止损状态...")

        # 计算亏损
        pnl = self.calculate_pnl(entry_price, current_price)
        pnl_pct = pnl * 100

        # 判断动作
        action, reason, suggestion = self.determine_action(pnl, daily_pnl, weekly_pnl, holding_days)

        # 计算紧迫度
        urgency = self.calculate_urgency(pnl, daily_pnl, weekly_pnl, holding_days)

        result = {
            'symbol': symbol,
            'entry_price': entry_price,
            'current_price': current_price,
            'pnl_pct': pnl_pct,
            'holding_days': holding_days,
            'daily_pnl': daily_pnl * 100,
            'weekly_pnl': weekly_pnl * 100,
            'action': action,
            'action_desc': self.get_action_description(action),
            'reason': reason,
            'suggestion': suggestion,
            'urgency': urgency,
        }

        return result

    def print_result(self, result):
        """打印结果"""
        action_color = {
            'SELL': '🔴',
            'LIQUIDATE_ALL': '🚨',
            'REDUCE': '🟡',
            'FORCE_EXIT': '⏰',
            'HOLD': '🟢',
            'WATCH': '👀',
        }.get(result['action'], '⚪')

        print(f"\n{'=' * 50}")
        print(f"{action_color} {result['symbol']}")
        print(f"{'=' * 50}")
        print(f"  入场价: {result['entry_price']} | 当前价: {result['current_price']}")
        print(f"  累计亏损: {result['pnl_pct']:.1f}%")
        print(f"  持仓天数: {result['holding_days']}日")
        print(f"  单日盈亏: {result['daily_pnl']:.1f}%")
        print(f"  周盈亏: {result['weekly_pnl']:.1f}%")
        print(f"  紧迫度: {result['urgency']}/100")
        print(f"  动作: {result['action_desc']}")
        print(f"  原因: {result['reason']}")
        print(f"  建议: {result['suggestion']}")
        print(f"{'=' * 50}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='港股止损检查')
    parser.add_argument('--stock', default='0700.HK', help='股票代码')
    parser.add_argument('--entry', type=float, default=480.0, help='入场价')
    parser.add_argument('--current', type=float, default=450.0, help='当前价')
    parser.add_argument('--days', type=int, default=5, help='持仓天数')
    parser.add_argument('--daily', type=float, default=-0.03, help='单日盈亏')
    parser.add_argument('--weekly', type=float, default=-0.06, help='周盈亏')
    args = parser.parse_args()

    analyzer = HKStopLossAnalyzer()
    result = analyzer.check_position(args.stock, args.entry, args.current,
                                     args.days, args.daily, args.weekly)
    analyzer.print_result(result)


if __name__ == "__main__":
    main()
