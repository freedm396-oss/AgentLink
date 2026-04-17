# earnings-surprise-strategy/skills/scripts/earnings_scanner.py

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os
import yaml
import warnings
warnings.filterwarnings('ignore')

try:
    from .data_fetcher import EarningsDataFetcher
    from .surprise_analyzer import SurpriseAnalyzer
    from .quality_analyzer import QualityAnalyzer
    from .market_analyzer import MarketReactionAnalyzer
    from .risk_assessor import RiskAssessor
    from .report_generator import EarningsReportGenerator
except ImportError:
    import os
import sys
    import os
    
    from data_fetcher import EarningsDataFetcher
    from surprise_analyzer import SurpriseAnalyzer
    from quality_analyzer import QualityAnalyzer
    from market_analyzer import MarketReactionAnalyzer
    from risk_assessor import RiskAssessor
    from report_generator import EarningsReportGenerator


class EarningsSurpriseScanner:
    """财报超预期扫描器"""
    
    def __init__(self):
        self.name = "财报超预期策略"
        self.data_fetcher = EarningsDataFetcher()
        self.surprise_analyzer = SurpriseAnalyzer()
        self.quality_analyzer = QualityAnalyzer()
        self.market_analyzer = MarketReactionAnalyzer()
        self.risk_assessor = RiskAssessor()
        self.report_generator = EarningsReportGenerator()
        
        # 评分权重
        self.weights = {
            'surprise_magnitude': 0.30,
            'growth_quality': 0.25,
            'market_reaction': 0.20,
            'institutional_attitude': 0.15,
            'industry_prosperity': 0.10
        }

    def _load_watchlist(self):
        """加载自选股池"""
        path = os.path.join(_BASE_DIR, 'my_stock_pool', 'watchlist.yaml')
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data.get('watchlist', {})

    def scan_watchlist(self, sector: str = None, top_n: int = 10) -> List[Dict]:
        """扫描自选股池中有财报超预期的股票"""
        watchlist = self._load_watchlist()
        if not watchlist:
            print("❌ 无法加载自选股池 watchlist.yaml")
            return []

        if sector:
            sectors_to_scan = {sector: watchlist.get(sector, {'core': [], 'focus': []})}
        else:
            sectors_to_scan = watchlist

        print(f"📋 开始扫描自选股池{'(' + sector + ')' if sector else ''}的财报...")
        total_core = sum(len(d['core']) for d in sectors_to_scan.values())
        total_focus = sum(len(d['focus']) for d in sectors_to_scan.values())
        print(f"   core 标的: {total_core}只 | focus 标的: {total_focus}只")
        print("-" * 60)

        # 获取最近一个财报季
        now = datetime.now()
        if now.month <= 4:
            quarter = f"{now.year-1}Q4"
        elif now.month <= 8:
            quarter = f"{now.year}Q1"
        else:
            quarter = f"{now.year}Q2"

        results = []
        stock_count = 0
        for sector_name, data in sectors_to_scan.items():
            all_stocks = data.get('core', []) + data.get('focus', [])
            tag = '⭐' if data.get('core') else '○'
            for name, code in all_stocks:
                stock_count += 1
                if stock_count % 20 == 0:
                    print(f"  进度: {stock_count}只已扫描...")
                try:
                    earnings = self.data_fetcher.get_earnings_by_stock(code, quarter)
                    if not earnings:
                        # 尝试上一季
                        earnings = self.data_fetcher.get_earnings_by_stock(code)
                    if earnings:
                        result = self.analyze_earnings(earnings)
                        if result and result['score'] >= 70:
                            result['sector'] = sector_name
                            result['is_core'] = (name, code) in data.get('core', [])
                            results.append(result)
                            print(f"  ✅ [{tag}{sector_name}] {name}({code}): {result['score']}分")
                except Exception:
                    pass

        results.sort(key=lambda x: x['score'], reverse=True)
        print(f"\n扫描完成，共发现 {len(results)} 只有超预期信号的股票")
        return results[:top_n]
        
    def scan_daily_earnings(self, date: str = None) -> List[Dict]:
        """扫描每日发布的财报"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"开始扫描{date}发布的财报...")
        
        # 获取当日发布的财报
        earnings_list = self.data_fetcher.get_earnings_by_date(date)
        
        if not earnings_list:
            print(f"{date}无财报发布")
            return []
        
        print(f"找到{len(earnings_list)}份财报")
        
        results = []
        for earnings in earnings_list:
            result = self.analyze_earnings(earnings)
            if result and result['score'] >= 70:
                results.append(result)
        
        # 按得分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"发现{len(results)}只符合条件的股票")
        return results
    
    def scan_earnings_season(self, start_date: str, end_date: str) -> List[Dict]:
        """扫描财报季所有财报"""
        print(f"扫描财报季 {start_date} 至 {end_date}")
        
        # 获取日期范围内的所有财报
        earnings_list = self.data_fetcher.get_earnings_in_range(start_date, end_date)
        
        results = []
        for earnings in earnings_list:
            result = self.analyze_earnings(earnings)
            if result and result['score'] >= 70:
                results.append(result)
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    
    def analyze_earnings(self, earnings: Dict) -> Optional[Dict]:
        """分析单份财报"""
        try:
            stock_code = earnings.get('stock_code')
            stock_name = earnings.get('stock_name')
            quarter = earnings.get('quarter')
            
            # 1. 超预期幅度分析
            surprise_analysis = self.surprise_analyzer.analyze(earnings)
            if surprise_analysis['score'] < 60:
                return None  # 超预期不明显
            
            # 2. 增长质量分析
            quality_analysis = self.quality_analyzer.analyze(stock_code, earnings)
            
            # 3. 市场反应分析
            market_analysis = self.market_analyzer.analyze(stock_code, earnings)
            
            # 4. 机构态度分析
            institutional_analysis = self._analyze_institutional_attitude(stock_code)
            
            # 5. 行业景气度分析
            industry_analysis = self._analyze_industry(earnings.get('industry', ''))
            
            # 计算总分
            total_score = self._calculate_total_score(
                surprise_analysis,
                quality_analysis,
                market_analysis,
                institutional_analysis,
                industry_analysis
            )
            
            # 生成交易建议
            recommendation = self._generate_recommendation(
                total_score,
                surprise_analysis,
                market_analysis
            )
            
            # 风险评估
            risks = self.risk_assessor.assess(
                stock_code,
                earnings,
                market_analysis
            )
            
            return {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'quarter': quarter,
                'announcement_date': earnings.get('announcement_date'),
                'signal': 'BUY' if total_score >= 75 else 'WATCH',
                'score': round(total_score, 2),
                'surprise_analysis': surprise_analysis,
                'quality_analysis': quality_analysis,
                'market_analysis': market_analysis,
                'institutional_analysis': institutional_analysis,
                'industry_analysis': industry_analysis,
                'recommendation': recommendation,
                'risks': risks,
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"分析{earnings.get('stock_code')}失败: {e}")
            return None
    
    def _analyze_institutional_attitude(self, stock_code: str) -> Dict:
        """分析机构态度"""
        try:
            # 获取分析师评级
            ratings = self.data_fetcher.get_analyst_ratings(stock_code)
            
            if not ratings:
                return {'score': 60, 'level': '数据不足'}
            
            # 评级变化
            recent_ratings = ratings[:5]
            upgrades = sum(1 for r in recent_ratings if r.get('change') == '上调')
            downgrades = sum(1 for r in recent_ratings if r.get('change') == '下调')
            
            if upgrades > downgrades:
                score = 85
                level = "机构看好"
            elif upgrades == downgrades:
                score = 70
                level = "机构中性"
            else:
                score = 50
                level = "机构谨慎"
            
            # 目标价空间
            target_price = self.data_fetcher.get_target_price(stock_code)
            current_price = self.data_fetcher.get_current_price(stock_code)
            
            if target_price and current_price:
                upside = (target_price - current_price) / current_price * 100
                if upside > 20:
                    score = min(100, score + 10)
                    level += "，目标价空间大"
            
            return {
                'score': score,
                'level': level,
                'upgrades': upgrades,
                'downgrades': downgrades,
                'target_upside': upside if target_price else None
            }
            
        except Exception as e:
            return {'score': 60, 'level': '无法获取', 'error': str(e)}
    
    def _analyze_industry(self, industry: str) -> Dict:
        """分析行业景气度"""
        try:
            if not industry:
                return {'score': 70, 'level': '未知'}
            
            # 获取行业指数表现
            industry_performance = self.data_fetcher.get_industry_performance(industry)
            
            if industry_performance:
                if industry_performance > 20:
                    score = 100
                    level = "高景气"
                elif industry_performance > 10:
                    score = 85
                    level = "中高景气"
                elif industry_performance > 0:
                    score = 70
                    level = "温和增长"
                else:
                    score = 40
                    level = "景气下行"
            else:
                score = 70
                level = "行业数据不足"
            
            return {'score': score, 'level': level, 'performance': industry_performance}
            
        except Exception as e:
            return {'score': 70, 'level': '无法评估', 'error': str(e)}
    
    def _calculate_total_score(self, surprise: Dict, quality: Dict,
                               market: Dict, institutional: Dict,
                               industry: Dict) -> float:
        """计算总分"""
        total = (
            surprise['score'] * self.weights['surprise_magnitude'] +
            quality['score'] * self.weights['growth_quality'] +
            market['score'] * self.weights['market_reaction'] +
            institutional['score'] * self.weights['institutional_attitude'] +
            industry['score'] * self.weights['industry_prosperity']
        )
        return total
    
    def _generate_recommendation(self, score: float, 
                                  surprise: Dict,
                                  market: Dict) -> Dict:
        """生成交易建议"""
        if score >= 85:
            action = "强烈推荐"
            urgency = "公告后1-2日内买入"
            entry = "公告次日开盘买入"
            position = "25%"
        elif score >= 75:
            action = "推荐"
            urgency = "公告后3-5日内择机买入"
            entry = "回调至5日线买入"
            position = "15%"
        elif score >= 70:
            action = "关注"
            urgency = "等待确认信号"
            entry = "突破公告日高点买入"
            position = "10%"
        else:
            action = "暂缓"
            urgency = "条件不充分"
            entry = "继续观察"
            position = "0%"
        
        return {
            'action': action,
            'urgency': urgency,
            'entry_method': entry,
            'suggested_position': position,
            'stop_loss': '-8%或跌破公告日最低价',
            'target': '15-25%',
            'holding_period': '2-4周'
        }


def main():
    """命令行入口"""

    # ── 路径设置（相对路径，基于脚本所在目录）────────────────────
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    _SKILL_DIR = os.path.dirname(_SCRIPT_DIR)
    _SKILL_ROOT = os.path.dirname(_SKILL_DIR)
    _BASE_DIR = os.path.dirname(_SKILL_ROOT)

    if _SKILL_ROOT not in sys.path:
        sys.path.insert(0, _SKILL_ROOT)
    if _SCRIPT_DIR not in sys.path:
        sys.path.insert(0, _SCRIPT_DIR)

    import argparse
    
    parser = argparse.ArgumentParser(description='财报超预期策略扫描')
    parser.add_argument('--scan', action='store_true', help='扫描今日财报')
    parser.add_argument('--date', type=str, help='指定日期 YYYY-MM-DD')
    parser.add_argument('--stock', type=str, help='分析指定股票')
    parser.add_argument('--name', type=str, help='股票名称')
    parser.add_argument('--quarter', type=str, help='财报季度 e.g., 2024Q1')
    parser.add_argument('--top', type=int, default=10, help='返回前N名')
    parser.add_argument('--pool', type=str, default=None, const='all', nargs='?',
                       help='扫描自选股池（my_stock_pool），可选：板块名或 all（全部）')
    parser.add_argument('--list-pools', action='store_true', help='列出所有自选股池板块')
    
    args = parser.parse_args()
    
    scanner = EarningsSurpriseScanner()
    
    if args.list_pools:
        watchlist = scanner._load_watchlist()
        if watchlist:
            print("📋 自选股池板块列表：")
            for s, d in watchlist.items():
                print(f"   {s}: core={len(d.get('core',[]))}, focus={len(d.get('focus',[]))}")
        else:
            print("❌ 无法加载自选股池")

    elif args.pool is not None:
        sector = args.pool if args.pool != 'all' else None
        results = scanner.scan_watchlist(sector=sector, top_n=args.top)
        report = scanner.report_generator.generate_scan_report(results, args.top)
        print(report)

    elif args.scan:
        date = args.date or datetime.now().strftime('%Y-%m-%d')
        results = scanner.scan_daily_earnings(date)
        
        report = scanner.report_generator.generate_scan_report(results, args.top)
        print(report)
        
    elif args.stock:
        # 分析指定股票
        earnings = scanner.data_fetcher.get_earnings_by_stock(
            args.stock, args.quarter
        )
        if earnings:
            result = scanner.analyze_earnings(earnings)
            report = scanner.report_generator.generate_stock_report(result)
            print(report)
        else:
            print(f"未找到{args.stock}的财报数据")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()