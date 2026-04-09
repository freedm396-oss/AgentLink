#!/usr/bin/env python3
"""
港股分红除权博弈策略 - 全市场扫描器
HK Dividend Ex-Right Strategy Scanner
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from hk_dividend_exright_analyzer import HKDividendExrightAnalyzer


# 高息蓝筹港股示例列表
HK_DIVIDEND_STOCKS = [
    ('0005.HK', '汇丰控股'),
    ('0011.HK', '恒生银行'),
    ('0016.HK', '新鸿基地产'),
    ('0006.HK', '电能实业'),
    ('1038.HK', '长江基建'),
    ('0012.HK', '恒基地产'),
    ('0003.HK', '中华煤气'),
    ('0066.HK', '港铁公司'),
    ('3888.HK', '金山软件'),
    ('0939.HK', '建设银行'),
]


def scan_dividend_stocks(top_n=10):
    """扫描高息蓝筹除权机会"""
    analyzer = HKDividendExrightAnalyzer()
    results = []

    print(f"\n开始扫描 {len(HK_DIVIDEND_STOCKS)} 只高息蓝筹港股...")
    print("-" * 60)

    for symbol, name in HK_DIVIDEND_STOCKS:
        try:
            result = analyzer.analyze_stock(symbol, name)
            if result and result['score'] >= 70:
                results.append(result)
                print(f"  ✅ {symbol} {name}: 股息{result['dividend_yield']:.1f}% "
                      f"距除权{result['days_to_exright']}日 评分{result['score']} {result['signal']}")
            else:
                yld = result['dividend_yield'] if result else 0
                days = result['days_to_exright'] if result else 0
                print(f"  ❌ {symbol} {name}: 股息{yld:.1f}% 距除权{days}日")
        except Exception as e:
            print(f"  ⚠️ {symbol} {name}: 错误 {e}")

    results.sort(key=lambda x: x['score'], reverse=True)

    print("\n" + "=" * 60)
    print(f"扫描结果: 共 {len(results)} 只符合条件（评分≥70）")
    print("=" * 60)

    for i, r in enumerate(results[:top_n], 1):
        print(f"\n{i}. {r['symbol']} {r['name']}")
        print(f"   评分: {r['score']} ({r['rating']})")
        print(f"   股息率: {r['dividend_yield']:.2f}% | 连续分红: {r['consecutive_years']}年")
        print(f"   距除权日: {r['days_to_exright']}日 {'✅' if r['timing_ok'] else '❌'}")
        print(f"   大市: {r['market_status']} {'✅' if r['market_ok'] else '❌'}")
        print(f"   预期涨幅: ~{r['expected_gain']:.1f}%")
        print(f"   信号: {r['signal']}")
        print(f"   入场: {r['entry_price']} | 止损: {r['stop_loss']} | 出场: {r['exit_day']}")

    return results


def main():
    scan_dividend_stocks()


if __name__ == "__main__":
    main()
