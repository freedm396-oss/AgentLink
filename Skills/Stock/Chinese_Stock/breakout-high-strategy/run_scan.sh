#!/bin/bash
# 临时修复：baostock 对当天数据返回空，改用近期交易日
# 直接 patch data_source_adapter.py 中的日期获取逻辑

python3 - <<'PYEOF'
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/breakout-high-strategy/skills/scripts')

import os
import datetime

# 强制设置 BAOSTOCK_DATE 为昨天（近期交易日）
os.environ['BAOSTOCK_DATE'] = '2026-04-08'

# Patch datetime.now() in the adapter module
import data_source_adapter as dsa
from datetime import datetime as dt, timedelta

_original_now = dt.now

def _patched_now():
    t = _original_now()
    if t.weekday() >= 5:
        t = t - timedelta(days=t.weekday() - 4)
    return t

dsa.datetime.now = _patched_now

# 现在直接用内部方式扫全市场
from breakout_high_analyzer import BreakoutHighAnalyzer

print("=" * 80)
print("突破前期高点策略 - 全市场扫描")
print("=" * 80)
print()

analyzer = BreakoutHighAnalyzer(data_source='baostock')

# 用昨天作为查询日期
import baostock as bs
lg = bs.login()
today = dt.now()
if today.weekday() >= 5:
    today = today - timedelta(days=today.weekday() - 4)
query_date = today.strftime('%Y-%m-%d')

print(f"获取股票列表（日期: {query_date}）...")

rs = bs.query_all_stock(day=query_date)
data_list = []
while rs.next():
    data_list.append(rs.get_row_data())

print(f"获取到 {len(data_list)} 只股票")
print("-" * 60)

# 过滤只要 A 股（6开头沪市, 0/3开头深市）
import pandas as pd
df = pd.DataFrame(data_list, columns=rs.fields)
df['code'] = df['code'].str.extract(r'\.(\d{6})$')[0]
# 只保留 A 股
df_a = df[df['code'].str.match(r'^[036]\d{5}$', na=False)].copy()
df_a['name'] = df_a['code']  # 名称暂用代码代替
stock_list = df_a[['code', 'name']]

print(f"过滤后 A 股数量: {len(stock_list)}")
print()

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
        print(f"  ✅ {name}({code}): {result['score']}分")

# 排序
candidates.sort(key=lambda x: x['score'], reverse=True)

print()
print("=" * 80)
print("突破前期高点策略 - 全市场扫描结果")
print(f"扫描时间: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"扫描范围: {total} 只 A 股")
print(f"符合条件: {len(candidates)} 只")
print("=" * 80)
print()

if not candidates:
    print("未发现符合条件的股票（突破前期高点且评分≥70）")
    print()
    print("说明：")
    print("  - 当前市场无有效突破信号")
    print("  - 突破条件：60日内高点 + 涨幅≥3% + 成交量≥1.5倍")
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
PYEOF
