# SKILL.md

---
name: strategy-fusion-advisor
description: 策略融合投资顾问 - 融合11个交易策略的推荐结果，输出最优投资组合
version: 1.0.0
author: QuantTeam
tags: [投资组合, 策略融合, 仓位管理, 智能投顾]
dependencies:
  - pandas>=1.5.0
  - numpy>=1.23.0
  - pyyaml>=6.0
---

# 策略融合投资顾问

## 概述

策略融合投资顾问是一个智能投资组合生成工具，它收集11个量化策略的每日推荐，根据各策略的历史胜率进行加权评分，最终输出最优的5只股票及仓位建议。

## 核心功能

### 1. 策略收集
- 收集11个策略的推荐结果
- 每个策略推荐5只股票
- 共55只候选股票

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
股票综合得分 = Σ(策略内评分 × 策略胜率 × 策略权重)

仓位比例 = 股票得分 / 所有入选股票得分总和

最终仓位 = 基础仓位 × 一致性因子 × 风险因子

text

## 使用方法

### 1. 生成每日推荐

```bash
cd ~/.openclaw/workspace/skills/strategy-fusion-advisor
python3 skills/scripts/fusion_advisor.py --daily
2. 查看报告
bash
cat data/recommendations/$(date +%Y%m%d)_report.md
3. 启动定时任务
bash
openclaw cron import crons/strategy-fusion-crons.yaml
融合策略列表
序号	策略名称	胜率	权重
1	缩量回踩均线	72%	1.00
2	财报超预期	75%	1.05
3	均线多头排列	68%	0.95
4	涨停回调	68%	0.95
5	MACD底背离	62%	0.85
6	早晨之星	62%	0.85
7	突破高点	68%	0.95
8	RSI超卖	58%	0.80
9	地量见底	62%	0.85
10	缺口回补	62%	0.85
输出示例
json
{
  "date": "2024-01-15",
  "portfolio": [
    {
      "stock_code": "000001",
      "stock_name": "平安银行",
      "combined_score": 92.5,
      "position_pct": 0.25,
      "strategies": ["缩量回踩均线", "财报超预期", "均线多头"],
      "investment_advice": {
        "action": "强烈买入",
        "entry_strategy": "开盘即可买入",
        "stop_loss": 11.88,
        "target": 13.75
      }
    }
  ]
}
定时任务
任务名称	执行时间	功能
afternoon-fusion-recommendation	16:00	每日盘后推荐
morning-portfolio-confirmation	9:15	早盘确认
weekly-portfolio-review	周五16:30	周度回顾
版本历史
v1.0.0 (2024-01-01)
初始版本发布

融合11个交易策略

实现综合评分算法

输出仓位建议

免责声明
本工具仅供参考学习，不构成投资建议。股市有风险，投资需谨慎。过往业绩不代表未来表现。

text

## 14. README.md

```markdown
# README.md

# 策略融合投资顾问

基于OpenClaw开发的智能投资组合生成工具，融合11个量化策略的推荐结果，输出最优投资组合。

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
生成每日推荐
bash
python skills/scripts/fusion_advisor.py --daily
查看报告
bash
cat data/recommendations/$(date +%Y%m%d)_report.md
融合策略
本工具融合以下11个策略：

缩量回踩均线 (胜率72%)

财报超预期 (胜率75%)

均线多头排列 (胜率68%)

涨停回调 (胜率68%)

MACD底背离 (胜率62%)

早晨之星 (胜率62%)

突破高点 (胜率68%)

RSI超卖 (胜率58%)

地量见底 (胜率62%)

缺口回补 (胜率62%)

输出内容
Top 5推荐股票

综合得分

建议仓位比例

买入策略建议

止损/止盈价位

目录结构
text
strategy-fusion-advisor/
├── agents/
│   └── strategy-fusion-agent.yaml
├── config/
│   ├── fusion_config.yaml
│   ├── strategy_weights.yaml
│   └── risk_config.yaml
├── crons/
│   └── strategy-fusion-crons.yaml
├── skills/scripts/
│   ├── fusion_advisor.py
│   ├── strategy_collector.py
│   ├── score_calculator.py
│   ├── portfolio_optimizer.py
│   ├── report_generator.py
│   └── demo.py
├── data/
│   └── recommendations/
├── README.md
├── requirements.txt
└── SKILL.md
版本历史
v1.0.0 (2024-01-01)
初始版本发布

许可证
MIT License

text

## 15. requirements.txt

```txt
# requirements.txt

pandas>=1.5.0
numpy>=1.23.0
pyyaml>=6.0