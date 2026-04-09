#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
港股投资组合优化器 - 优化仓位分配
"""

from typing import Dict, List


class HKPortfolioOptimizer:
    """港股投资组合优化器"""

    def __init__(self, config: Dict, risk_config: Dict):
        self.config = config
        self.risk_config = risk_config

        self.max_position = config['fusion']['portfolio']['max_single_position']
        self.min_position = config['fusion']['portfolio']['min_single_position']
        self.cash_reserve = config['fusion']['portfolio']['cash_reserve']
        self.final_top_n = config['fusion']['recommendations']['final_top_n']

    def optimize_portfolio(self, scored_stocks: List[Dict]) -> List[Dict]:
        selected = scored_stocks[:self.final_top_n]
        if not selected:
            return []

        total_score = sum(s['combined_score'] for s in selected)
        if total_score == 0:
            return []

        available_capital = 1 - self.cash_reserve

        for stock in selected:
            base_position = (stock['combined_score'] / total_score) * available_capital
            consistency_factor = 0.8 + (stock['consistency_score'] / 100) * 0.4
            position = base_position * consistency_factor
            risk_factor = 1 - (stock['risk_score'] / 100) * 0.3
            position = position * risk_factor
            position = max(self.min_position, min(self.max_position, position))
            stock['position_pct'] = round(position, 4)

        total_position = sum(s['position_pct'] for s in selected)
        if total_position > 0:
            for stock in selected:
                stock['position_pct'] = round(
                    stock['position_pct'] / total_position * available_capital, 4)

        for stock in selected:
            stock['investment_advice'] = self._generate_investment_advice(stock)
            stock['expected_return_pct'] = round(stock['expected_return'] * 100, 1)

        return selected

    def _generate_investment_advice(self, stock: Dict) -> Dict:
        score = stock['combined_score']

        if score >= 80:
            action, urgency, entry = "强烈买入", "高", "开盘即可买入"
        elif score >= 70:
            action, urgency, entry = "买入", "中", "分2批买入"
        elif score >= 60:
            action, urgency, entry = "关注", "低", "等待回调买入"
        else:
            action, urgency, entry = "观望", "极低", "暂缓买入"

        return {
            'action': action,
            'urgency': urgency,
            'entry_strategy': entry,
            'stop_loss': stock.get('stop_loss', stock['current_price'] * 0.94),
            'target': stock.get('target_price', stock['current_price'] * 1.12)
        }

    def calculate_portfolio_risk(self, portfolio: List[Dict]) -> Dict:
        if not portfolio:
            return {'risk_level': '未知', 'score': 0}

        max_weight = max(s['position_pct'] for s in portfolio)
        concentration_risk = max_weight / self.max_position

        all_strategies = set()
        for stock in portfolio:
            for rec in stock.get('recommendations', []):
                all_strategies.add(rec.get('strategy_display', ''))

        strategy_diversity = len(all_strategies) / len(self.config['fusion']['strategies'])
        risk_score = (concentration_risk * 0.5 + (1 - strategy_diversity) * 0.5) * 100

        if risk_score < 30:
            risk_level = "低风险"
        elif risk_score < 60:
            risk_level = "中等风险"
        else:
            risk_level = "高风险"

        return {
            'risk_level': risk_level,
            'risk_score': round(risk_score, 1),
            'concentration_risk': round(concentration_risk * 100, 1),
            'strategy_diversity': round(strategy_diversity * 100, 1),
            'max_single_weight': round(max_weight * 100, 1)
        }
