#!/usr/bin/env python3
"""
港股财报超预期策略 - 核心分析器
HK Earnings Surprise Analyzer
"""

import os
import sys
import yaml
import numpy as np
import pandas as pd

try:
    import requests
except ImportError:
    requests = None


class HKEarningsAnalyzer:
    """财报超预期分析器"""

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "config", "strategy_config.yaml"
            )
        self.config = self._load_config(config_path)
        self.proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}

    def _load_config(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _to_yahoo_code(self, symbol):
        """H股代码转 Yahoo Finance 格式"""
        raw = symbol.replace('.HK', '').lstrip('0') or '0'
        orig = symbol.replace('.HK', '')
        leading_zeros = len(orig) - len(orig.lstrip('0'))
        if leading_zeros >= 1:
            code = raw.zfill(len(raw) + 1)
        else:
            code = raw
        return code + '.HK'

    def _get_price_data(self, symbol):
        """获取近期股价数据"""
        code = self._to_yahoo_code(symbol)
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}'
        params = {'interval': '1d', 'range': '60d'}
        try:
            r = requests.get(url, params=params, proxies=self.proxies,
                           timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            data = r.json().get('chart', {}).get('result')
            if not data:
                return None
            d = data[0]
            timestamps = d['timestamp']
            quotes = d['indicators']['quote'][0]
            df = pd.DataFrame({
                'date': pd.to_datetime(timestamps, unit='s'),
                'close': quotes.get('close'),
                'volume': quotes.get('volume'),
            })
            df = df.dropna()
            print(f"  股价来源: Yahoo Finance ({len(df)} 条)")
            return df.tail(60)
        except Exception as e:
            print(f"  股价获取失败: {e}")
            return self._get_mock_price_data(symbol)

    def _get_mock_price_data(self, symbol):
        """模拟股价数据"""
        dates = pd.date_range(end=pd.Timestamp.today(), periods=60, freq='D')
        np.random.seed(hash(symbol) % 1000)
        base = 100
        trend = np.concatenate([
            np.linspace(0, 15, 30),
            np.array([8]),  # 业绩公告跳空上涨
            np.linspace(8, 20, 29),
        ])
        data = {
            'date': dates,
            'close': base + trend + np.random.randn(60) * 2,
            'volume': np.random.randint(5000000, 50000000, 60),
        }
        return pd.DataFrame(data)

    def _get_earnings_data(self, symbol):
        """
        获取财报数据（模拟数据）
        实际应从港交所披露易获取业绩公告
        """
        np.random.seed(hash(symbol) % 1000)

        known_earnings = {
            '0700': {  # 腾讯
                'net_profit_yoy': 0.35,
                'revenue_yoy': 0.22,
                'eps_surprise': 0.18,
                'announce_days_ago': 5,
                'price_reaction': 0.08,  # 公告后上涨8%
            },
            '9988': {  # 阿里
                'net_profit_yoy': 0.28,
                'revenue_yoy': 0.18,
                'eps_surprise': 0.12,
                'announce_days_ago': 3,
                'price_reaction': 0.05,
            },
            '3690': {  # 美团
                'net_profit_yoy': 0.45,
                'revenue_yoy': 0.32,
                'eps_surprise': 0.25,
                'announce_days_ago': 2,
                'price_reaction': 0.12,
            },
            '0941': {  # 中移动
                'net_profit_yoy': 0.15,
                'revenue_yoy': 0.10,
                'eps_surprise': 0.05,
                'announce_days_ago': 8,
                'price_reaction': 0.02,
            },
            '0939': {  # 建行
                'net_profit_yoy': 0.08,
                'revenue_yoy': 0.05,
                'eps_surprise': 0.03,
                'announce_days_ago': 10,
                'price_reaction': -0.01,
            },
        }

        raw = symbol.replace('.HK', '').lstrip('0')
        if raw in known_earnings:
            return known_earnings[raw]

        # 模拟随机财报
        surprise = np.random.choice([True, False], p=[0.4, 0.6])
        if surprise:
            return {
                'net_profit_yoy': np.random.uniform(0.20, 0.50),
                'revenue_yoy': np.random.uniform(0.15, 0.40),
                'eps_surprise': np.random.uniform(0.08, 0.30),
                'announce_days_ago': np.random.randint(1, 15),
                'price_reaction': np.random.uniform(0.02, 0.15),
            }
        else:
            return {
                'net_profit_yoy': np.random.uniform(-0.10, 0.20),
                'revenue_yoy': np.random.uniform(0.00, 0.15),
                'eps_surprise': np.random.uniform(-0.05, 0.08),
                'announce_days_ago': np.random.randint(1, 15),
                'price_reaction': np.random.uniform(-0.05, 0.05),
            }

    def check_growth_standards(self, earnings):
        """检查业绩增长标准"""
        cfg = self.config['growth_standards']
        net_ok = earnings['net_profit_yoy'] >= cfg['min_net_profit_yoy']
        rev_ok = earnings['revenue_yoy'] >= cfg['min_revenue_yoy']
        return net_ok and rev_ok

    def check_surprise(self, earnings):
        """检查超预期"""
        cfg = self.config['surprise_standards']
        surprise_ok = earnings['eps_surprise'] >= cfg['min_surprise_pct']
        return surprise_ok

    def check_market_reaction(self, earnings, price_df):
        """检查市场反应"""
        reaction_ok = earnings['price_reaction'] > 0  # 公告后股价上涨
        return reaction_ok

    def score_surprise(self, earnings):
        """超预期评分"""
        eps = earnings['eps_surprise']
        if eps > 0.30:
            return 100
        elif eps > 0.20:
            return 85
        elif eps > 0.10:
            return 70
        else:
            return 40

    def score_growth_quality(self, earnings):
        """增长质量评分"""
        yoy = earnings['net_profit_yoy']
        if yoy > 0.40:
            return 100
        elif yoy > 0.25:
            return 80
        elif yoy > 0.15:
            return 60
        else:
            return 30

    def score_market_reaction(self, earnings):
        """市场反应评分"""
        reaction = earnings['price_reaction']
        if reaction > 0.10:
            return 100
        elif reaction > 0.05:
            return 80
        elif reaction > 0:
            return 60
        else:
            return 30

    def analyze_stock(self, symbol, name=""):
        """分析单只股票"""
        print(f"\n分析 {symbol} {name}...")

        # 获取财报数据
        earnings = self._get_earnings_data(symbol)

        # 获取股价数据
        price_df = self._get_price_data(symbol)

        # 各条件检查
        growth_ok = self.check_growth_standards(earnings)
        surprise_ok = self.check_surprise(earnings)
        reaction_ok = self.check_market_reaction(earnings, price_df)

        # 评分
        surprise_score = self.score_surprise(earnings)
        growth_score = self.score_growth_quality(earnings)
        reaction_score = self.score_market_reaction(earnings)

        cfg = self.config
        weights = cfg.get('scoring', {}).get('weights', {
            'surprise_score': 0.30, 'growth_quality': 0.25,
            'market_reaction': 0.25, 'risk_level': 0.20
        })

        total_score = (
            surprise_score * weights.get('surprise_score', 0.30) +
            growth_score * weights.get('growth_quality', 0.25) +
            reaction_score * weights.get('market_reaction', 0.25) +
            70 * weights.get('risk_level', 0.20)  # 风险评分（简化）
        )

        # 信号判断
        if total_score >= 85:
            signal, rating = "强烈买入", "极强"
        elif total_score >= 75:
            signal, rating = "买入", "强"
        elif total_score >= 70:
            signal, rating = "观望", "中等"
        else:
            signal, rating = "不建议", "弱"

        # 超预期等级
        if earnings['eps_surprise'] > 0.20:
            surprise_level = "显著超预期"
        elif earnings['eps_surprise'] > 0.10:
            surprise_level = "超预期"
        elif earnings['eps_surprise'] > 0:
            surprise_level = "略超预期"
        else:
            surprise_level = "不及预期"

        # 增长质量等级
        if earnings['net_profit_yoy'] > 0.35:
            quality_level = "优秀"
        elif earnings['net_profit_yoy'] > 0.20:
            quality_level = "良好"
        elif earnings['net_profit_yoy'] > 0.10:
            quality_level = "一般"
        else:
            quality_level = "较差"

        current_price = price_df['close'].iloc[-1] if price_df is not None else 100.0
        entry_price = current_price
        stop_loss = entry_price * (1 - cfg['risk']['stop_loss_pct'])
        take_profit = entry_price * (1 + cfg['risk']['take_profit_pct'])

        result = {
            'symbol': symbol,
            'name': name,
            'net_profit_yoy': earnings['net_profit_yoy'] * 100,
            'revenue_yoy': earnings['revenue_yoy'] * 100,
            'eps_surprise': earnings['eps_surprise'] * 100,
            'surprise_score': surprise_score,
            'surprise_level': surprise_level,
            'growth_score': growth_score,
            'quality_level': quality_level,
            'reaction_score': reaction_score,
            'reaction_level': '上涨' if earnings['price_reaction'] > 0 else '下跌',
            'announce_days_ago': earnings['announce_days_ago'],
            'score': round(total_score, 1),
            'rating': rating,
            'signal': signal,
            'growth_ok': growth_ok,
            'surprise_ok': surprise_ok,
            'reaction_ok': reaction_ok,
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'max_days': cfg['risk']['max_holding_days'],
            'suggestion': f"评分{total_score:.0f}分({rating})，{signal}",
        }
        return result

    def print_result(self, result):
        if result is None:
            return
        print(f"\n{'=' * 50}")
        print(f"分析结果: {result['symbol']} {result['name']}")
        print(f"{'=' * 50}")
        print(f"  净利润增长: {result['net_profit_yoy']:.1f}%")
        print(f"  营收增长: {result['revenue_yoy']:.1f}%")
        print(f"  EPS超预期: {result['eps_surprise']:.1f}%")
        print(f"  超预期评分: {result['surprise_score']}/100 ({result['surprise_level']})")
        print(f"  增长质量: {result['growth_score']}/100 ({result['quality_level']})")
        print(f"  市场反应: {result['reaction_score']}/100 ({result['reaction_level']})")
        print(f"  公告距今: {result['announce_days_ago']}日")
        print(f"  综合评分: {result['score']} ({result['rating']})")
        print(f"  信号: {result['signal']}")
        print(f"  入场价: {result['entry_price']} | 止损: {result['stop_loss']} | 止盈: {result['take_profit']}")
        print(f"  最长持仓: {result['max_days']}日")
        print(f"  建议: {result['suggestion']}")
        print(f"{'=' * 50}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='港股财报超预期分析')
    parser.add_argument('--stock', default='0700.HK', help='股票代码')
    parser.add_argument('--name', default='腾讯控股', help='股票名称')
    args = parser.parse_args()

    analyzer = HKEarningsAnalyzer()
    result = analyzer.analyze_stock(args.stock, args.name)
    analyzer.print_result(result)


if __name__ == "__main__":
    main()
