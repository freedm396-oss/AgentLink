#!/usr/bin/env python3
"""
均线多头排列策略分析器
支持多数据源：akshare、tushare、baostock、yfinance
"""

import os
import sys

# 清除代理环境变量
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    if key in os.environ:
        if key in os.environ:
            del os.environ[key]

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
    sys.path.insert(0, '/home/qinliming/.npm-global/lib/node_modules/openclaw/skills/Stock/Chinese_Stock/ma-bullish-strategy')
    from skills.scripts.data_source_adapter import DataSourceAdapter


class MABullishAnalyzer:
    """均线多头排列分析器"""

    def __init__(self, data_source: str = "auto", analysis_date: Optional[str] = None):
        self.name = "均线多头排列策略"
        self.ma_short = 5
        self.ma_mid = 10
        self.ma_long = 20
        self.volume_ma = 20

        # 评分权重
        self.weights = {
            'ma_arrangement': 0.35,
            'price_position': 0.20,
            'volume_trend': 0.20,
            'trend_strength': 0.15,
            'market_environment': 0.10
        }

        if analysis_date:
            self.analysis_date = datetime.strptime(analysis_date, '%Y-%m-%d')
        else:
            self.analysis_date = None

        self.data_adapter = DataSourceAdapter(data_source)
        if not self.data_adapter.data_source:
            raise RuntimeError("没有可用的数据源，请安装akshare、tushare、baostock或yfinance")

    def calculate_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算均线"""
        df = df.copy()
        df[f'ma{self.ma_short}'] = df['close'].rolling(window=self.ma_short).mean()
        df[f'ma{self.ma_mid}'] = df['close'].rolling(window=self.ma_mid).mean()
        df[f'ma{self.ma_long}'] = df['close'].rolling(window=self.ma_long).mean()
        df[f'volume_ma'] = df['volume'].rolling(window=self.volume_ma).mean()
        return df

    def is_ma_bullish(self, df: pd.DataFrame) -> bool:
        """判断是否均线多头排列"""
        if len(df) < self.ma_long:
            return False
        latest = df.iloc[-1]
        ma_s = latest[f'ma{self.ma_short}']
        ma_m = latest[f'ma{self.ma_mid}']
        ma_l = latest[f'ma{self.ma_long}']
        if pd.isna(ma_s) or pd.isna(ma_m) or pd.isna(ma_l):
            return False
        return ma_s > ma_m > ma_l

    def check_price_above_ma_long(self, df: pd.DataFrame) -> bool:
        """检查价格是否在长期均线上方"""
        if len(df) < 1:
            return False
        latest = df.iloc[-1]
        return latest['close'] > latest[f'ma{self.ma_long}']

    def check_volume_surge(self, df: pd.DataFrame, ratio: float = 1.2) -> bool:
        """检查成交量是否放大"""
        if len(df) < self.volume_ma:
            return False
        latest = df.iloc[-1]
        vol_ma = latest['volume_ma']
        if pd.isna(vol_ma) or vol_ma == 0:
            return False
        return latest['volume'] >= vol_ma * ratio

    def score_ma_arrangement(self, df: pd.DataFrame) -> float:
        """均线排列评分 0-100"""
        if not self.is_ma_bullish(df):
            return 0
        latest = df.iloc[-1]
        ma_s = latest[f'ma{self.ma_short}']
        ma_m = latest[f'ma{self.ma_mid}']
        ma_l = latest[f'ma{self.ma_long}']
        # 发散程度
        spread = (ma_s - ma_l) / ma_l * 100
        if spread > 15:
            return 100
        elif spread > 10:
            return 90
        elif spread > 5:
            return 80
        else:
            return 70

    def score_price_position(self, df: pd.DataFrame) -> float:
        """价格位置评分 0-100"""
        if len(df) < self.ma_long:
            return 0
        latest = df.iloc[-1]
        ma_l = latest[f'ma{self.ma_long}']
        if pd.isna(ma_l) or ma_l == 0:
            return 0
        position = (latest['close'] - ma_l) / ma_l * 100
        if position > 15:
            return 100
        elif position > 10:
            return 90
        elif position > 5:
            return 80
        elif position > 0:
            return 70
        else:
            return 30

    def score_volume_trend(self, df: pd.DataFrame) -> float:
        """成交量趋势评分 0-100"""
        if len(df) < 5:
            return 0
        recent_vol = df['volume'].tail(5).mean()
        older_vol = df['volume'].iloc[-10:-5].mean() if len(df) >= 10 else recent_vol
        if older_vol == 0:
            return 50
        ratio = recent_vol / older_vol
        if ratio >= 1.5:
            return 100
        elif ratio >= 1.3:
            return 85
        elif ratio >= 1.2:
            return 70
        elif ratio >= 1.0:
            return 60
        else:
            return 40

    def score_trend_strength(self, df: pd.DataFrame) -> float:
        """趋势强度评分 0-100（基于斜率）"""
        if len(df) < 10:
            return 0
        prices = df['close'].tail(20).values
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]
        avg_price = np.mean(prices)
        if avg_price == 0:
            return 0
        slope_pct = slope / avg_price * 100
        if slope_pct > 0.5:
            return 100
        elif slope_pct > 0.3:
            return 85
        elif slope_pct > 0.1:
            return 70
        elif slope_pct > 0:
            return 60
        else:
            return 30

    def score_market_environment(self, df: pd.DataFrame) -> float:
        """市场环境评分 0-100（基于大盘指数）"""
        # 简化版：使用自身的均线状态代表大盘环境
        if len(df) < self.ma_long:
            return 50
        df_ma = self.calculate_ma(df)
        if self.is_ma_bullish(df_ma):
            return 100
        return 40

    def calculate_total_score(self, df: pd.DataFrame) -> float:
        """计算总分"""
        return (
            self.score_ma_arrangement(df) * self.weights['ma_arrangement'] +
            self.score_price_position(df) * self.weights['price_position'] +
            self.score_volume_trend(df) * self.weights['volume_trend'] +
            self.score_trend_strength(df) * self.weights['trend_strength'] +
            self.score_market_environment(df) * self.weights['market_environment']
        )

    def analyze_stock(self, stock_code: str, stock_name: str = "") -> Dict:
        """分析单只股票"""
        result = {
            'code': stock_code,
            'name': stock_name or stock_code,
            'score': 0,
            'is_bullish': False,
            'signals': {},
            'data': None,
            'error': None
        }

        try:
            end_date = self.analysis_date.strftime('%Y-%m-%d') if self.analysis_date else None
            start_date = (self.analysis_date - timedelta(days=60)).strftime('%Y-%m-%d') if self.analysis_date else None

            df = self.data_adapter.get_stock_data(stock_code, start_date, end_date)
            if df is None or df.empty:
                result['error'] = '获取数据失败'
                return result

            df = self.calculate_ma(df)
            result['data'] = df

            is_bullish = self.is_ma_bullish(df)
            result['is_bullish'] = is_bullish

            if is_bullish:
                result['score'] = round(self.calculate_total_score(df), 2)
                result['signals'] = {
                    'ma_arrangement': self.score_ma_arrangement(df),
                    'price_position': self.score_price_position(df),
                    'volume_trend': self.score_volume_trend(df),
                    'trend_strength': self.score_trend_strength(df),
                    'market_environment': self.score_market_environment(df),
                }

            return result

        except Exception as e:
            result['error'] = str(e)
            return result

    def scan_all_stocks(self, top_n: int = 20) -> List[Dict]:
        """扫描全市场"""
        print(f"开始扫描全市场股票... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"使用数据源: {self.data_adapter.source}")

        try:
            stock_list = self.data_adapter.get_stock_list()
            if stock_list is None or stock_list.empty:
                print("获取股票列表失败")
                return []
            print(f"获取到{len(stock_list)}只股票")
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return []

        candidates = []
        total = len(stock_list)

        for idx, (_, row) in enumerate(stock_list.iterrows(), 1):
            code = str(row.get('code', '')).zfill(6)
            name = str(row.get('name', code))

            if idx % 100 == 0:
                print(f"  进度: {idx}/{total} ({idx*100//total}%)")

            try:
                result = self.analyze_stock(code, name)
                if result['is_bullish'] and result['score'] >= 70:
                    candidates.append(result)
            except Exception:
                continue

            if idx >= 2000:
                print(f"  已扫描{idx}只，限制扫描数量以加快速度")
                break

        candidates.sort(key=lambda x: x['score'], reverse=True)
        print(f"\n扫描完成，发现 {len(candidates)} 只符合条件")
        return candidates[:top_n]

    def print_analysis(self, result: Dict):
        """打印分析结果"""
        print("=" * 60)
        print(f"股票: {result['name']} ({result['code']})")
        print("=" * 60)

        if result['error']:
            print(f"❌ 错误: {result['error']}")
            return

        is_bullish = result['is_bullish']
        score = result['score']

        if is_bullish:
            print(f"✅ 均线多头排列 | 评分: {score}")
            if score >= 85:
                level = "🔴 强烈推荐"
            elif score >= 75:
                level = "🟡 推荐"
            else:
                level = "🟢 关注"
            print(f"   推荐等级: {level}")
        else:
            print(f"❌ 不符合均线多头排列条件")

        if result['signals']:
            print("\n分项评分:")
            for k, v in result['signals'].items():
                bar = "█" * int(v / 10)
                print(f"  {k}: {v:>3} {bar}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='均线多头排列策略分析器')
    parser.add_argument('--scan', action='store_true', help='扫描全市场（分析所有股票，较慢）')
    parser.add_argument('--stock', type=str, help='股票代码')
    parser.add_argument('--name', type=str, help='股票名称')
    parser.add_argument('--top', type=int, default=20, help='返回前N名')
    parser.add_argument('--source', type=str, default='auto',
                        help='数据源 (akshare/tushare/baostock/yfinance/auto)')
    parser.add_argument('--date', type=str, help='分析日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--sector', type=str, help='分析指定板块 (科技/医药/金融/消费/新能源/军工)')
    parser.add_argument('--all-sectors', action='store_true', help='分析所有板块')
    parser.add_argument('--stocks', type=str, help='分析指定股票列表，逗号分隔，如: 000001,000002,600000')
    args = parser.parse_args()

    try:
        analyzer = MABullishAnalyzer(data_source=args.source, analysis_date=args.date)
    except RuntimeError as e:
        print(f"❌ {e}")
        return

    if args.scan:
        results = analyzer.scan_all_stocks(top_n=args.top)
        for r in results:
            analyzer.print_analysis(r)
        print(f"\n共找到 {len(results)} 只符合条件的股票")

    elif args.stocks:
        stocks = [s.strip() for s in args.stocks.split(',')]
        for code in stocks:
            result = analyzer.analyze_stock(code, code)
            analyzer.print_analysis(result)

    elif args.stock:
        result = analyzer.analyze_stock(args.stock, args.name or args.stock)
        analyzer.print_analysis(result)

    elif args.all_sectors:
        from skills.scripts.sector_analyzer import SectorAnalyzer
        sector_analyzer = SectorAnalyzer(analyzer)
        results = sector_analyzer.analyze_all_sectors(analysis_date=args.date)
        for sector, result in results.items():
            print(f"\n{'='*60}")
            print(f"板块: {sector}")
            print(f"{'='*60}")
            for r in result:
                analyzer.print_analysis(r)

    elif args.sector:
        from skills.scripts.sector_analyzer import SectorAnalyzer
        sector_analyzer = SectorAnalyzer(analyzer)
        result = sector_analyzer.analyze_sector(args.sector, analysis_date=args.date)
        print(f"\n{'='*60}")
        print(f"板块: {args.sector}")
        print(f"{'='*60}")
        for r in result:
            analyzer.print_analysis(r)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
