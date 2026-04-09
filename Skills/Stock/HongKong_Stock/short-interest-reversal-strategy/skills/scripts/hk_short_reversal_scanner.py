#!/usr/bin/env python3
"""
港股沽空比率反转策略 - 全市场扫描器
HK Short Interest Reversal Scanner
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from hk_short_reversal_analyzer import HKShortReversalAnalyzer


# 百亿市值以上港股示例列表
HK_STOCKS = [
    ('0700.HK', '腾讯控股'),
    ('9988.HK', '阿里巴巴'),
    ('3690.HK', '美团-W'),
    ('0941.HK', '中国移动'),
    ('0939.HK', '建设银行'),
    ('0992.HK', '联想集团'),
    ('1024.HK', '快手-W'),
    ('2018.HK', '瑞声科技'),
    ('3888.HK', '金山软件'),
    ('6198.HK', '青岛港'),
]


def scan_short_reversal_stocks(top_n=10):
    """扫描高市值港股沽空反转机会"""
    analyzer = HKShortReversalAnalyzer()
    results = []

    print(f"\n开始扫描 {len(HK_STOCKS)} 只百亿市值港股...")
    print("-" * 60)

    for symbol, name in HK_STOCKS:
        try:
            result = analyzer.analyze_stock(symbol, name)
            if result and result['score'] >= 70:
                results.append(result)
                print(f"  ✅ {symbol} {name}: 评分{result['score']} {result['signal']}")
            else:
                days = result['high_short_days'] if result else 0
                rev_days = result['consecutive_down_days'] if result else 0
                print(f"  ❌ {symbol} {name}: 高沽空{days}日/下降{rev_days}日")
        except Exception as e:
            print(f"  ⚠️ {symbol} {name}: 错误 {e}")

    results.sort(key=lambda x: x['score'], reverse=True)

    print("\n" + "=" * 60)
    print(f"扫描结果: 共 {len(results)} 只符合条件（评分≥70）")
    print("=" * 60)

    for i, r in enumerate(results[:top_n], 1):
        print(f"\n{i}. {r['symbol']} {r['name']}")
        print(f"   评分: {r['score']} ({r['rating']})")
        print(f"   沽空比率: {r['short_ratio']:.2f}%")
        print(f"   高沽空天数: {r['high_short_days']}日")
        print(f"   连续下降: {r['consecutive_down_days']}日")
        print(f"   量能: {r['volume_ratio']:.2f}x MA20")
        print(f"   市值: {r['market_cap_b']:.0f}亿港元")
        print(f"   信号: {r['signal']}")
        print(f"   入场: {r['entry_price']} | 止损: {r['stop_loss']} | 止盈: {r['take_profit']}")

    return results


def main():
    scan_short_reversal_stocks()


if __name__ == "__main__":
    main()
