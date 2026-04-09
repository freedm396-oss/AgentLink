#!/usr/bin/env python3
"""
港股止损检查器 - 单持仓检查工具
HK Stop Loss Checker
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from hk_stop_loss_analyzer import HKStopLossAnalyzer


def main():
    import argparse
    parser = argparse.ArgumentParser(description='港股止损检查')
    parser.add_argument('--stock', required=True, help='股票代码')
    parser.add_argument('--entry', type=float, required=True, help='入场价')
    parser.add_argument('--current', type=float, required=True, help='当前价')
    parser.add_argument('--days', type=int, default=5, help='持仓天数')
    parser.add_argument('--daily', type=float, default=-0.03, help='单日盈亏（负数）')
    parser.add_argument('--weekly', type=float, default=-0.06, help='周盈亏（负数）')
    args = parser.parse_args()

    analyzer = HKStopLossAnalyzer()
    result = analyzer.check_position(args.stock, args.entry, args.current,
                                     args.days, args.daily, args.weekly)
    analyzer.print_result(result)


if __name__ == "__main__":
    main()
