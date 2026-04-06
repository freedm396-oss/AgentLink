# skills/scripts/portfolio_optimizer.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
投资组合优化器 - 优化仓位分配
"""

import numpy as np
from typing import Dict, List, Optional, Tuple


class PortfolioOptimizer:
    """投资组合优化器"""
    
    def __init__(self, config: Dict, risk_config: Dict):
        self.config = config
        self.risk_config = risk_config
        
        self.max_position = config['fusion']['portfolio']['max_single_position']
        self.min_position = config['fusion']['portfolio']['min_single_position']
        self.cash_reserve = config['fusion']['portfolio']['cash_reserve']
        self.final_top_n = config['fusion']['recommendations']['final_top_n']
        
    def optimize_portfolio(self, scored_stocks: List[Dict]) -> List[Dict]:
        """优化投资组合"""
        # 1. 选择Top N股票
        selected = scored_stocks[:self.final_top_n]
        
        if not selected:
            return []
        
        # 2. 计算基础仓位
        total_score = sum(s['combined_score'] for s in selected)
        
        if total_score == 0:
            return []
        
        # 3. 分配仓位
        available_capital = 1 - self.cash_reserve
        
        for stock in selected:
            # 基础仓位 = 得分占比
            base_position = (stock['combined_score'] / total_score) * available_capital
            
            # 根据一致性调整
            consistency_factor = 0.8 + (stock['consistency_score'] / 100) * 0.4
            position = base_position * consistency_factor
            
            # 根据风险评分调整
            risk_factor = 1 - (stock['risk_score'] / 100) * 0.3
            position = position * risk_factor
            
            # 限制仓位范围
            position = max(self.min_position, min(self.max_position, position))
            
            stock['position_pct'] = round(position, 4)
        
        # 4. 归一化仓位
        total_position = sum(s['position_pct'] for s in selected)
        
        if total_position > 0:
            for stock in selected:
                stock['position_pct'] = round(stock['position_pct'] / total_position * available_capital, 4)
        
        # 5. 添加投资建议
        for stock in selected:
            stock['investment_advice'] = self._generate_investment_advice(stock)
            stock['expected_return_pct'] = round(stock['expected_return'] * 100, 1)
        
        return selected
    
    def _generate_investment_advice(self, stock: Dict) -> Dict:
        """生成投资建议"""
        score = stock['combined_score']
        
        if score >= 80:
            action = "强烈买入"
            urgency = "高"
            entry_strategy = "开盘即可买入"
        elif score >= 70:
            action = "买入"
            urgency = "中"
            entry_strategy = "分2批买入"
        elif score >= 60:
            action = "关注"
            urgency = "低"
            entry_strategy = "等待回调买入"
        else:
            action = "观望"
            urgency = "极低"
            entry_strategy = "暂缓买入"
        
        return {
            'action': action,
            'urgency': urgency,
            'entry_strategy': entry_strategy,
            'stop_loss': stock.get('stop_loss', stock['current_price'] * 0.95),
            'target': stock.get('target_price', stock['current_price'] * 1.10)
        }
    
    def calculate_portfolio_risk(self, portfolio: List[Dict]) -> Dict:
        """计算组合风险"""
        if not portfolio:
            return {'risk_level': '未知', 'score': 0}
        
        # 计算集中度风险
        max_weight = max(s['position_pct'] for s in portfolio)
        concentration_risk = max_weight / self.max_position
        
        # 计算策略分散度
        all_strategies = set()
        for stock in portfolio:
            for rec in stock.get('recommendations', []):
                all_strategies.add(rec.get('strategy_display', ''))
        
        strategy_diversity = len(all_strategies) / len(self.config['fusion']['strategies'])
        
        # 综合风险评分
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