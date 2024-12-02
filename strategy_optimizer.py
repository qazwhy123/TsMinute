import pandas as pd
import numpy as np
from backtest_engine import BacktestEngine
from strategies.vwap_strategy import VWAPStrategy
from strategies.ma_strategy import MAStrategy
from strategies.grid_strategy import GridStrategy
from itertools import product
import time
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns

class StrategyOptimizer:
    def __init__(self, symbol, start_date, end_date, initial_capital=1000000, show_plots=False):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.results = []
        self.show_plots = show_plots
        
        # 策略注册表
        self.strategy_registry = {
            'VWAP': {
                'class': VWAPStrategy,
                'optimizer': self._optimize_vwap_strategy,
                'default_params': None
            },
            'MA': {
                'class': MAStrategy,
                'optimizer': self._optimize_ma_strategy,
                'default_params': {
                    'short_periods': [3, 5, 8, 10, 12, 15],
                    'long_periods': [10, 15, 20, 25, 30, 40]
                }
            },
            'Grid': {
                'class': GridStrategy,
                'optimizer': self._optimize_grid_strategy,
                'default_params': {
                    'grid_nums': [5, 8, 10, 12, 15, 20],
                    'price_range_ratios': [0.005, 0.01, 0.015, 0.02, 0.025, 0.03]
                }
            }
        }
        
        # 策略配置
        self.strategy_configs = {
            name: {'enabled': False, 'params': info['default_params']} 
            for name, info in self.strategy_registry.items()
        }
        
    def register_strategy(self, name, strategy_class, optimizer_func, default_params=None):
        """注册新策略"""
        self.strategy_registry[name] = {
            'class': strategy_class,
            'optimizer': optimizer_func,
            'default_params': default_params
        }
        self.strategy_configs[name] = {
            'enabled': False,
            'params': default_params
        }
        
    def set_strategy_config(self, strategy_name, enabled=False, params=None):
        """设置策略配置"""
        if strategy_name not in self.strategy_configs:
            raise ValueError(f"未知策略: {strategy_name}")
            
        self.strategy_configs[strategy_name]['enabled'] = enabled
        if params is not None:
            self.strategy_configs[strategy_name]['params'] = params
            
    def run_single_test(self, strategy, params=None):
        """运行单次回测"""
        engine = BacktestEngine(initial_capital=self.initial_capital, commission_rate=0.00005)
        results = engine.run_backtest(
            strategy=strategy,
            symbol=self.symbol,
            start_date=self.start_date,
            end_date=self.end_date,
            show_plots=False
        )
        
        summary = {
            '策略名称': strategy.name,
            '参数': str(params) if params else 'default',
            '总收益率': results['总收益率'],
            '费前收益': results['费前收益'],
            '费后收益': results['费后收益'],
            '总手续费': results['总手续费'],
            '换手率': results['换手率'],
            '交易次数': results['交易次数'],
            '日均交易次数': results['交易次数'] / 5,
            '单笔收益': results['费后收益'] / results['交易次数'] if results['交易次数'] > 0 else 0
        }
        self.results.append(summary)
        return results
        
    def _optimize_vwap_strategy(self):
        """VWAP策略优化"""
        strategy = VWAPStrategy()
        self.run_single_test(strategy)
        
    def _optimize_ma_strategy(self):
        """MA策略优化"""
        params = self.strategy_configs['MA']['params']
        short_periods = params['short_periods']
        long_periods = params['long_periods']
        
        print(f"MA策略参数组合数: {len(short_periods) * len(long_periods)}")
        
        for short_period, long_period in product(short_periods, long_periods):
            if short_period >= long_period:
                continue
                
            strategy_params = {'short_period': short_period, 'long_period': long_period}
            strategy = MAStrategy(short_period=short_period, long_period=long_period)
            strategy.name = f"MA({short_period},{long_period})"
            self.run_single_test(strategy, strategy_params)
            
    def _optimize_grid_strategy(self):
        """网格策略优化"""
        params = self.strategy_configs['Grid']['params']
        grid_nums = params['grid_nums']
        price_range_ratios = params['price_range_ratios']
        
        print(f"网格策略参数组合数: {len(grid_nums) * len(price_range_ratios)}")
        
        for grid_num, ratio in product(grid_nums, price_range_ratios):
            strategy_params = {'grid_num': grid_num, 'price_range_ratio': ratio}
            strategy = GridStrategy(grid_num=grid_num, price_range_ratio=ratio)
            strategy.name = f"Grid({grid_num},{ratio:.3f})"
            self.run_single_test(strategy, strategy_params)
            
    def run_all_tests(self):
        """运行所有启用的策略测试"""
        print("\n=== 开始策略测试 ===")
        start_time = time.time()
        
        # 运行所有启用的策略
        for strategy_name, config in self.strategy_configs.items():
            if config['enabled']:
                print(f"\n测试 {strategy_name} 策略...")
                optimizer_func = self.strategy_registry[strategy_name]['optimizer']
                optimizer_func()
        
        print(f"\n策略测试完成! 总耗时: {time.time() - start_time:.2f}秒")
        
    def plot_parameter_heatmap(self, strategy_type, save_fig=False):
        """绘制参数热力图"""
        results_df = pd.DataFrame(self.results)
        
        # 检查是否有该策略的数据
        strategy_results = results_df[results_df['策略名称'].str.startswith(strategy_type)]
        if strategy_results.empty:
            print(f"没有{strategy_type}策略的测试数据，跳过绘图")
            return
        
        if strategy_type == 'MA':
            # 提取MA策略的参数
            params = strategy_results['参数'].apply(eval)
            
            # 创建热力图数据
            heatmap_data = pd.pivot_table(
                strategy_results,
                values='总收益率',
                index=params.apply(lambda x: x['short_period']),
                columns=params.apply(lambda x: x['long_period'])
            )
            
            plt.figure(figsize=(10, 8))
            sns.heatmap(heatmap_data, annot=True, fmt='.2%', cmap='RdYlGn')
            plt.title('MA策略参数优化热力图')
            plt.xlabel('长期均线周期')
            plt.ylabel('短期均线周期')
            
            if save_fig:
                plt.savefig(f'MA_heatmap_{self.start_date}_{self.end_date}.png')
            
        elif strategy_type == 'Grid':
            # 提取网格策略的参数
            params = strategy_results['参数'].apply(eval)
            
            # 创建热力图数据
            heatmap_data = pd.pivot_table(
                strategy_results,
                values='总收益率',
                index=params.apply(lambda x: x['grid_num']),
                columns=params.apply(lambda x: x['price_range_ratio'])
            )
            
            plt.figure(figsize=(10, 8))
            sns.heatmap(heatmap_data, annot=True, fmt='.2%', cmap='RdYlGn')
            plt.title('网格策略参数优化热力图')
            plt.xlabel('价格区间比例')
            plt.ylabel('网格数量')
            
            if save_fig:
                plt.savefig(f'Grid_heatmap_{self.start_date}_{self.end_date}.png')
            
        if self.show_plots:
            plt.show()
        else:
            plt.close()
        
    def print_results(self, top_n=10, save_plots=False):
        """打印测试结果"""
        if not self.results:
            print("没有测试结果!")
            return
            
        results_df = pd.DataFrame(self.results)
        
        # 按策略类型分组统计
        strategy_stats = results_df.groupby(results_df['策略名称'].str.split('(').str[0]).agg({
            '总收益率': ['mean', 'max', 'min', 'std'],
            '交易次数': 'mean',
            '单笔收益': 'mean'
        }).round(4)
        
        print("\n=== 策略类型统计 ===")
        print(strategy_stats)
        
        # 打印每种策略的最优参数组合
        print("\n=== 各策略最优参数 ===")
        for strategy_type in ['MA', 'Grid', 'VWAP']:
            strategy_results = results_df[results_df['策略名称'].str.startswith(strategy_type)]
            if not strategy_results.empty:
                best_result = strategy_results.loc[strategy_results['总收益率'].idxmax()]
                print(f"\n{strategy_type}策略最优结果:")
                for key, value in best_result.items():
                    if isinstance(value, float):
                        print(f"{key}: {value:.4f}")
                    else:
                        print(f"{key}: {value}")
        
        # 根据设置决定是否显示或保存图表
        if self.show_plots or save_plots:
            # 只为有数据的策略绘制热力图
            for strategy_type in ['MA', 'Grid']:
                if results_df[results_df['策略名称'].str.startswith(strategy_type)].empty:
                    continue
                self.plot_parameter_heatmap(strategy_type, save_fig=save_plots)

if __name__ == "__main__":
    # 测试参数
    symbol = "IF"
    start_date = "20230101"
    end_date = "20241105"
    
    # 创建优化器，设置不显示图表
    optimizer = StrategyOptimizer(
        symbol, 
        start_date, 
        end_date, 
        show_plots=False  # 不显示图表
    )
    
    # 配置策略
    optimizer.set_strategy_config('Grid', enabled=True, params={
        'grid_nums': [3, 5, 8, 10],
        'price_range_ratios': [0.002, 0.003,0.005, 0.01, 0.015, 0.02, 0.025, 0.03]
    })
    optimizer.set_strategy_config('MA', enabled=False)
    optimizer.set_strategy_config('VWAP', enabled=False)
    
    # 运行测试
    optimizer.run_all_tests()
    
    # 保存结果和图表，但不显示
    optimizer.print_results(save_plots=True) 