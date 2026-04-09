#!/usr/bin/env python3
"""
港股回购公告跟进策略 - 全市场扫描器
HK Buyback Follow Strategy Scanner
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from hk_buyback_analyzer import HKBuybackAnalyzer


# 持续回购的港股示例列表
HK_BUYBACK_STOCKS = [
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


def scan_buyback_stocks(top_n=10):
    """扫描回购公告跟进机会"""
    analyzer = HKBuybackAnalyzer()
    results = []

    print(f"\n开始扫描 {len(HK_BUYBACK_STOCKS)} 只持续回购港股...")
    print("-" * 60)

    for symbol, name in HK_BUYBACK_STOCKS:
        try:
            result = analyzer.analyze_stock(symbol, name)
            if result and result['score'] >= 70:
                results.append(result)
                print(f"  ✅ {symbol} {name}: 偏离{result['price_discount']:.1f}% "
                      f"评分{result['score']} {result['signal']}")
            else:
                disc = result['price_discount'] if result else 0
                print(f"  ❌ {symbol} {name}: 偏离{disc:.1f}%")
        except Exception as e:
            print(f"  ⚠️ {symbol} {name}: 错误 {e}")

    results.sort(key=lambda x: x['score'], reverse=True)

    print("\n" + "=" * 60)
    print(f"扫描结果: 共 {len(results)} 只符合条件（评分≥70）")
    print("=" * 60)

    for i, r in enumerate(results[:top_n], 1):
        print(f"\n{i}. {r['symbol']} {r['name']}")
        print(f"   评分: {r['score']} ({r['rating']})")
        print(f"   当前价: {r['current_price']:.2f} | 回购均价: {r['buyback_avg_price']:.2f}")
        print(f"   偏离度: {r['price_discount']:.2f}% {'✅' if r['discount_ok'] else '❌'}")
        print(f"   回购规模: {r['buyback_ratio']:.3f}% | 历史: {r['historical_count']}次")
        print(f"   公告时效: {r['days_since_announce']}日内")
        print(f"   信号: {r['signal']}")
        print(f"   入场: {r['entry_price']} | 止损: {r['stop_loss']} | 止盈: {r['take_profit']}")

    return results


def main():
    scan_buyback_stocks()


if __name__ == "__main__":
    main()
