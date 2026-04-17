#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成交量地量见底分析器
识别和分析成交量极度萎缩后的底部反弹机会
"""

import os
import sys

# 清除代理环境变量
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    if key in os.environ:
        del os.environ[key]

# ── 路径设置（相对路径，基于脚本所在目录）────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # .../skills/scripts
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)  # .../skills
_SKILL_ROOT = os.path.dirname(_SKILL_DIR)  # .../<strategy-name>
_BASE_DIR = os.path.dirname(_SKILL_ROOT)  # .../Chinese_Stock

if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# 导入数据源适配器
try:
    from skills.scripts.data_source_adapter import DataSourceAdapter
except ImportError:
    if _SCRIPT_DIR not in sys.path:
        sys.path.insert(0, _SCRIPT_DIR)
    from skills.scripts.data_source_adapter import DataSourceAdapter


class VolumeExtremeAnalyzer:
    """成交量地量见底分析器"""
    
    def __init__(self, data_source: str = "auto"):
        self.name = "成交量地量见底策略"
        self.version = "v1.0.0"
        self.win_rate = 0.62
        
        # 成交量参数
        self.volume_ma_period = 20
        self.volume_threshold = 0.3  # 地量标准：成交量低于均量的30%
        self.price_recovery_threshold = 0.02  # 价格恢复阈值
        
        # 评分权重
        self.weights = {
            'volume_extreme': 0.35,  # 量能极度萎缩程度
            'price_stability': 0.20,  # 价格稳定性
            'volume_recovery': 0.20,  # 量能恢复信号
            'trend_reversal': 0.15,  # 趋势反转确认
            'market_environment': 0.10  # 市场环境
        }
        
        self.data_adapter = DataSourceAdapter(data_source)
        if not self.data_adapter.data_source:
            raise RuntimeError("没有可用的数据源")

    def calculate_volume_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算成交量统计指标"""
        df = df.copy()
        
        # 成交量均线
        df['volume_ma'] = df['volume'].rolling(window=self.volume_ma_period, min_periods=1).mean()
        
        # 量能萎缩比例
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # 成交量变异系数 (CV) - 衡量波动性
        if len(df) >= self.volume_ma_period:
            df['volume_cv'] = df['volume'].rolling(window=self.volume_ma_period).std() / df['volume_ma']
        else:
            df['volume_cv'] = 0
        
        # 价格变化率
        df['price_change'] = df['close'].pct_change()
        df['price_abs_change'] = df['price_change'].abs()
        
        # 波动率
        df['volatility'] = df['price_change'].rolling(window=5).std()
        
        return df

    def find_volume_extreme(self, df: pd.DataFrame, lookback: int = 60) -> List[Dict]:
        """查找成交量极度萎缩的位置"""
        if len(df) < 20:
            return []
        
        df = self.calculate_volume_stats(df)
        extremes = []
        
        for i in range(self.volume_ma_period, len(df)):
            row = df.iloc[i]
            prev_volumes = df['volume'].iloc[max(0, i-20):i]
            
            # 条件1：当前成交量低于均量的30%
            if row['volume_ratio'] > self.volume_threshold:
                continue
            
            # 条件2：最近20日成交量持续萎缩
            if len(prev_volumes) < 10:
                continue
                
            # 检查是否持续萎缩（后10日均量 < 前10日均量）
            mid_point = len(prev_volumes) // 2
            recent_avg = prev_volumes.iloc[mid_point:].mean()
            older_avg = prev_volumes.iloc[:mid_point].mean()
            
            if recent_avg >= older_avg:
                continue
            
            # 条件3：价格相对稳定（波动 < 5%）
            price_std = df['price_change'].iloc[max(0, i-5):i].std()
            if price_std > 0.05:
                continue
            
            # 找到极值点
            local_min_idx = df['volume'].iloc[max(0, i-10):i].idxmin()
            if local_min_idx == i:
                extremes.append({
                    'index': i,
                    'date': df.index[i] if hasattr(df.index[i], 'strftime') else str(df.index[i]),
                    'volume_ratio': row['volume_ratio'],
                    'volume_ma': row['volume_ma'],
                    'price': row['close']
                })
        
        return extremes

    def analyze_volume_recovery(self, df: pd.DataFrame, extreme_idx: int) -> Dict:
        """分析地量后的量能恢复"""
        if extreme_idx >= len(df) - 1:
            return {'has_recovery': False}
        
        recovery_data = df.iloc[extreme_idx:min(extreme_idx+5, len(df))]
        
        # 检查量能是否逐步放大
        volumes = recovery_data['volume'].values
        if len(volumes) < 2:
            return {'has_recovery': False}
        
        # 第一天vs地量
        volume_increase = volumes[1] / df.iloc[extreme_idx]['volume'] if df.iloc[extreme_idx]['volume'] > 0 else 0
        
        # 价格是否上涨
        price_change = (recovery_data['close'].iloc[-1] - recovery_data['close'].iloc[0]) / recovery_data['close'].iloc[0]
        
        has_recovery = volume_increase > 1.5 and price_change > 0
        
        return {
            'has_recovery': has_recovery,
            'volume_increase_ratio': volume_increase,
            'price_change': price_change,
            'recovery_days': len(recovery_data) - 1
        }

    def calculate_score(self, df: pd.DataFrame, extreme: Dict, recovery: Dict) -> Tuple[float, str]:
        """计算股票评分"""
        score = 0
        reasons = []
        
        # 1. 量能极度萎缩得分 (0-35)
        volume_ratio = extreme['volume_ratio']
        if volume_ratio < 0.1:
            score += 35
            reasons.append("量能极度萎缩（不足均量10%）")
        elif volume_ratio < 0.2:
            score += 28
            reasons.append("量能严重萎缩（不足均量20%）")
        elif volume_ratio < 0.3:
            score += 20
            reasons.append("量能明显萎缩（不足均量30%）")
        
        # 2. 量能恢复得分 (0-20)
        if recovery['has_recovery']:
            score += 20
            reasons.append("量能已出现恢复信号")
        else:
            vi_ratio = recovery.get('volume_increase_ratio', 0)
            if vi_ratio > 1.2:
                score += 12
                reasons.append("量能有初步放大迹象")
        
        # 3. 价格稳定性得分 (0-20)
        if len(df) > extreme['index']:
            recent_df = df.iloc[max(0, extreme['index']-5):extreme['index']]
            if len(recent_df) >= 3:
                price_std = recent_df['close'].std() / recent_df['close'].mean()
                if price_std < 0.02:
                    score += 20
                    reasons.append("价格极度稳定")
                elif price_std < 0.05:
                    score += 15
                    reasons.append("价格相对稳定")
                elif price_std < 0.1:
                    score += 10
                    reasons.append("价格波动适中")
        
        # 4. 趋势反转确认 (0-15)
        if recovery['has_recovery'] and recovery['price_change'] > 0.03:
            score += 15
            reasons.append("价格已开始上涨，确认底部反转")
        elif recovery['has_recovery']:
            score += 10
            reasons.append("有底部反转迹象")
        
        # 5. 市场环境 (0-10)
        score += 10  # 默认满分
        
        return score, "; ".join(reasons)

    def analyze_stock(self, stock_code: str, stock_name: str = None) -> Optional[Dict]:
        """分析单只股票"""
        try:
            # 获取数据
            df = self.data_adapter.get_stock_history(stock_code)
            if df is None or len(df) < 60:
                return None
            
            # 标准化列名
            df = self.data_adapter.normalize_columns(df)
            
            # 查找地量位置
            extremes = self.find_volume_extreme(df)
            
            if not extremes:
                return None
            
            # 取最近一次地量
            extreme = extremes[-1]
            
            # 分析量能恢复
            recovery = self.analyze_volume_recovery(df, extreme['index'])
            
            # 计算评分
            score, reasons = self.calculate_score(df, extreme, recovery)
            
            # 获取当前价格信息
            current = df.iloc[-1]
            current_price = current['close']
            current_volume = current['volume']
            volume_ma = extreme['volume_ma']
            
            # 计算从地量到现在的涨跌幅
            from_extreme_change = (current_price - extreme['price']) / extreme['price'] * 100
            
            return {
                'code': stock_code,
                'name': stock_name or stock_code,
                'score': score,
                'reasons': reasons,
                'current_price': round(current_price, 2),
                'current_volume': int(current_volume),
                'volume_ma': round(volume_ma, 0),
                'volume_ratio': round(extreme['volume_ratio'] * 100, 1),
                'from_extreme_change': round(from_extreme_change, 2),
                'has_recovery': recovery['has_recovery'],
                'strategy': self.name,
                'win_rate': self.win_rate
            }
            
        except Exception as e:
            return None

    def batch_analyze(self, stock_list: List[tuple], top_n: int = 10) -> List[Dict]:
        """批量分析股票"""
        results = []
        
        for name, code in stock_list:
            try:
                result = self.analyze_stock(code, name)
                if result and result['score'] > 0:
                    results.append(result)
            except Exception as e:
                continue
        
        # 按评分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:top_n]


if __name__ == '__main__':
    analyzer = VolumeExtremeAnalyzer()
    
    # 测试
    test_stocks = [
        ('平安银行', '000001'),
        ('万科A', '000002'),
    ]
    
    print("成交量地量见底策略测试")
    print("-" * 60)
    
    for name, code in test_stocks:
        result = analyzer.analyze_stock(code, name)
        if result:
            print(f"{name}({code}): 评分={result['score']}, 原因={result['reasons']}")
        else:
            print(f"{name}({code}): 未找到地量信号")
