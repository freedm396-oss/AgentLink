# earnings-surprise-strategy/skills/scripts/surprise_analyzer.py

from typing import Dict, List, Optional
import numpy as np

class SurpriseAnalyzer:
    """超预期幅度分析器"""
    
    def __init__(self):
        # 超预期评分标准
        self.surprise_thresholds = {
            'excellent': 30,   # 超预期>30%
            'good': 20,        # 超预期20-30%
            'normal': 10,      # 超预期10-20%
            'poor': 0          # 超预期<10%
        }
        
    def analyze(self, earnings: Dict) -> Dict:
        """分析超预期幅度"""
        # 1. 净利润超预期分析
        net_profit_surprise = self._calculate_net_profit_surprise(earnings)
        
        # 2. 营收超预期分析
        revenue_surprise = self._calculate_revenue_surprise(earnings)
        
        # 3. 双重超预期加成
        double_beat_bonus = 0
        if net_profit_surprise['is_surprise'] and revenue_surprise['is_surprise']:
            double_beat_bonus = 15
        
        # 计算总分
        base_score = (net_profit_surprise['score'] + revenue_surprise['score']) / 2
        total_score = min(100, base_score + double_beat_bonus)
        
        # 评级
        if total_score >= 85:
            level = "显著超预期"
        elif total_score >= 70:
            level = "超预期"
        elif total_score >= 60:
            level = "小幅超预期"
        else:
            level = "符合预期或不及预期"
        
        return {
            'score': total_score,
            'level': level,
            'net_profit': net_profit_surprise,
            'revenue': revenue_surprise,
            'double_beat': double_beat_bonus > 0,
            'is_significant': total_score >= 85
        }
    
    def _calculate_net_profit_surprise(self, earnings: Dict) -> Dict:
        """计算净利润超预期"""
        actual_yoy = earnings.get('net_profit_yoy', 0)
        actual_qoq = earnings.get('net_profit_qoq', 0)
        
        # 获取预期值（简化：使用行业平均增速作为预期）
        expected_yoy = self._get_expected_growth(earnings.get('industry', ''))
        
        # 计算超预期幅度
        if expected_yoy > 0:
            surprise_pct = (actual_yoy - expected_yoy) / abs(expected_yoy) * 100
        else:
            surprise_pct = actual_yoy - expected_yoy
        
        is_surprise = actual_yoy > expected_yoy and actual_yoy >= 20
        
        # 评分
        if actual_yoy >= 50:
            score = 100
            level = "爆发式增长"
        elif actual_yoy >= 30:
            score = 85
            level = "高速增长"
        elif actual_yoy >= 20:
            score = 70
            level = "稳定增长"
        elif actual_yoy >= 10:
            score = 50
            level = "温和增长"
        else:
            score = 30
            level = "增长乏力"
        
        # 超预期加成
        if surprise_pct > 30:
            score = min(100, score + 15)
        elif surprise_pct > 20:
            score = min(100, score + 10)
        elif surprise_pct > 10:
            score = min(100, score + 5)
        
        return {
            'score': score,
            'level': level,
            'actual_yoy': round(actual_yoy, 2),
            'expected_yoy': round(expected_yoy, 2),
            'surprise_pct': round(surprise_pct, 2),
            'is_surprise': is_surprise
        }
    
    def _calculate_revenue_surprise(self, earnings: Dict) -> Dict:
        """计算营收超预期"""
        actual_yoy = earnings.get('revenue_yoy', 0)
        
        # 获取预期值
        expected_yoy = self._get_expected_growth(earnings.get('industry', '')) * 0.8
        
        # 计算超预期幅度
        if expected_yoy > 0:
            surprise_pct = (actual_yoy - expected_yoy) / abs(expected_yoy) * 100
        else:
            surprise_pct = actual_yoy - expected_yoy
        
        is_surprise = actual_yoy > expected_yoy and actual_yoy >= 15
        
        # 评分
        if actual_yoy >= 30:
            score = 100
            level = "高速增长"
        elif actual_yoy >= 20:
            score = 85
            level = "稳定增长"
        elif actual_yoy >= 10:
            score = 70
            level = "温和增长"
        elif actual_yoy >= 0:
            score = 50
            level = "持平"
        else:
            score = 30
            level = "下滑"
        
        # 超预期加成
        if surprise_pct > 20:
            score = min(100, score + 10)
        elif surprise_pct > 10:
            score = min(100, score + 5)
        
        return {
            'score': score,
            'level': level,
            'actual_yoy': round(actual_yoy, 2),
            'expected_yoy': round(expected_yoy, 2),
            'surprise_pct': round(surprise_pct, 2),
            'is_surprise': is_surprise
        }
    
    def _get_expected_growth(self, industry: str) -> float:
        """获取行业预期增速"""
        # 简化实现，实际需要从数据源获取
        industry_benchmarks = {
            '医药生物': 15,
            '食品饮料': 12,
            '电子': 20,
            '计算机': 18,
            '新能源': 25,
            '银行': 5,
            '证券': 10,
            '保险': 8,
            '房地产': -5,
            '钢铁': 0,
            '煤炭': 5
        }
        
        for key in industry_benchmarks:
            if key in industry:
                return industry_benchmarks[key]
        
        return 10  # 默认预期增速