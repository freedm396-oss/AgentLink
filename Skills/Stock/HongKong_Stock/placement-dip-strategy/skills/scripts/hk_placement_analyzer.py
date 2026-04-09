#!/usr/bin/env python3
"""
港股配股砸盘抄底策略 - 核心分析器
HK Placement Dip Strategy Analyzer
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


class HKPlacementAnalyzer:
    """配股砸盘分析器"""

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

    def get_price_data(self, symbol):
        """获取近期股价数据"""
        code = self._to_yahoo_code(symbol)
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}'
        params = {'interval': '1d', 'range': '30d'}
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
            })
            df = df.dropna()
            print(f"  股价来源: Yahoo Finance ({len(df)} 条)")
            return df.tail(30)
        except Exception as e:
            print(f"  股价获取失败: {e}，使用模拟数据")
            return self._get_mock_price_data(symbol)

    def _get_mock_price_data(self, symbol):
        """模拟股价数据"""
        dates = pd.date_range(end=pd.Timestamp.today(), periods=30, freq='D')
        np.random.seed(hash(symbol) % 1000)
        base = 100
        # 模拟公告日前高位，公告日后急跌
        trend = np.concatenate([
            np.linspace(0, 10, 19),    # 上涨19天
            np.array([-12]),            # 公告日暴跌12%
            np.linspace(-12, -8, 5),   # 继续震荡
            np.linspace(-8, -5, 5),    # 略有反弹
        ])  # 19+1+5+5 = 30，与dates一致
        data = {
            'date': dates,
            'close': base + trend + np.random.randn(30) * 2,
        }
        return pd.DataFrame(data)

    def _get_placement_info(self, symbol):
        """
        获取配股信息（模拟数据）
        实际应从港交所披露易获取：
        https://www.hkexnews.hk/sha_recent_placement/sha_recent_placement_dataflow.aspx
        """
        np.random.seed(hash(symbol) % 1000)

        known_placements = {
            '0700': {  # 腾讯
                'placement_price': 380.0,
                'prev_close': 420.0,
                'drop_magnitude': -9.5,
                'fund_usage': '业务扩张',
                'institutional_count': 6,
                'days_since': 4,
            },
            '9988': {  # 阿里
                'placement_price': 98.0,
                'prev_close': 115.0,
                'drop_magnitude': -14.8,
                'fund_usage': '偿还债务',
                'institutional_count': 3,
                'days_since': 2,
            },
            '3690': {  # 美团
                'placement_price': 82.0,
                'prev_close': 90.0,
                'drop_magnitude': -8.9,
                'fund_usage': '业务扩张',
                'institutional_count': 5,
                'days_since': 1,
            },
        }

        raw = symbol.replace('.HK', '').lstrip('0')
        if raw in known_placements:
            info = known_placements[raw].copy()
        else:
            prev = np.random.uniform(50, 200)
            disc = np.random.uniform(0.06, 0.18)
            drop = -np.random.uniform(0.07, 0.16) * 100
            usage_good = np.random.random() > 0.3
            info = {
                'placement_price': prev * (1 - disc),
                'prev_close': prev,
                'drop_magnitude': drop,
                'fund_usage': '业务扩张' if usage_good else '偿还债务',
                'institutional_count': np.random.randint(1, 7),
                'days_since': np.random.randint(1, 8),
            }

        # 计算折价
        info['discount'] = (info['prev_close'] - info['placement_price']) / info['prev_close']
        return info

    def check_discount(self, discount):
        """检查配股折价 > 5%"""
        cfg = self.config['placement']
        threshold = cfg['discount_min']
        return discount > threshold

    def check_drop_magnitude(self, drop_magnitude):
        """检查跌幅在 -8% 到 -15% 区间"""
        cfg = self.config['placement']
        drop_min = cfg['drop_min']
        drop_max = cfg['drop_max']
        # drop_magnitude 是负数，所以 -8% < drop < -15%
        # 即 drop < -0.08 且 drop > -0.15
        return (-drop_max < drop_magnitude < -drop_min), drop_magnitude

    def check_fund_usage(self, fund_usage):
        """检查资金用途"""
        cfg = self.config['fund_usage']
        good_uses = cfg['good']
        return fund_usage in good_uses

    def check_institutions(self, count):
        """检查机构参与数 >= 3"""
        cfg = self.config['placement']
        return count >= cfg['min_institutions']

    def score_stock(self, discount, drop_magnitude, fund_usage, inst_count,
                   discount_ok, drop_ok, usage_ok, inst_ok):
        """综合评分"""
        score = 0
        cfg = self.config['placement']

        # 折价深度
        if discount > 0.20:
            score += 25
        elif discount > 0.15:
            score += 20
        elif discount > 0.10:
            score += 15
        elif discount_ok:
            score += 10

        # 跌幅区间
        if -0.15 < drop_magnitude <= -0.10:
            score += 25  # 最佳区间 -10%~-15%
        elif -0.10 < drop_magnitude <= -0.08:
            score += 20
        elif drop_ok:
            score += 15

        # 资金用途
        if fund_usage in ['并购', '研发投入']:
            score += 25
        elif fund_usage == '业务扩张':
            score += 20
        elif fund_usage == '产能扩张':
            score += 18
        elif usage_ok:
            score += 10

        # 机构背书
        if inst_count >= 5:
            score += 25
        elif inst_ok:
            score += 20
        elif inst_count >= 2:
            score += 10

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

    def analyze_stock(self, symbol, name=""):
        """分析单只股票"""
        print(f"\n分析 {symbol} {name}...")

        # 获取配股信息
        placement = self._get_placement_info(symbol)

        # 获取股价数据
        df = self.get_price_data(symbol)
        current_price = df['close'].iloc[-1] if df is not None and not df.empty else placement['prev_close']

        # 各条件检查
        discount_ok = self.check_discount(placement['discount'])
        drop_ok, drop_mag = self.check_drop_magnitude(placement['drop_magnitude'])
        usage_ok = self.check_fund_usage(placement['fund_usage'])
        inst_ok = self.check_institutions(placement['institutional_count'])

        # 综合评分
        score = self.score_stock(placement['discount'], placement['drop_magnitude'],
                                placement['fund_usage'], placement['institutional_count'],
                                discount_ok, drop_ok, usage_ok, inst_ok)
        signal, rating = self.get_signal(score)

        # 入场和止损
        entry_price = current_price
        stop_loss = entry_price * (1 - self.config['risk']['stop_loss_pct'])
        take_profit = entry_price * (1 + self.config['risk']['take_profit_pct'])

        result = {
            'symbol': symbol,
            'name': name,
            'current_price': current_price,
            'placement_price': placement['placement_price'],
            'prev_close': placement['prev_close'],
            'placement_discount': placement['discount'] * 100,
            'discount_ok': discount_ok,
            'drop_magnitude': placement['drop_magnitude'],
            'drop_ok': drop_ok,
            'fund_usage': placement['fund_usage'],
            'usage_ok': usage_ok,
            'institutional_count': placement['institutional_count'],
            'inst_ok': inst_ok,
            'days_since': placement['days_since'],
            'score': score,
            'rating': rating,
            'signal': signal,
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'max_days': self.config['holding']['max_days'],
            'suggestion': f"评分{score}分({rating})，{signal}",
        }
        return result

    def print_result(self, result):
        if result is None:
            return
        print(f"\n{'=' * 50}")
        print(f"分析结果: {result['symbol']} {result['name']}")
        print(f"{'=' * 50}")
        print(f"  当前价: {result['current_price']:.2f}")
        print(f"  配股价: {result['placement_price']:.2f} | 前收: {result['prev_close']:.2f}")
        print(f"  配股折价: {result['placement_discount']:.2f}% {'✅' if result['discount_ok'] else '❌'}")
        print(f"  公告日跌幅: {result['drop_magnitude']:.2f}% {'✅' if result['drop_ok'] else '❌'}")
        print(f"  资金用途: {result['fund_usage']} {'✅' if result['usage_ok'] else '❌'}")
        print(f"  机构参与: {result['institutional_count']}家 {'✅' if result['inst_ok'] else '❌'}")
        print(f"  距公告: {result['days_since']}日")
        print(f"  综合评分: {result['score']} ({result['rating']})")
        print(f"  信号: {result['signal']}")
        print(f"  入场价: {result['entry_price']} | 止损: {result['stop_loss']} | 止盈: {result['take_profit']}")
        print(f"  持仓上限: {result['max_days']}日")
        print(f"  建议: {result['suggestion']}")
        print(f"{'=' * 50}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='港股配股砸盘分析')
    parser.add_argument('--stock', default='0700.HK', help='股票代码')
    parser.add_argument('--name', default='腾讯控股', help='股票名称')
    args = parser.parse_args()

    analyzer = HKPlacementAnalyzer()
    result = analyzer.analyze_stock(args.stock, args.name)
    analyzer.print_result(result)


if __name__ == "__main__":
    main()
