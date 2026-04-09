#!/usr/bin/env python3
"""
港股AH溢价套利策略 - 全市场扫描器
HK AH Premium Arbitrage Scanner
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from hk_ah_arbitrage_analyzer import HKAHPremiumAnalyzer


# A+H股示例列表 (hk_code, name, a_code)
AH_STOCKS = [
    ('0700', '腾讯控股', None),      # 无A股
    ('0992', '联想集团', None),      # 无A股
    ('3869', '中国化工', '600028'),  # 中国石化 A+H
    ('3968', '招商银行', '600036'),  # 招商银行 A+H
    ('2318', '中国平安', '601318'),  # 中国平安 A+H
    ('6030', '中信证券', '600030'),  # 中信证券 A+H
    ('3868', '中国铝业', '601600'),  # 中国铝业 A+H
    ('1797', '中国飞鹤', '06186'),   # 飞鹤 A+H
    ('6185', '康希诺生物', '688185'), # 康希诺 A+H
    ('2196', '复星医药', '600196'),  # 复星医药 A+H
]


def scan_ah_premium_stocks(top_n=10):
    """扫描AH溢价套利机会"""
    analyzer = HKAHPremiumAnalyzer()
    results = []

    print(f"\n开始扫描 {len(AH_STOCKS)} 只A+H股...")
    print("-" * 60)

    for hk_code, name, a_code in AH_STOCKS:
        try:
            result = analyzer.analyze_stock(hk_code, name, a_code)
            if result and result['score'] >= 70:
                results.append(result)
                print(f"  ✅ {hk_code} {name}: 溢价{result['ah_premium']:.1f}% 评分{result['score']} {result['signal']}")
            else:
                prem = result['ah_premium'] if result else 0
                print(f"  ❌ {hk_code} {name}: 溢价{prem:.1f}% {'不达40%' if prem < 40 else '其他条件'}")
        except Exception as e:
            print(f"  ⚠️ {hk_code} {name}: 错误 {e}")

    results.sort(key=lambda x: x['score'], reverse=True)

    print("\n" + "=" * 60)
    print(f"扫描结果: 共 {len(results)} 只符合条件（评分≥70）")
    print("=" * 60)

    for i, r in enumerate(results[:top_n], 1):
        print(f"\n{i}. {r['symbol']} {r['name']}")
        print(f"   评分: {r['score']} ({r['rating']})")
        print(f"   AH溢价率: {r['ah_premium']:.2f}%")
        print(f"   H股: {r['h_price']:.2f}港元 | A股: {r['a_price']:.2f}人民币")
        print(f"   H股量能: {r['h_volume_m']:.1f}M {'✅' if r['h_volume_ok'] else '❌'}")
        print(f"   行业趋势: {r['sector_trend']} {'✅' if r['sector_ok'] else '❌'}")
        print(f"   信号: {r['signal']}")
        print(f"   入场: {r['entry_price']} | 止损: {r['stop_loss']}")
        print(f"   止盈: 溢价<{r['exit_premium']}% 或满{r['max_days']}日")

    return results


def main():
    scan_ah_premium_stocks()


if __name__ == "__main__":
    main()
