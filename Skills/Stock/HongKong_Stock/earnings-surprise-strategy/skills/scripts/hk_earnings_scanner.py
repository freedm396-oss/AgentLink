#!/usr/bin/env python3
"""
港股财报超预期策略 - 批量扫描器
HK Earnings Surprise Scanner
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from hk_earnings_analyzer import HKEarningsAnalyzer


# 港股大蓝筹列表
HK_STOCKS = [
    ('0700.HK', '腾讯控股'),
    ('9988.HK', '阿里巴巴'),
    ('3690.HK', '美团-W'),
    ('0941.HK', '中国移动'),
    ('0939.HK', '建设银行'),
    ('0992.HK', '联想集团'),
    ('1024.HK', '快手-W'),
    ('3888.HK', '金山软件'),
    ('2382.HK', '舜宇光学'),
    ('2018.HK', '瑞声科技'),
]


def scan_earnings_stocks(top_n=10):
    """扫描财报超预期港股"""
    analyzer = HKEarningsAnalyzer()
    results = []

    print(f"\n开始扫描 {len(HK_STOCKS)} 只港股财报超预期机会...")
    print("-" * 60)

    for symbol, name in HK_STOCKS:
        try:
            result = analyzer.analyze_stock(symbol, name)
            if result and result['score'] >= 70:
                results.append(result)
                print(f"  ✅ {symbol} {name}: "
                      f"超预期{result['eps_surprise']:.1f}% "
                      f"净利润+{result['net_profit_yoy']:.1f}% "
                      f"评分{result['score']} {result['signal']}")
            else:
                print(f"  ❌ {symbol} {name}: "
                      f"超预期{result['eps_surprise'] if result else 0:.1f}% "
                      f"评分{result['score'] if result else 0} {result['signal'] if result else 'N/A'}")
        except Exception as e:
            print(f"  ⚠️ {symbol} {name}: 错误 {e}")

    results.sort(key=lambda x: x['score'], reverse=True)

    print("\n" + "=" * 60)
    print(f"扫描结果: 共 {len(results)} 只符合条件（评分≥70）")
    print("=" * 60)

    for i, r in enumerate(results[:top_n], 1):
        print(f"\n{i}. {r['symbol']} {r['name']}")
        print(f"   评分: {r['score']} ({r['rating']})")
        print(f"   EPS超预期: {r['eps_surprise']:.1f}% | 净利润: +{r['net_profit_youd']:.1f}% | 营收: +{r['revenue_yoy']:.1f}%")
        print(f"   超预期: {r['surprise_level']} | 质量: {r['quality_level']} | 反应: {r['reaction_level']}")
        print(f"   信号: {r['signal']}")
        print(f"   入场: {r['entry_price']} | 止损: {r['stop_loss']} | 止盈: {r['take_profit']}")

    return results


def main():
    scan_earnings_stocks()


if __name__ == "__main__":
    main()
