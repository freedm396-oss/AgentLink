#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
港股报告生成器 - 生成投资报告
"""

from datetime import datetime
from typing import Dict, List


class HKReportGenerator:
    """港股投资报告生成器"""

    def __init__(self, config: Dict):
        self.config = config

    def generate_report(self, scored_stocks: List[Dict],
                      portfolio: List[Dict],
                      recommendations: List[Dict]) -> str:
        report = []

        report.append("=" * 70)
        report.append(f"📊 港股策略融合投资顾问报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 70)

        report.append("\n## 一、市场概况")
        report.append(self._generate_market_overview())

        report.append("\n## 二、今日推荐投资组合")
        report.append(self._generate_portfolio_table(portfolio))

        report.append("\n## 三、策略贡献分析")
        report.append(self._generate_strategy_analysis(scored_stocks))

        report.append("\n## 四、个股详细分析")
        report.append(self._generate_stock_details(portfolio))

        report.append("\n## 五、风险提示")
        report.append(self._generate_risk_warning(portfolio))

        report.append("\n## 六、操作建议")
        report.append(self._generate_action_plan(portfolio))

        report.append("\n" + "=" * 70)
        report.append("免责声明：本报告仅供参考，不构成投资建议。")
        report.append("股市有风险，投资需谨慎。过往业绩不代表未来表现。")
        report.append("=" * 70)

        return "\n".join(report)

    def _generate_market_overview(self) -> str:
        return """
| 指标 | 数值 | 评价 |
|------|------|------|
| 市场情绪 | 中性偏多 | 可适度参与 |
| 策略信号数 | ~50只 | 机会较多 |
| 策略一致性 | 中等 | 存在分歧 |
| 建议仓位 | 90% | 积极配置 |
        """

    def _generate_portfolio_table(self, portfolio: List[Dict]) -> str:
        if not portfolio:
            return "暂无推荐组合"

        lines = [
            "| 排名 | 股票 | 代码 | 综合得分 | 策略数 | 仓位 | 操作 |",
            "|------|------|------|----------|--------|------|------|"
        ]

        for i, stock in enumerate(portfolio, 1):
            action = stock.get('investment_advice', {}).get('action', '关注')
            lines.append(
                f"| {i} | {stock['stock_name']} | {stock['stock_code']} | "
                f"{stock['combined_score']} | {stock['strategy_count']} | "
                f"{stock['position_pct']*100:.1f}% | {action} |"
            )

        total_position = sum(s['position_pct'] for s in portfolio)
        lines.append("")
        lines.append(f"**组合汇总**: 股票{len(portfolio)}只 | 总仓位{total_position*100:.1f}% | "
                      f"现金{(1-total_position)*100:.1f}%")

        return "\n".join(lines)

    def _generate_strategy_analysis(self, scored_stocks: List[Dict]) -> str:
        strategy_contributions = {}
        for stock in scored_stocks[:10]:
            for rec in stock.get('recommendations', []):
                name = rec.get('strategy_display', '')
                if name:
                    strategy_contributions[name] = strategy_contributions.get(name, 0) + 1

        lines = ["| 策略名称 | 被采纳数 | 贡献度 |"]
        lines.append("|----------|----------|--------|")
        for name, count in sorted(strategy_contributions.items(),
                                  key=lambda x: x[1], reverse=True)[:10]:
            pct = count / len(scored_stocks[:10]) * 100 if scored_stocks else 0
            lines.append(f"| {name} | {count} | {pct:.0f}% |")

        return "\n".join(lines)

    def _generate_stock_details(self, portfolio: List[Dict]) -> str:
        if not portfolio:
            return "无详细分析"

        lines = []
        for stock in portfolio:
            lines.append(f"\n### {stock['stock_name']} ({stock['stock_code']})")
            lines.append(f"- **综合得分**: {stock['combined_score']}分")
            lines.append(f"- **推荐策略**: {', '.join(stock['strategies'][:5])}")
            lines.append(f"- **策略平均胜率**: {stock['avg_win_rate']}%")
            lines.append(f"- **建议仓位**: {stock['position_pct']*100:.1f}%")
            lines.append(f"- **当前价格**: {stock['current_price']}港元")
            lines.append(f"- **预期收益**: {stock['expected_return_pct']}%")
            advice = stock.get('investment_advice', {})
            lines.append(f"- **操作建议**: {advice.get('action', '关注')}")
            lines.append(f"- **止损价位**: {advice.get('stop_loss', 'N/A')}港元")
            lines.append(f"- **目标价位**: {advice.get('target', 'N/A')}港元")

        return "\n".join(lines)

    def _generate_risk_warning(self, portfolio: List[Dict]) -> str:
        warnings_list = [
            "⚠️ 港股有风险，投资需谨慎",
            "⚠️ 本报告仅供参考，不构成买卖依据",
            "⚠️ 建议设置止损位，严格执行纪律",
            "⚠️ 单只股票仓位不宜过重",
            "⚠️ 注意汇率风险（港元与人民币）"
        ]

        if portfolio:
            max_pos = max(s['position_pct'] for s in portfolio)
            if max_pos > 0.25:
                name = next(s['stock_name'] for s in portfolio if s['position_pct'] == max_pos)
                warnings_list.append(f"⚠️ {name}仓位较重({max_pos*100:.0f}%)，注意集中度风险")

        return "\n".join(f"- {w}" for w in warnings_list)

    def _generate_action_plan(self, portfolio: List[Dict]) -> str:
        lines = ["### 买入计划", "",
                 "| 优先级 | 股票 | 建议买入价 | 仓位 | 买入时机 |",
                 "|--------|------|------------|------|----------|"]

        for i, stock in enumerate(portfolio, 1):
            advice = stock.get('investment_advice', {})
            lines.append(
                f"| {i} | {stock['stock_name']} | {stock['current_price']}港元 | "
                f"{stock['position_pct']*100:.0f}% | {advice.get('entry_strategy', '开盘买入')} |"
            )

        lines.extend(["", "### 持仓管理",
                      "- 每日收盘后检查持仓状态",
                      "- 触及止损线立即离场",
                      "- 达到目标价分批止盈",
                      "- 每周五进行组合再平衡"])

        return "\n".join(lines)
