#!/usr/bin/env python3
"""
港股配股砸盘抄底策略 - 全市场扫描器
HK Placement Dip Strategy Scanner
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from hk_placement_analyzer import HKPlacementAnalyzer


# 近期有配股消息的港股示例列表
HK_PLACEMENT_STOCKS = [
    ('0700.HK', '腾讯控股'),
    ('9988.HK', '阿里巴巴'),
    ('3690.HK', '美团-W'),
    ('0941.HK', '中国移动'),
    ('0992.HK', '联想集团'),
    ('1024.HK', '快手-W'),
    ('3888.HK', '金山软件'),
    ('2382.HK', '舜宇光学'),
    ('2018.HK', '瑞声科技'),
    ('3836.HK', '国联证券'),
]


def scan_placement_stocks(top_n=10):
    """扫描配股砸盘机会"""
    analyzer = HKPlacementAnalyzer()
    results = []

    print(f"\n开始扫描 {len(HK_PLACEMENT_STOCKS)} 只有配股消息的港股...")
    print("-" * 60)

    for symbol, name in HK_PLACEMENT_STOCKS:
        try:
            result = analyzer.analyze_stock(symbol, name)
            if result and result['score'] >= 70:
                results.append(result)
                print(f"  ✅ {symbol} {name}: 折价{result['placement_discount']:.1f}% "
                      f"跌幅{result['drop_magnitude']:.1f}% 评分{result['score']} {result['signal']}")
            else:
                disc = result['placement_discount'] if result else 0
                drop = result['drop_magnitude'] if result else 0
                print(f"  ❌ {symbol} {name}: 折价{disc:.1f}% 跌幅{drop:.1f}%")
        except Exception as e:
            print(f"  ⚠️ {symbol} {name}: 错误 {e}")

    results.sort(key=lambda x: x['score'], reverse=True)

    print("\n" + "=" * 60)
    print(f"扫描结果: 共 {len(results)} 只符合条件（评分≥70）")
    print("=" * 60)

    for i, r in enumerate(results[:top_n], 1):
        print(f"\n{i}. {r['symbol']} {r['name']}")
        print(f"   评分: {r['score']} ({r['rating']})")
        print(f"   配股折价: {r['placement_discount']:.2f}% {'✅' if r['discount_ok'] else '❌'}")
        print(f"   公告跌幅: {r['drop_magnitude']:.2f}% {'✅' if r['drop_ok'] else '❌'}")
        print(f"   资金用途: {r['fund_usage']} {'✅' if r['usage_ok'] else '❌'}")
        print(f"   机构参与: {r['institutional_count']}家 {'✅' if r['inst_ok'] else '❌'}")
        print(f"   信号: {r['signal']}")
        print(f"   入场: {r['entry_price']} | 止损: {r['stop_loss']} | 止盈: {r['take_profit']}")
        print(f"   持仓上限: {r['max_days']}日")

    return results


def main():
    scan_placement_stocks()


if __name__ == "__main__":
    main()
