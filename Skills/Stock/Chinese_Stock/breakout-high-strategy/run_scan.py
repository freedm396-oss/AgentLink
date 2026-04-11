#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全市场扫描补丁：baostock 对当天数据返回空，改用近期交易日
直接读取本地 skill 目录中的模块，不破坏原结构
"""
import sys
import os
from datetime import datetime, timedelta

# 强制使用近期交易日（昨天如果是周末则往前找）
today = datetime.now()
if today.weekday() >= 5:
    today = today - timedelta(days=today.weekday() - 4)
else:
    today = today - timedelta(days=1)  # 用昨天
query_date = today.strftime('%Y-%m-%d')

sys.path.insert(0, '/root/.openclaw/workspace/skills/breakout-high-strategy/skills/scripts')
import baostock as bs
import pandas as pd
from breakout_high_analyzer import BreakoutHighAnalyzer

print("=" * 80)
print("突破前期高点策略 - 全市场扫描")
print("=" * 80)
print(f"使用数据日期: {query_date} (baostock对当天数据暂不可用)")
print()

lg = bs.login()
print(f"登录: {lg.error_msg}")

rs = bs.query_all_stock(day=query_date)
data_list = []
while rs.next():
    data_list.append(rs.get_row_data())

print(f"获取股票列表: {len(data_list)} 只")
if not data_list:
    print("获取失败，退出")
    bs.logout()
    sys.exit(1)

df = pd.DataFrame(data_list, columns=rs.fields)
df['code'] = df['code'].str.extract(r'\.(\d{6})$')[0]
# 只保留 A 股（沪市6开头，深市0/3开头）
df_a = df[df['code'].str.match(r'^[036]\d{5}$', na=False)].copy()
df_a['name'] = df_a['code']
stock_list = df_a[['code', 'name']]

print(f"过滤后 A 股数量: {len(stock_list)}")
print("-" * 60)

analyzer = BreakoutHighAnalyzer(data_source='baostock')

candidates = []
total = len(stock_list)

for idx, (_, row) in enumerate(stock_list.iterrows(), 1):
    code = row['code']
    name = row['name']
    
    if idx % 200 == 0:
        print(f"进度: {idx}/{total} ({idx/total*100:.1f}%)")
    
    result = analyzer.analyze_stock(code, name)
    if result and result['score'] >= 70:
        candidates.append(result)
        score = result['score']
        signal = result['signal']
        price = result.get('current_price', 'N/A')
        bk_price = result.get('breakout_price', 'N/A')
        prev_high = result.get('previous_high', 'N/A')
        bk_pct = result.get('breakout_pct', 'N/A')
        vol_ratio = result.get('volume_ratio', 'N/A')
        print(f"  ✅ {name}({code}): {score}分 | 信号:{signal} | 现价:{price} | 突破:{bk_price} | 前期高点:{prev_high} | 涨幅:+{bk_pct}% | 量比:{vol_ratio}x")

candidates.sort(key=lambda x: x['score'], reverse=True)

print()
print("=" * 80)
print("突破前期高点策略 - 全市场扫描结果")
print(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"使用数据日期: {query_date}")
print(f"扫描范围: {total} 只 A 股")
print(f"符合条件: {len(candidates)} 只")
print("=" * 80)
print()

if not candidates:
    print("未发现符合条件的股票（突破前期高点且评分≥70）")
else:
    for i, r in enumerate(candidates[:20], 1):
        emoji = '🔥' if r['score'] >= 85 else '✅' if r['score'] >= 75 else '👀'
        print(f"{emoji} {i}. {r['stock_name']}({r['stock_code']})")
        print(f"   综合得分: {r['score']}分 | 信号: {r['signal']}")
        print(f"   当前价: {r['current_price']}元")
        print(f"   突破价: {r['breakout_price']}元")
        print(f"   前期高点: {r['previous_high']}元")
        print(f"   突破幅度: +{r['breakout_pct']}%")
        print(f"   成交量比: {r['volume_ratio']}倍")
        print()

bs.logout()
