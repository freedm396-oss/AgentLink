# skills/scripts/hk_ma_pullback_analyzer.py

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
港股缩量回踩均线分析器
识别港股机构股缩量回踩20日均线的买入机会
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class HKMaPullbackAnalyzer:
    """港股缩量回踩均线分析器"""
    
    def __init__(self):
        self.name = "港股缩量回踩均线策略"
        self.win_rate = 0.68
        
        # 港股特化参数
        self.ma_period = 20
        self.volume_ma_period = 20
        self.shrink_ratio = 0.6
        self.min_avg_volume = 20000000  # 2000万港元
        self.min_price = 1.0            # 最小股价1港元
        self.min_market_cap = 100000000000  # 100亿港元
        
        # 评分权重
        self.weights = {
            'trend': 0.35,
            'pullback': 0.30,
            'volume': 0.25,
            'liquidity': 0.10
        }
        
    def analyze_stock(self, stock_code: str, stock_name: str) -> Optional[Dict]:
        """分析单只港股是否出现回踩信号"""
        # 获取数据
        df = self._get_hk_stock_data(stock_code)
        if df is None or len(df) < self.ma_period + 20:
            return None
        
        # 计算指标
        df = self._calculate_indicators(df)
        
        # 获取最新数据
        latest = df.iloc[-1]
        
        # 1. 流动性过滤（港股特化）
        liquidity_check = self._check_liquidity(latest, df)
        if not liquidity_check['passed']:
            return None
        
        # 2. 趋势分析
        trend = self._analyze_trend(df)
        if trend['score'] == 0:
            return None
        
        # 3. 回踩分析
        pullback = self._analyze_pullback(latest, df)
        if pullback['score'] == 0:
            return None
        
        # 4. 缩量分析
        volume = self._analyze_volume(latest, df)
        
        # 5. 流动性评分
        liquidity = self._score_liquidity(latest, df)
        
        # 计算总分
        total_score = self._calculate_total_score(
            trend, pullback, volume, liquidity
        )
        
        if total_score < 70:
            return None
        
        # 计算买卖点
        entry = self._calculate_entry(latest, pullback)
        stop_loss = self._calculate_stop(latest)
        targets = self._calculate_targets(entry)
        
        return {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'signal': 'BUY' if total_score >= 75 else 'WATCH',
            'score': round(total_score, 2),
            'current_price': round(latest['close'], 2),
            'ma20': round(latest['ma20'], 2),
            'deviation': round(latest['deviation'], 2),
            'volume_ratio': round(volume['volume_ratio'], 2),
            'avg_volume_hkd': round(latest['avg_volume_hkd'] / 10000, 2),
            'entry_price': round(entry, 2),
            'stop_loss': round(stop_loss, 2),
            'target1': round(targets[0], 2),
            'target2': round(targets[1], 2),
            'target3': round(targets[2], 2),
            'details': {
                'trend': trend,
                'pullback': pullback,
                'volume': volume,
                'liquidity': liquidity
            },
            'suggestion': self._generate_suggestion(total_score, stock_name),
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _get_hk_stock_data(self, stock_code: str) -> Optional[pd.DataFrame]:
        """获取港股历史数据"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=120)
            
            df = ak.stock_hk_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                adjust="qfq"
            )
            
            if df is not None and len(df) > 0:
                # akshare 返回中文列名，统一重命名为英文
                col_map = {
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'turnover',
                    '振幅': 'amplitude',
                    '涨跌幅': 'pct_change',
                    '涨跌额': 'price_change',
                    '换手率': 'turnover_rate',
                }
                df.rename(columns=col_map, inplace=True)
                df['date'] = pd.to_datetime(df['date'])
                # 成交额转换为港元（akshare返回的是人民币需估算，港股成交额单位通常是港元）
                # 这里直接使用原始值，单位为港元
                return df
        except Exception as e:
            print(f"获取港股数据失败 {stock_code}: {e}")
        
        return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        # 移动平均线
        df['ma20'] = df['close'].rolling(self.ma_period).mean()
        df['ma60'] = df['close'].rolling(60).mean()
        
        # 计算20日线斜率
        df['ma20_slope'] = df['ma20'].diff(5) / 5
        
        # 成交量均线
        df['volume_ma20'] = df['volume'].rolling(self.volume_ma_period).mean()
        
        # 成交额均线（港元）
        if 'turnover' in df.columns:
            df['avg_volume_hkd'] = df['turnover'].rolling(self.volume_ma_period).mean()
        else:
            # 如果没有成交额数据，用成交量估算
            df['avg_volume_hkd'] = df['volume'] * df['close'].rolling(20).mean()
        
        # 偏离度
        df['deviation'] = (df['close'] - df['ma20']) / df['ma20'] * 100
        
        # 成交量比率
        df['volume_ratio'] = df['volume'] / df['volume_ma20']
        
        return df
    
    def _check_liquidity(self, latest: pd.Series, df: pd.DataFrame) -> Dict:
        """检查流动性（港股特化）"""
        current_price = latest['close']
        avg_volume_hkd = latest.get('avg_volume_hkd', 0)
        
        # 仙股过滤
        if current_price < self.min_price:
            return {'passed': False, 'reason': f"股价{current_price}低于{self.min_price}港元（仙股）"}
        
        # 成交额过滤
        if avg_volume_hkd < self.min_avg_volume:
            return {'passed': False, 'reason': f"平均成交额{avg_volume_hkd/10000:.0f}万低于2000万港元"}
        
        # 市值估算（简化）
        return {'passed': True, 'reason': '流动性达标'}
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """分析趋势"""
        latest = df.iloc[-1]
        
        # 20日线斜率
        slope = latest['ma20_slope']
        is_slope_up = slope > 0
        
        # 股价位置
        above_ma60 = latest['close'] > latest['ma60']
        
        if is_slope_up and above_ma60:
            if slope > 0.1:
                score = 100
                level = "强势上升趋势"
            elif slope > 0.05:
                score = 85
                level = "良好上升趋势"
            else:
                score = 70
                level = "温和上升趋势"
        elif is_slope_up:
            score = 60
            level = "上升趋势（需确认）"
        else:
            score = 0
            level = "非上升趋势"
        
        return {
            'score': score,
            'level': level,
            'slope': round(slope, 3),
            'above_ma60': above_ma60
        }
    
    def _analyze_pullback(self, latest: pd.Series, df: pd.DataFrame) -> Dict:
        """分析回踩位置"""
        deviation = abs(latest['deviation'])
        
        if deviation < 0.5:
            score = 100
            level = "精确回踩20日线"
        elif deviation < 1.0:
            score = 85
            level = "接近20日线"
        elif deviation < 2.0:
            score = 70
            level = "回踩20日线附近"
        else:
            score = 0
            level = "偏离过大"
        
        return {
            'score': score,
            'level': level,
            'deviation': round(latest['deviation'], 2)
        }
    
    def _analyze_volume(self, latest: pd.Series, df: pd.DataFrame) -> Dict:
        """分析缩量情况"""
        volume_ratio = latest['volume_ratio']
        
        if volume_ratio < 0.4:
            score = 100
            level = "极度缩量"
        elif volume_ratio < 0.5:
            score = 85
            level = "明显缩量"
        elif volume_ratio < 0.6:
            score = 70
            level = "温和缩量"
        else:
            score = 0
            level = "缩量不足"
        
        return {
            'score': score,
            'level': level,
            'volume_ratio': round(volume_ratio, 2)
        }
    
    def _score_liquidity(self, latest: pd.Series, df: pd.DataFrame) -> Dict:
        """流动性评分"""
        avg_volume_hkd = latest.get('avg_volume_hkd', 0)
        current_price = latest['close']
        
        # 成交额评分
        if avg_volume_hkd >= 100000000:  # 1亿港元
            volume_score = 100
            volume_level = "超高流动性"
        elif avg_volume_hkd >= 50000000:  # 5000万港元
            volume_score = 85
            volume_level = "高流动性"
        elif avg_volume_hkd >= 20000000:  # 2000万港元
            volume_score = 70
            volume_level = "良好流动性"
        else:
            volume_score = 40
            volume_level = "流动性不足"
        
        # 股价评分
        if current_price >= 50:
            price_score = 100
        elif current_price >= 20:
            price_score = 85
        elif current_price >= 5:
            price_score = 70
        else:
            price_score = 50
        
        score = (volume_score * 0.7 + price_score * 0.3)
        
        return {
            'score': round(score, 2),
            'level': volume_level,
            'avg_volume_hkd': round(avg_volume_hkd / 10000, 2),
            'current_price': current_price
        }
    
    def _calculate_total_score(self, trend: Dict, pullback: Dict,
                               volume: Dict, liquidity: Dict) -> float:
        """计算总分"""
        total = (
            trend['score'] * self.weights['trend'] +
            pullback['score'] * self.weights['pullback'] +
            volume['score'] * self.weights['volume'] +
            liquidity['score'] * self.weights['liquidity']
        )
        return total
    
    def _calculate_entry(self, latest: pd.Series, pullback: Dict) -> float:
        """计算入场价"""
        return latest['close']
    
    def _calculate_stop(self, latest: pd.Series) -> float:
        """计算止损价"""
        return latest['close'] * 0.93  # 7%止损
    
    def _calculate_targets(self, entry: float) -> Tuple[float, float, float]:
        """计算目标位"""
        return (entry * 1.08, entry * 1.12, entry * 1.15)
    
    def _generate_suggestion(self, score: float, stock_name: str) -> str:
        """生成建议"""
        if score >= 85:
            return f"强烈推荐：{stock_name}完美回踩20日线，缩量明显，建议积极买入"
        elif score >= 75:
            return f"推荐：{stock_name}有效回踩20日线，建议分批建仓"
        elif score >= 70:
            return f"关注：{stock_name}回踩20日线附近，等待确认"
        else:
            return "暂缓：条件不充分，继续观察"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='港股缩量回踩均线策略')
    parser.add_argument('--stock', type=str, help='港股代码')
    parser.add_argument('--name', type=str, help='股票名称')
    
    args = parser.parse_args()
    
    if args.stock:
        analyzer = HKMaPullbackAnalyzer()
        result = analyzer.analyze_stock(args.stock, args.name or args.stock)
        
        if result:
            print("\n" + "=" * 60)
            print(f"港股缩量回踩均线分析报告")
            print("=" * 60)
            print(f"股票: {result['stock_name']}({result['stock_code']})")
            print(f"综合评分: {result['score']}分")
            print(f"信号: {result['signal']}")
            print(f"当前价格: {result['current_price']}港元")
            print(f"20日均线: {result['ma20']}港元")
            print(f"偏离度: {result['deviation']}%")
            print(f"缩量比率: {result['volume_ratio']}")
            print(f"平均成交额: {result['avg_volume_hkd']}万港元")
            print(f"建议入场: {result['entry_price']}")
            print(f"止损价格: {result['stop_loss']} (-7%)")
            print(f"目标价格: {result['target1']} / {result['target2']} / {result['target3']}")
            print(f"操作建议: {result['suggestion']}")
            print("=" * 60)
        else:
            print(f"{args.stock}不符合回踩条件")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()