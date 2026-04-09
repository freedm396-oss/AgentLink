#!/usr/bin/env python3
"""
港股均线多头排列策略 - 全市场扫描器
HK MA Bullish Arrangement Scanner
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from hk_ma_bullish_analyzer import HKBullishAnalyzer


# 恒生成分股示例列表（实际应从数据源获取完整列表）
HSI_STOCKS = [
    ('00700', '腾讯控股'),
    ('09988', '阿里巴巴'),
    ('03690', '美团-W'),
    ('00941', '中国移动'),
    ('00939', '建设银行'),
    ('00992', '联想集团'),
    ('01024', '快手-W'),
    ('02018', '瑞声科技'),
    ('03888', '金山软件'),
    ('06198', '青岛港'),
]


def scan_bullish_stocks(top_n=10):
    """扫描均线多头排列的港股"""
    analyzer = HKBullishAnalyzer()
    results = []

    print(f"\n开始扫描 {len(HSI_STOCKS)} 只港股通标的...")
    print("-" * 60)

    for symbol, name in HSI_STOCKS:
        try:
            result = analyzer.analyze_stock(symbol, name)
            if result and result['score'] >= 70:
                results.append(result)
                print(f"  ✅ {symbol} {name}: 评分{result['score']} {result['signal']}")
            else:
                print(f"  ❌ {symbol} {name}: 不符合条件")
        except Exception as e:
            print(f"  ⚠️ {symbol} {name}: 错误 {e}")

    # 排序输出
    results.sort(key=lambda x: x['score'], reverse=True)

    print("\n" + "=" * 60)
    print(f"扫描结果: 共 {len(results)} 只符合条件（评分≥70）")
    print("=" * 60)

    for i, r in enumerate(results[:top_n], 1):
        print(f"\n{i}. {r['symbol']} {r['name']}")
        print(f"   评分: {r['score']} ({r['rating']})")
        print(f"   均线: {r['ma_arrangement']}")
        print(f"   发散度: {r['ma_spread']:.2%}")
        print(f"   港股通: {r['southbound_holding']:.2%}")
        print(f"   信号: {r['signal']}")
        print(f"   入场: {r['entry_price']} | 止损: {r['stop_loss']} | 止盈: {r['take_profit']}")

    return results


def main():
    scan_bullish_stocks()


if __name__ == "__main__":
    main()
