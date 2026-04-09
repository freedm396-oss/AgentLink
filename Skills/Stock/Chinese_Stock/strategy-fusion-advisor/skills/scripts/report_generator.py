# skills/scripts/report_generator.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
报告生成器 - 生成投资报告
"""

from datetime import datetime
from typing import Dict, List


class ReportGenerator:
    """投资报告生成器"""
    
    def __init__(self, config: Dict):
        self.config = config
        
    def generate_report(self, scored_stocks: List[Dict],
                        portfolio: List[Dict],
                        recommendations: List[Dict]) -> str:
        """生成完整投资报告"""
        report = []
        
        # 标题
        report.append("=" * 80)
        report.append(f"📊 策略融合投资顾问报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        # 市场概况
        report.append("\n## 一、市场概况")
        report.append(self._generate_market_overview())
        
        # 推荐组合
        report.append("\n## 二、今日推荐投资组合")
        report.append(self._generate_portfolio_table(portfolio))
        
        # 策略贡献分析
        report.append("\n## 三、策略贡献分析")
        report.append(self._generate_strategy_analysis(scored_stocks, recommendations))
        
        # 个股详细分析
        report.append("\n## 四、个股详细分析")
        report.append(self._generate_stock_details(portfolio))
        
        # 风险提示
        report.append("\n## 五、风险提示")
        report.append(self._generate_risk_warning(portfolio))
        
        # 操作建议
        report.append("\n## 六、操作建议")
        report.append(self._generate_action_plan(portfolio))
        
        report.append("\n" + "=" * 80)
        report.append("免责声明：本报告仅供参考，不构成投资建议。")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def _generate_market_overview(self) -> str:
        """生成市场概况"""
        return """
| 指标 | 数值 | 评价 |
|------|------|------|
| 市场情绪 | 中性偏多 | 可适度参与 |
| 策略信号数 | 55只 | 机会较多 |
| 策略一致性 | 中等 | 存在分歧 |
| 建议仓位 | 90% | 积极配置 |
        """
    
    def _generate_portfolio_table(self, portfolio: List[Dict]) -> str:
        """生成投资组合表格"""
        if not portfolio:
            return "暂无推荐组合"
        
        lines = [
            "| 排名 | 股票 | 代码 | 综合得分 | 策略数 | 建议仓位 | 操作建议 |",
            "|------|------|------|----------|--------|----------|----------|"
        ]
        
        for i, stock in enumerate(portfolio, 1):
            action = stock.get('investment_advice', {}).get('action', '关注')
            lines.append(
                f"| {i} | {stock['stock_name']} | {stock['stock_code']} | "
                f"{stock['combined_score']} | {stock['strategy_count']} | "
                f"{stock['position_pct']*100:.1f}% | {action} |"
            )
        
        # 添加组合汇总
        total_position = sum(s['position_pct'] for s in portfolio)
        
        lines.append("")
        lines.append(f"**组合汇总**")
        lines.append(f"- 股票数量: {len(portfolio)}只")
        lines.append(f"- 总仓位: {total_position*100:.1f}%")
        lines.append(f"- 现金预留: {100 - total_position*100:.1f}%")
        
        return "\n".join(lines)
    
    def _generate_strategy_analysis(self, scored_stocks: List[Dict],
                                    recommendations: List[Dict]) -> str:
        """生成策略贡献分析"""
        # 统计各策略推荐被采纳情况
        strategy_contributions = {}
        
        for stock in scored_stocks[:10]:
            for rec in stock.get('recommendations', []):
                strategy_name = rec.get('strategy_display', '')
                if strategy_name:
                    strategy_contributions[strategy_name] = \
                        strategy_contributions.get(strategy_name, 0) + 1
        
        lines = ["| 策略名称 | 推荐被采纳数 | 贡献度 |"]
        lines.append("|----------|--------------|--------|")
        
        for name, count in sorted(strategy_contributions.items(), 
                                  key=lambda x: x[1], reverse=True)[:10]:
            contribution = count / len(scored_stocks[:10]) * 100 if scored_stocks else 0
            lines.append(f"| {name} | {count} | {contribution:.0f}% |")
        
        return "\n".join(lines)
    
    def _generate_stock_details(self, portfolio: List[Dict]) -> str:
        """生成个股详细分析"""
        if not portfolio:
            return "无详细分析"
        
        lines = []
        
        for stock in portfolio:
            lines.append(f"\n### {stock['stock_name']} ({stock['stock_code']})")
            lines.append(f"- **综合得分**: {stock['combined_score']}分")
            lines.append(f"- **推荐策略**: {', '.join(stock['strategies'][:5])}")
            lines.append(f"- **策略内平均分**: {stock['avg_strategy_score']}分")
            lines.append(f"- **策略平均胜率**: {stock['avg_win_rate']}%")
            lines.append(f"- **建议仓位**: {stock['position_pct']*100:.1f}%")
            lines.append(f"- **当前价格**: {stock['current_price']}元")
            lines.append(f"- **预期收益**: {stock['expected_return_pct']}%")
            
            advice = stock.get('investment_advice', {})
            lines.append(f"- **操作建议**: {advice.get('action', '关注')}")
            lines.append(f"- **买入策略**: {advice.get('entry_strategy', '正常买入')}")
            lines.append(f"- **止损价位**: {advice.get('stop_loss', 'N/A')}元")
            lines.append(f"- **目标价位**: {advice.get('target', 'N/A')}元")
        
        return "\n".join(lines)
    
    def _generate_risk_warning(self, portfolio: List[Dict]) -> str:
        """生成风险提示"""
        warnings = [
            "⚠️ 股市有风险，投资需谨慎",
            "⚠️ 本报告仅供参考，不构成买卖依据",
            "⚠️ 建议设置止损位，严格执行纪律",
            "⚠️ 单只股票仓位不宜过重",
            "⚠️ 注意大盘系统性风险"
        ]
        
        # 添加特定风险
        if len(portfolio) > 0:
            max_position = max(s['position_pct'] for s in portfolio)
            if max_position > 0.25:
                warnings.append(f"⚠️ {portfolio[0]['stock_name']}仓位较重({max_position*100:.0f}%)，注意集中度风险")
        
        return "\n".join(f"- {w}" for w in warnings)
    
    def _generate_action_plan(self, portfolio: List[Dict]) -> str:
        """生成操作计划"""
        lines = [
            "### 买入计划",
            "",
            "| 优先级 | 股票 | 建议买入价 | 买入比例 | 买入时机 |",
            "|--------|------|------------|----------|----------|"
        ]
        
        for i, stock in enumerate(portfolio, 1):
            advice = stock.get('investment_advice', {})
            lines.append(
                f"| {i} | {stock['stock_name']} | {stock['current_price']} | "
                f"{stock['position_pct']*100:.0f}% | {advice.get('entry_strategy', '开盘买入')} |"
            )
        
        lines.append("")
        lines.append("### 持仓管理")
        lines.append("- 每日收盘后检查持仓状态")
        lines.append("- 触及止损线立即离场")
        lines.append("- 达到目标价分批止盈")
        lines.append("- 每周五进行组合再平衡")
        
        return "\n".join(lines)