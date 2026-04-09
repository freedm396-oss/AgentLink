#!/usr/bin/env python3
"""
港股AH溢价套利策略 - 核心分析器
HK AH Premium Arbitrage Analyzer
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


class HKAHPremiumAnalyzer:
    """AH溢价分析器"""

    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "config", "strategy_config.yaml"
            )
        self.config = self._load_config(config_path)
        self.proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
        self.fx_rate = self.config['fx']['assumed_rate']  # HKD/CNY

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

    def _get_a_stock_price(self, a_code):
        """
        获取A股价格（从 Sina Finance API 模拟）
        实际应使用 akshare 或 tushare 获取A股数据
        """
        np.random.seed(hash(a_code) % 1000)
        # 常见AH股A股价格模拟
        known_a = {
            '600028': 7.5,   # 中国石化
            '600036': 35.0,  # 招商银行
            '601318': 48.0,  # 中国平安
            '600030': 22.0,  # 中信证券
            '600019': 7.8,   # 宝钢股份
        }
        if a_code in known_a:
            return known_a[a_code] * (1 + np.random.uniform(-0.02, 0.02))
        return np.random.uniform(5, 50)

    def get_h_stock_data(self, symbol):
        """获取H股行情数据"""
        code = self._to_yahoo_code(symbol)
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}'
        params = {'interval': '1d', 'range': '90d'}
        try:
            r = requests.get(url, params=params, proxies=self.proxies,
                             timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            data = r.json().get('chart', {}).get('result')
            if not data:
                return None, None
            d = data[0]
            timestamps = d['timestamp']
            quotes = d['indicators']['quote'][0]
            df = pd.DataFrame({
                'date': pd.to_datetime(timestamps, unit='s'),
                'open': quotes.get('open'),
                'high': quotes.get('high'),
                'low': quotes.get('low'),
                'close': quotes.get('close'),
                'volume': quotes.get('volume'),
            })
            df = df.dropna()
            print(f"  H股数据来源: Yahoo Finance ({len(df)} 条)")
            return df.tail(90), df['close'].iloc[-1]
        except Exception as e:
            print(f"  H股数据获取失败: {e}，使用模拟")
            return self._get_mock_h_data(symbol), 100.0

    def _get_mock_h_data(self, symbol):
        """模拟H股数据"""
        dates = pd.date_range(end=pd.Timestamp.today(), periods=90, freq='D')
        np.random.seed(hash(symbol) % 1000)
        base = 100
        data = {
            'date': dates,
            'open': base + np.random.randn(90).cumsum() * 2,
            'high': base + 2 + np.random.randn(90).cumsum() * 2,
            'low': base - 2 + np.random.randn(90).cumsum() * 2,
            'close': base + np.random.randn(90).cumsum() * 2,
            'volume': np.random.randint(5000000, 50000000, 90),
        }
        return pd.DataFrame(data)

    def calculate_ah_premium(self, h_price, a_price_cny):
        """计算AH溢价率 = (A - H*FX) / (H*FX) * 100%"""
        h_in_cny = h_price * self.fx_rate
        if h_in_cny == 0:
            return 0.0
        premium = (a_price_cny - h_in_cny) / h_in_cny
        return premium

    def check_h_volume(self, df):
        """检查H股成交量 > 1000万港元"""
        vol = df['volume'].iloc[-1]
        threshold = self.config['volume']['h_min_million_hkd'] * 1000000
        return vol > threshold, vol / 1000000

    def check_a_volume(self, a_volume_cny):
        """检查A股成交量 > 5000万人民币"""
        threshold = self.config['volume']['a_min_million_cny'] * 1000000
        return a_volume_cny > threshold, a_volume_cny / 1000000

    def check_sector_trend(self, df):
        """
        检查行业趋势（H股行业指数 > MA20）
        简化：用恒生科技/恒生指数代替行业指数
        """
        # 这里用H股自身的MA20来判断
        ma20 = df['close'].rolling(window=20).mean().iloc[-1]
        current = df['close'].iloc[-1]
        if pd.isna(ma20):
            return True, "数据不足"
        return current > ma20, f"{'多头' if current > ma20 else '空头'}"

    def score_stock(self, ah_premium, h_vol_ok, a_vol_ok, sector_ok, h_vol_m, a_vol_m):
        """综合评分"""
        score = 0
        cfg = self.config['ah_premium']

        # AH溢价评分
        if ah_premium > 0.80:
            score += 35
        elif ah_premium > 0.50:
            score += 30
        elif ah_premium > 0.40:
            score += 25
        elif ah_premium > 0.30:
            score += 15

        # H股量能
        if h_vol_ok:
            score += 15
        elif h_vol_m > 5:
            score += 8

        # A股量能
        if a_vol_ok:
            score += 10
        elif a_vol_m > 20:
            score += 5

        # 行业趋势
        if sector_ok:
            score += 20

        return min(score, 100)

    def get_signal(self, score):
        if score >= 85:
            return "强烈买入", "极强"
        elif score >= 75:
            return "买入", "强"
        elif score >= 70:
            return "观望", "中等"
        else:
            return "不建议", "弱"

    def analyze_stock(self, hk_code, name="", a_code=None):
        """分析单只AH股票"""
        print(f"\n分析 {hk_code} {name}...")

        # 获取H股数据
        df, h_price = self.get_h_stock_data(hk_code)
        if df is None or df.empty:
            print(f"  无法获取H股数据")
            return None

        # 获取A股价格
        if a_code is None:
            a_code = hk_code  # 兜底
        a_price_cny = self._get_a_stock_price(a_code)

        # 计算AH溢价
        ah_premium = self.calculate_ah_premium(h_price, a_price_cny)
        ah_premium_pct = ah_premium * 100

        # 各条件检查
        h_vol_ok, h_vol_m = self.check_h_volume(df)
        # A股成交量模拟
        np.random.seed(hash(a_code) % 1000)
        a_volume_cny = np.random.uniform(30, 200) * 1000000
        a_vol_ok, a_vol_m = self.check_a_volume(a_volume_cny)
        sector_ok, sector_str = self.check_sector_trend(df)

        # 综合评分
        score = self.score_stock(ah_premium, h_vol_ok, a_vol_ok, sector_ok, h_vol_m, a_vol_m)
        signal, rating = self.get_signal(score)

        entry_price = h_price  # 明日开盘买入
        stop_loss = entry_price * (1 - self.config['risk']['h_stop_loss_pct'])

        result = {
            'symbol': hk_code,
            'a_code': a_code,
            'name': name,
            'h_price': h_price,
            'a_price': a_price_cny,
            'ah_premium': ah_premium_pct,
            'h_volume_ok': h_vol_ok,
            'h_volume_m': h_vol_m,
            'a_volume_ok': a_vol_ok,
            'a_volume_m': a_vol_m,
            'sector_trend': sector_str,
            'sector_ok': sector_ok,
            'score': score,
            'rating': rating,
            'signal': signal,
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'exit_premium': self.config['ah_premium']['exit_threshold'] * 100,
            'max_days': self.config['holding']['max_days'],
            'suggestion': f"评分{score}分({rating})，{signal}",
        }
        return result

    def print_result(self, result):
        if result is None:
            return
        print(f"\n{'=' * 50}")
        print(f"分析结果: {result['symbol']} {result['name']} (A股:{result['a_code']})")
        print(f"{'=' * 50}")
        print(f"  H股价格: {result['h_price']:.2f} 港元")
        print(f"  A股价格: {result['a_price']:.2f} 人民币")
        print(f"  AH溢价率: {result['ah_premium']:.2f}% {'✅入场' if result['ah_premium'] > 40 else '❌'}")
        print(f"  H股量能: {result['h_volume_m']:.1f}M 港元 {'✅' if result['h_volume_ok'] else '❌'}")
        print(f"  A股量能: {result['a_volume_m']:.1f}M 人民币 {'✅' if result['a_volume_ok'] else '❌'}")
        print(f"  行业趋势: {result['sector_trend']} {'✅' if result['sector_ok'] else '❌'}")
        print(f"  综合评分: {result['score']} ({result['rating']})")
        print(f"  信号: {result['signal']}")
        print(f"  入场价: {result['entry_price']} | 止损: {result['stop_loss']} (-8%)")
        print(f"  止盈: 溢价<{result['exit_premium']}% 或满{result['max_days']}日")
        print(f"  建议: {result['suggestion']}")
        print(f"{'=' * 50}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='港股AH溢价套利分析')
    parser.add_argument('--stock', default='0700', help='H股代码')
    parser.add_argument('--name', default='腾讯控股', help='股票名称')
    parser.add_argument('--a_stock', default=None, help='A股代码（可选）')
    args = parser.parse_args()

    analyzer = HKAHPremiumAnalyzer()
    result = analyzer.analyze_stock(args.stock, args.name, args.a_stock)
    analyzer.print_result(result)


if __name__ == "__main__":
    main()
