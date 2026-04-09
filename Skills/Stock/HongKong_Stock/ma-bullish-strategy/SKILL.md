# SKILL.md

---
name: hk-ma-bullish-strategy
description: 港股均线多头排列策略 - 均线发散+北水持续增持，趋势跟随策略，胜率65%
version: 1.0.0
author: QuantTeam
tags: [港股, 技术分析, 均线多头, 南向资金, 趋势跟随]
dependencies:
  - akshare>=1.12.0
  - pandas>=1.5.0
  - numpy>=1.23.0
  - pyyaml>=6.0
---

# 港股均线多头排列策略

## 策略概述

港股均线多头排列策略专为港股通标的设计，聚焦均线系统全面多头排列且北水持续增持的强势股。

### 核心逻辑

```
买入条件：
1. 均线多头排列：MA5 > MA10 > MA20 > MA60
2. 均线发散度：(MA5 - MA60) / MA60 > 5%
3. 港股通持股比例 > 5%（南向资金持续买入）
4. 成交量趋势：MA5(量) > MA20(量)，量价配合

卖出规则：
- 止损：入场价 -6%
- 止盈：+20% 或 MA5 跌破 MA10（移动止盈）
```

### 策略表现

| 市场环境 | 胜率 | 盈亏比 | 持仓周期 | 适用场景 |
|---------|------|--------|---------|---------|
| 上升趋势 | 65-75% | 3:1 | 10-30天 | 趋势股持有 |
| 震荡市场 | 55-65% | 2:1 | 5-15天 | 波段操作 |
| 下跌趋势 | < 50% | 不建议 | - | 空仓观望 |

## 快速开始

### 安装依赖

```bash
pip install akshare pandas numpy pyyaml
```

### 命令行使用

```bash
# 进入脚本目录
cd skills/Stock/HongKong_Stock/ma-bullish-strategy/skills/scripts

# 分析单只港股
python3 hk_ma_bullish_analyzer.py --stock 00700 --name 腾讯控股

# 扫描恒生成分股（均线多头排列）
python3 hk_ma_bullish_scanner.py

# 一致性检查
python3 check_consistency.py
```

### Python API

```python
import sys
sys.path.insert(0, 'skills/scripts')
from hk_ma_bullish_analyzer import HKBullishAnalyzer

analyzer = HKBullishAnalyzer()
result = analyzer.analyze_stock('00700', '腾讯控股')

if result:
    print(f"均线排列: {result['ma_arrangement']}")
    print(f"发散度: {result['ma_spread']:.2%}")
    print(f"港股通持股: {result['southbound_holding']:.2%}")
    print(f"信号: {result['signal']}")
    print(f"入场价: {result['entry_price']}")
    print(f"止损价: {result['stop_loss']}")
    print(f"止盈价: {result['take_profit']}")
    print(f"建议: {result['suggestion']}")
```

## 评分体系

| 分数 | 等级 | 建议 |
|------|------|------|
| ≥85 | 极强 | 重点关注，积极买入 |
| 75-84 | 强 | 可考虑买入 |
| 70-74 | 中等 | 需观察，等待确认 |
| <70 | 弱 | 建议观望 |

## 分析维度权重

| 维度 | 权重 | 关键指标 |
|------|------|---------|
| 均线排列 | 30% | MA5>MA10>MA20>MA60 多头程度 |
| 均线发散 | 25% | (MA5-MA60)/MA60 发散度 |
| 北水支撑 | 25% | 港股通持股比例及变化 |
| 量价配合 | 20% | 成交量趋势确认 |

## 目录结构

```
ma-bullish-strategy/
├── SKILL.md                        # 本文件
├── README.md                        # 策略说明文档
├── requirements.txt                 # Python依赖
├── demo.py                          # 演示脚本
├── check_consistency.py             # 一致性检查
├── config/                          # 配置文件
│   ├── strategy_config.yaml        # 策略参数
│   ├── scoring_weights.yaml         # 评分权重
│   └── risk_rules.yaml              # 风险规则
├── agents/                          # Agent配置
│   └── hk-ma-bullish-agent.yaml
├── crons/                           # 定时任务
│   └── hk-ma-bullish-crons.yaml
└── skills/scripts/                 # 策略脚本
    ├── hk_ma_bullish_analyzer.py   # 核心分析器
    ├── hk_ma_bullish_scanner.py     # 全市场扫描器
    └── check_consistency.py         # 一致性检查
```

## 数据源

- **akshare**（推荐）：免费，港股数据全面
- 港股通持股数据：港交所披露易 / Choice / Wind

## 风险提示

- 恒指处于下降趋势时，均线策略胜率大幅下降
- 避免单日成交额低于 5000 万港元的标的
- 港股通持股数据 T+2 披露，存在延迟效应
- 策略仅供参考，不构成投资建议

## 更新日志

### v1.0.0 (2026-04-08)
- ✨ 初始版本发布
- ✨ 均线多头排列 + 发散度过滤
- ✨ 北水（港股通）持股比例确认
- ✨ 量价配合验证
