from data_loader import MinuteDataLoader
from dominant_contract import DominantContractLoader
import pandas as pd
import numpy as np
from tabulate import tabulate
from visualizer import BacktestVisualizer
import matplotlib.pyplot as plt

class BacktestEngine:
    def __init__(self, initial_capital=1000000, commission_rate=0.0003):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}  # 当前持仓 {symbol: position}
        self.trades = []     # 交易记录
        self.data_loader = MinuteDataLoader()
        self.dominant_loader = DominantContractLoader()
        self.data = None
        self.commission_rate = commission_rate  # 手续费率
        
    def print_results(self, results):
        """格式化打印回测结果"""
        # 基础指标表格
        basic_metrics = [
            ['初始资金', f"{results['初始资金']:,.2f}"],
            ['结束资金', f"{results['结束资金']:,.2f}"],
            ['总收益率', f"{results['总收益率']:.2%}"],
            ['费前收益', f"{results['费前收益']:,.2f}"],
            ['总手续费', f"{results['总手续费']:,.2f}"],
            ['费后收益', f"{results['费后收益']:,.2f}"],
            ['换手率', f"{results['换手率']:.2%}"],
            ['交易次数', results['交易次数']],
            ['合约切换次数', results['合约切换次数']]
        ]
        
        print("\n=== 回测结果汇总 ===")
        print(tabulate(basic_metrics, headers=['指标', '数值'], tablefmt='grid'))
        
        # 合约切换记录表格
        if results['合约切换记录']:
            switch_records = [[
                switch['切换时间'],
                switch['旧合约'],
                switch['新合约']
            ] for switch in results['合约切换记录']]
            
            print("\n=== 合约切换记录 ===")
            print(tabulate(switch_records, 
                         headers=['切换时间', '旧合约', '新合约'],
                         tablefmt='grid'))
        
    def _calculate_pnl(self):
        """计算每个时间点的PNL和净值"""
        # 创建时间序列数据框
        df = pd.DataFrame(index=self.data.index)
        df['close'] = self.data['close']
        df['position'] = 0
        df['position_value'] = 0
        df['cash'] = self.initial_capital
        df['commission'] = 0
        
        # 遍历所有交易，更新持仓和现金
        trades_df = pd.DataFrame(self.trades)
        if trades_df.empty:
            return df
        
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
        trades_df = trades_df.set_index('timestamp')
        
        # 初始化当前持仓
        current_position = 0
        current_cash = self.initial_capital
        
        for timestamp in df.index:
            # 更新当日交易
            if timestamp in trades_df.index:
                day_trades = trades_df.loc[timestamp]
                if isinstance(day_trades, pd.Series):
                    day_trades = pd.DataFrame([day_trades])
                
                for _, trade in day_trades.iterrows():
                    # 更新持仓
                    current_position += trade['direction'] * trade['volume']
                    # 更新现金
                    current_cash -= trade['direction'] * trade['cost'] + trade['commission']
                    # 记录手续费
                    df.loc[timestamp, 'commission'] += trade['commission']
            
            # 更新当前状态
            df.loc[timestamp, 'position'] = current_position
            df.loc[timestamp, 'cash'] = current_cash
            
            # 计算持仓市值
            df.loc[timestamp, 'position_value'] = current_position * df.loc[timestamp, 'close']
        
        # 计算总资产和收益
        df['total_value'] = df['cash'] + df['position_value']
        df['pnl'] = df['total_value'] - self.initial_capital
        df['net_value'] = df['total_value'] / self.initial_capital
        
        return df
    
    def run_backtest(self, strategy, symbol, start_date, end_date, show_plots=True):
        """
        运行回测
        
        Parameters:
        -----------
        strategy: Strategy
            策略类实例
        symbol: str
            期货品种代码（如'IF'）或具体合约代码（如'IF2309'）
        start_date: str
            开始日期 'YYYYMMDD'
        end_date: str
            结束日期 'YYYYMMDD'
        show_plots: bool
            是否显示图表
        """
        # 判断是否是品种代码（主力合约）
        is_dominant = len(symbol) <= 2 or symbol.isalpha()
        
        if is_dominant:
            # 加载主力合约数据
            self.data = self.dominant_loader.load_dominant_data(symbol, start_date, end_date)
            current_contract = None
        else:
            # 加载单个合约数据
            self.data = self.data_loader.load_future_data(symbol, start_date, end_date)
            self.data['symbol'] = symbol  # 添加合约列
            
        # 回测主循环
        for i, (timestamp, bar) in enumerate(self.data.iterrows()):
            # 如果合约发生变化，需要处理持仓转移
            if is_dominant and (current_contract != bar['symbol']):
                if current_contract is not None:
                    self._handle_contract_switch(current_contract, bar['symbol'], bar)
                current_contract = bar['symbol']
            
            # 更新策略
            signals = strategy.on_bar(timestamp, bar)
            
            # 处理交易信号
            if signals:
                # 获取下一个bar的开盘价（如果存在）
                next_open = None
                if i + 1 < len(self.data):
                    next_open = self.data.iloc[i + 1]['open']
                
                self._process_signals(signals, bar['symbol'], bar, next_open)
                
        # 计算回测结果
        self.pnl_df = self._calculate_pnl()
        results = self._calculate_results()
        self.print_results(results)
        
        # 绘制图表
        if self.trades:
            visualizer = BacktestVisualizer(
                self.trades, 
                self.data, 
                self.pnl_df, 
                strategy
            )
            visualizer.plot_trades_and_indicators()
            visualizer.plot_pnl_curve()
            
            if show_plots:
                plt.show()
            else:
                plt.close('all')
            
        return results
    
    def _handle_contract_switch(self, old_contract, new_contract, bar):
        """处理主力合约切换"""
        if old_contract in self.positions and self.positions[old_contract] != 0:
            # 记录平仓旧合约
            close_trade = {
                'timestamp': bar.name,
                'symbol': old_contract,
                'direction': -np.sign(self.positions[old_contract]),
                'price': bar['close'],
                'volume': abs(self.positions[old_contract]),
                'cost': bar['close'] * abs(self.positions[old_contract]),
                'type': 'switch_close',
                'commission': bar['close'] * abs(self.positions[old_contract]) * self.commission_rate
            }
            self.trades.append(close_trade)
            
            # 记录开仓新合约
            open_trade = {
                'timestamp': bar.name,
                'symbol': new_contract,
                'direction': np.sign(self.positions[old_contract]),
                'price': bar['close'],
                'volume': abs(self.positions[old_contract]),
                'cost': bar['close'] * abs(self.positions[old_contract]),
                'type': 'switch_open',
                'commission': bar['close'] * abs(self.positions[old_contract]) * self.commission_rate
            }
            self.trades.append(open_trade)
            
            # 持仓
            self.positions[new_contract] = self.positions[old_contract]
            self.positions[old_contract] = 0
    
    def _process_signals(self, signals, symbol, bar, next_open):
        """处理交易信号"""
        for signal in signals:
            direction = signal['direction']
            volume = signal['volume']
            
            # 使用下一个bar的开盘价，如果没有下一个bar则使用当前bar的收盘价
            price = next_open if next_open is not None else bar['close']
            
            # 根据当前资金调整交易量
            if direction == 1:  # 买入
                volume = min(volume, self.current_capital / price)
            
            # 计算手续费
            commission = price * volume * self.commission_rate
            
            # 记录交易
            trade = {
                'timestamp': bar.name,
                'symbol': symbol,
                'direction': direction,
                'price': price,
                'volume': volume,
                'cost': price * volume,
                'type': 'trade',
                'commission': commission,
                'initial_capital': self.initial_capital
            }
            self.trades.append(trade)
            
            # 更新持仓和资金
            if symbol not in self.positions:
                self.positions[symbol] = 0
            self.positions[symbol] += direction * volume
            self.current_capital -= direction * price * volume + commission
    
    def _calculate_results(self):
        """计算回测结果统计"""
        trades_df = pd.DataFrame(self.trades)
        
        # 使用pnl_df中的结果
        final_pnl = self.pnl_df['pnl'].iloc[-1]
        total_commission = self.pnl_df['commission'].sum()
        
        # 计算换手率
        total_trade_value = trades_df['cost'].sum()
        avg_capital = self.pnl_df['total_value'].mean()
        turnover_rate = total_trade_value / avg_capital
        
        # 获取合约切换信息
        switch_trades = trades_df[trades_df['type'] == 'switch_close']
        contract_switches = []
        for _, trade in switch_trades.iterrows():
            contract_switches.append({
                '切换时间': trade['timestamp'],
                '旧合约': trade['symbol'],
                '新合约': trades_df.loc[trades_df.index[trades_df.index.get_loc(trade.name) + 1], 'symbol']
            })
        
        # 按交易类型分类统计
        normal_trades = trades_df[trades_df['type'] == 'trade']
        switch_trades = trades_df[trades_df['type'].isin(['switch_close', 'switch_open'])]
        
        results = {
            '初始资金': self.initial_capital,
            '结束资金': self.pnl_df['total_value'].iloc[-1],
            '总收益率': self.pnl_df['net_value'].iloc[-1] - 1,
            '费前收益': final_pnl + total_commission,
            '总手续费': total_commission,
            '费后收益': final_pnl,
            '换手率': turnover_rate,
            '交易次数': len(normal_trades),
            '合约切换次数': len(switch_trades) // 2,
            '合约切换记录': contract_switches
        }
        
        return results 