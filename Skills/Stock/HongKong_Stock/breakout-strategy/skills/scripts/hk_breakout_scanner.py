#!/usr/bin/env python3
"""
港股突破高点策略 - 全市场扫描器
HK Breakout Strategy Scanner
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from hk_breakout_analyzer import HKBreakoutAnalyzer


# 高流动性港股示例列表
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


def scan_breakout_stocks(top_n=10):
    """扫描突破高点的港股"""
    analyzer = HKBreakoutAnalyzer()
    results = []

    print(f"\n开始扫描 {len(HK_STOCKS)} 只高流动性港股...")
    print("-" * 60)

    for symbol, name in HK_STOCKS:
        try:
            result = analyzer.analyze_stock(symbol, name)
            if result and result['score'] >= 70:
                results.append(result)
                print(f"  ✅ {symbol} {name}: 评分{result['score']} {result['signal']}")
            else:
                status = result['break_status'] if result else 'N/A'
                print(f"  ❌ {symbol} {name}: 未突破 ({status})")
        except Exception as e:
            print(f"  ⚠️ {symbol} {name}: 错误 {e}")

    results.sort(key=lambda x: x['score'], reverse=True)

    print("\n" + "=" * 60)
    print(f"扫描结果: 共 {len(results)} 只符合条件（评分≥70）")
    print("=" * 60)

    for i, r in enumerate(results[:top_n], 1):
        print(f"\n{i}. {r['symbol']} {r['name']}")
        print(f"   评分: {r['score']} ({r['rating']})")
        print(f"   突破: {r['break_status']} ({r['break_ratio']:.2%})")
        print(f"   量能: {r['volume_ratio']:.2f}x MA50")
        print(f"   回踩: {r['pullback_status']}")
        print(f"   RSI: {r['rsi_str']}")
        print(f"   信号: {r['signal']}")
        print(f"   入场: {r['entry_price']} | 止损: {r['stop_loss']} | 止盈: {r['take_profit']}")

    return results


def main():
    scan_breakout_stocks()


if __name__ == "__main__":
    main()
