# SKILL.md

---
name: hk-strategy-optimizer
description: 港股策略优化器 - 基于回测数据自动优化港股交易策略参数，支持10种港股策略的网格搜索与评分权重调优
version: 1.0.0
author: QuantTeam
tags: [港股, 策略优化, 参数调优, 机器学习, 回测分析]
dependencies:
  - requests>=2.28.0
  - pandas>=1.5.0
  - numpy>=1.23.0
  - pyyaml>=6.0
  - scikit-learn>=1.2.0
---

# 港股策略优化器

## 概述

港股策略优化器是专为港股市场设计的自动化参数优化工具，基于历史回测数据，通过网格搜索和权重调优，持续提升策略表现。

## 支持的策略

| # | 策略代码 | 策略名称 | 胜率 | 核心参数 |
|---|---------|---------|------|---------|
| 1 | `ma-bullish-strategy` | 均线多头排列策略 | 65% | MA周期/发散度 |
| 2 | `breakout-strategy` | 突破高点策略 | 58% | 突破幅度/量能倍数 |
| 3 | `short-interest-reversal-strategy` | 沽空比率反转策略 | 70% | 沽空比率/下降天数 |
| 4 | `ah-premium-arbitrage-strategy` | AH溢价套利策略 | 74% | 溢价率/量能门槛 |
| 5 | `buyback-follow-strategy` | 回购公告跟进策略 | 62% | 偏离度/规模比例 |
| 6 | `placement-dip-strategy` | 配股砸盘抄底策略 | 60% | 折价/跌幅区间 |
| 7 | `dividend-exright-strategy` | 分红除权博弈策略 | 67% | 股息率/距除权日 |
| 8 | `liquidity-filter-strategy` | 流动性过滤策略 | 风控 | 成交额/换手率 |
| 9 | `short-stop-loss-strategy` | 做空止损策略 | 风控 | 止损幅度 |
| 10 | `earnings-surprise-strategy` | 财报超预期策略 | 70% | 净利润增长/EPS超预期 |
| 11 | `ma-pullback-strategy` | 均线回踩策略 | 待测 | 回踩深度/量能 |

## 核心功能

### 1. 参数优化
- 网格搜索最优参数组合
- 支持整数、浮点数参数
- 自定义参数范围

### 2. 权重优化
- 优化评分维度权重
- 自动归一化处理
- 交叉验证

### 3. 阈值优化
- 优化买入/卖出阈值
- 调整评分标准
- 改善信号质量

### 4. 性能分析
- 计算胜率、夏普比率
- 分析最大回撤
- 生成综合评分

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 优化单个策略

```bash
cd skills/Stock/HongKong_Stock/strategy-optimizer/skills/scripts
python3 strategy_optimizer.py --strategy ma-bullish-strategy
```

### 优化所有策略

```bash
python3 strategy_optimizer.py --all
```

### 优化评分权重

```bash
python3 strategy_optimizer.py --weights ma-bullish-strategy
```

## 优化流程

```
1. 收集回测数据
       ↓
2. 分析当前表现
       ↓
3. 生成参数组合
       ↓
4. 网格搜索优化
       ↓
5. 验证优化效果
       ↓
6. 输出优化报告
```

## 输出示例

```json
{
  "strategy": "ma-bullish-strategy",
  "current_performance": {
    "win_rate": 65.0,
    "sharpe_ratio": 1.35,
    "max_drawdown": 8.2
  },
  "optimized_params": {
    "ma_spread_threshold": 0.06,
    "southbound_min": 0.06,
    "volume_ratio": 1.3
  },
  "validation": {
    "win_rate_improvement": 3.2,
    "sharpe_improvement": 0.15,
    "drawdown_reduction": 1.5
  }
}
```

## 目录结构

```
strategy-optimizer/
├── SKILL.md
├── README.md
├── requirements.txt
├── demo.py
├── check_consistency.py
├── config/
│   ├── optimizer_config.yaml      # 优化器配置（策略列表）
│   ├── optimization_params.yaml    # 各策略参数范围
│   └── evaluation_config.yaml     # 评估指标配置
├── agents/
│   └── hk-strategy-optimizer-agent.yaml
├── crons/
│   └── hk-strategy-optimizer-crons.yaml
├── data/
│   ├── backtest_results/          # 回测数据
│   ├── optimized_params/          # 优化结果
│   ├── predictions/               # 预测结果
│   └── logs/                     # 日志
└── skills/scripts/
    ├── strategy_optimizer.py      # 主模块
    ├── param_optimizer.py         # 参数优化
    ├── performance_analyzer.py   # 性能分析
    ├── model_updater.py          # 配置更新
    └── check_consistency.py       # 一致性检查
```

## 数据源

- **Yahoo Finance**：港股历史行情
- **港交所披露易**：回购/配股/沽空数据
- **本地回测数据**：CSV格式

## 定时任务

| 任务名称 | 执行时间 | 功能 |
|---------|---------|------|
| weekly-strategy-optimization | 周日22:00 | 每周策略优化 |
| monthly-comprehensive-optimization | 每月1日23:00 | 月度综合优化 |
| daily-strategy-health-check | 每日20:00 | 策略健康检查 |

## 风险提示

- 优化结果基于历史数据，不保证未来表现
- 建议在模拟盘验证后应用优化参数
- 避免过度优化（过拟合）风险

## 更新日志

### v1.0.0 (2026-04-08)
- ✨ 初始版本发布
- ✨ 支持10种港股策略
- ✨ 网格搜索参数优化
- ✨ 权重优化功能
- ✨ 性能分析与评估
