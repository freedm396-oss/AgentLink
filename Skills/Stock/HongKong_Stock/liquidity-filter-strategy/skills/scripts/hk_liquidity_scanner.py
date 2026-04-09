#!/usr/bin/env python3
"""
港股流动性过滤策略 - 批量扫描器
HK Liquidity Filter Scanner
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from hk_liquidity_analyzer import HKLiquidityAnalyzer


# 港股示例列表（包含不同流动性的股票）
HK_STOCKS = [
    ('0700.HK', '腾讯控股'),
    ('0981.HK', '中芯国际'),
    ('0999.HK', '泡泡玛特'),
    ('0003.HK', '中华煤气'),
    ('0823.HK', '领展房产基金'),
    ('0386.HK', '中国石化'),
    ('0006.HK', '电能实业'),
    ('0012.HK', '恒基地产'),
    ('0941.HK', '中国移动'),
    ('3888.HK', '金山软件'),
]


def scan_liquidity():
    """批量扫描港股流动性"""
    analyzer = HKLiquidityAnalyzer()
    allowed = []
    rejected = []

    print(f"\n开始扫描 {len(HK_STOCKS)} 只港股流动性...")
    print("-" * 60)

    for symbol, name in HK_STOCKS:
        try:
            result = analyzer.check_stock(symbol, name)
            if result['allowed']:
                allowed.append(result)
                print(f"  ✅ {symbol} {name}: "
                      f"成交{result['avg_volume_m']:.0f}M 换手{result['turnover_rate']:.2f}% "
                      f"价差{result['bid_ask_spread']:.2f}% 市值{result['market_cap_b']:.0f}B "
                      f"评分{result['score']}")
            else:
                rejected.append(result)
                print(f"  ❌ {symbol} {name}: {result['reject_reasons'][0]}")
        except Exception as e:
            print(f"  ⚠️ {symbol} {name}: 错误 {e}")

    allowed.sort(key=lambda x: x['score'], reverse=True)
    rejected.sort(key=lambda x: x['score'], reverse=True)

    print("\n" + "=" * 60)
    print(f"扫描结果: 允许 {len(allowed)} 只 | 拒绝 {len(rejected)} 只")
    print("=" * 60)

    if allowed:
        print("\n✅ 允许交易:")
        for i, r in enumerate(allowed, 1):
            print(f"  {i}. {r['symbol']} {r['name']} "
                  f"| 成交{r['avg_volume_m']:.0f}M | 换手{r['turnover_rate']:.2f}% | "
                  f"价差{r['bid_ask_spread']:.2f}% | 评分{r['score']}")

    if rejected:
        print("\n❌ 拒绝交易（仙股/低流动性）:")
        for i, r in enumerate(rejected, 1):
            print(f"  {i}. {r['symbol']} {r['name']}: {', '.join(r['reject_reasons'])}")

    return allowed, rejected


def main():
    scan_liquidity()


if __name__ == "__main__":
    main()
