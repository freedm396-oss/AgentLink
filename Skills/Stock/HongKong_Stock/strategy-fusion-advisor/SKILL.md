# SKILL.md

---
name: hk-strategy-fusion-advisor
description: 港股策略融合投资顾问 - 融合10个港股交易策略的推荐结果，输出最优投资组合，胜率加权评分
version: 1.0.0
author: QuantTeam
tags: [港股, 策略融合, 投资组合, 仓位管理, 智能投顾]
dependencies:
  - requests>=2.28.0
  - pandas>=1.5.0
  - numpy>=1.23.0
  - pyyaml>=6.0
---

# 港股策略融合投资顾问

## 概述

港股策略融合投资顾问是一个智能投资组合生成工具，收集10个港股量化策略的每日推荐，根据各策略的历史胜率进行加权评分，最终输出最优的5只股票及仓位建议。

## 核心功能

### 1. 策略收集
- 收集10个港股策略的推荐结果
- 每个策略推荐5只股票
- 共50只候选股票

### 2. 综合评分
- 策略内评分 × 策略胜率 × 权重系数
- 多策略推荐同一股票时得分叠加
- 考虑策略一致性

### 3. 仓位优化
- 基于得分分配仓位
- 考虑风险分散
- 设定仓位上下限

### 4. 投资报告
- 组合明细及仓位
- 策略贡献分析
- 个股详细分析
- 风险提示

## 融合算法

```
股票综合得分 = Σ(策略内评分 × 策略胜率 × 策略权重)
仓位比例 = 股票得分 / 所有入选股票得分总和
最终仓位 = 基础仓位 × 一致性因子 × 风险因子
```

## 融合策略列表

| # | 策略代码 | 策略名称 | 胜率 | 权重 |
|---|---------|---------|------|------|
| 1 | `ma-bullish-strategy` | 均线多头排列策略 | 65% | 1.0 |
| 2 | `breakout-strategy` | 突破高点策略 | 58% | 0.9 |
| 3 | `short-interest-reversal-strategy` | 沽空比率反转策略 | 70% | 1.1 |
| 4 | `ah-premium-arbitrage-strategy` | AH溢价套利策略 | 74% | 1.15 |
| 5 | `buyback-follow-strategy` | 回购公告跟进策略 | 62% | 1.0 |
| 6 | `placement-dip-strategy` | 配股砸盘抄底策略 | 60% | 0.9 |
| 7 | `dividend-exright-strategy` | 分红除权博弈策略 | 67% | 1.0 |
| 8 | `liquidity-filter-strategy` | 流动性过滤策略 | 风控层 | 1.2 |
| 9 | `short-stop-loss-strategy` | 做空止损策略 | 风控层 | 1.2 |
| 10 | `earnings-surprise-strategy` | 财报超预期策略 | 70% | 1.1 |

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 生成每日推荐

```bash
cd skills/Stock/HongKong_Stock/strategy-fusion-advisor/skills/scripts
python3 fusion_advisor.py --daily
```

### 查看报告

```bash
cat data/recommendations/$(date +%Y%m%d)_report.md
```

## 输出示例

```json
{
  "date": "2026-04-09",
  "portfolio": [
    {
      "stock_code": "0700.HK",
      "stock_name": "腾讯控股",
      "combined_score": 92.5,
      "position_pct": 0.25,
      "strategies": ["均线多头排列", "沽空比率反转", "财报超预期"],
      "investment_advice": {
        "action": "强烈买入",
        "entry_strategy": "开盘即可买入",
        "stop_loss": 460.0,
        "target": 540.0
      }
    }
  ]
}
```

## 目录结构

```
strategy-fusion-advisor/
├── SKILL.md
├── README.md
├── requirements.txt
├── demo.py
├── config/
│   ├── fusion_config.yaml      # 融合配置（10个港股策略）
│   ├── strategy_weights.yaml    # 策略权重配置
│   └── risk_config.yaml        # 风险管理配置
├── agents/
│   └── hk-strategy-fusion-agent.yaml
├── crons/
│   └── hk-strategy-fusion-crons.yaml
├── data/
│   ├── recommendations/
│   ├── historical/
│   └── logs/
└── skills/scripts/
    ├── fusion_advisor.py        # 主模块
    ├── strategy_collector.py    # 策略收集器
    ├── score_calculator.py     # 评分计算器
    ├── portfolio_optimizer.py  # 仓位优化器
    ├── report_generator.py     # 报告生成器
    └── check_consistency.py
```

## 定时任务

| 任务名称 | 执行时间 | 功能 |
|---------|---------|------|
| afternoon-fusion-recommendation | 16:00 | 每日盘后推荐 |
| morning-portfolio-confirmation | 9:15 | 早盘确认 |
| weekly-portfolio-review | 周五16:30 | 周度回顾 |

## 更新日志

### v1.0.0 (2026-04-09)
- ✨ 初始版本发布
- ✨ 融合10个港股交易策略
- ✨ 实现综合评分算法
- ✨ 输出仓位建议

## 免责声明

本工具仅供参考学习，不构成投资建议。股市有风险，投资需谨慎。过往业绩不代表未来表现。
