# example.py
from backtest_engine import BacktestEngine
from strategy import BaseStrategy
import pandas as pd
import numpy as np

class VWAPStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.current_position = 0  # 记录当前持仓方向
        self.daily_data = []  # 存储当天的数据
        self.current_date = None
        self.current_vwap = None
        self.vwap_history = []  # 记录VWAP历史数据
        self.first_bar_of_day = True  # 标记每天的第一个bar
        
    def calculate_vwap(self):
        """计算当天的VWAP"""
        if not self.daily_data:
            return None
            
        df = pd.DataFrame(self.daily_data)
        vwap = (df['price'] * df['volume']).sum() / df['volume'].sum()
        return vwap
        
    def on_bar(self, timestamp, bar):
        current_time = pd.Timestamp(timestamp).time()
        current_date = pd.Timestamp(timestamp).date()
        signals = []
        
        # 收盘前平仓时间（14:55）
        close_time = pd.Timestamp('14:55:00').time()
        # 开始交易时间（9:31，即第一根K线结束）
        start_time = pd.Timestamp('09:31:00').time()
        
        # 处理新交易日
        if self.current_date != current_date:
            self.current_date = current_date
            self.daily_data = []
            self.first_bar_of_day = True
            self.current_position = 0  # 确保新的交易日从0仓位开始
        
        # 添加当前bar的数据用于计算VWAP
        self.daily_data.append({
            'price': (bar['high'] + bar['low'] + bar['close']) / 3,  # 使用典型价格
            'volume': bar['volume']
        })
        
        # 计算VWAP
        self.current_vwap = self.calculate_vwap()
        if self.current_vwap is not None:
            self.vwap_history.append({
                'timestamp': timestamp,
                'vwap': self.current_vwap
            })
        
        # 收盘前平仓
        if current_time >= close_time:
            if self.current_position != 0:
                volume = 1000000 / bar['close']
                signals.append({
                    'direction': -self.current_position,
                    'volume': volume,
                    'price': bar['close']
                })
                self.current_position = 0
            return signals
        
        # 跳过每天的第一根K线
        if self.first_bar_of_day:
            self.first_bar_of_day = False
            return signals
        
        # 只在交易时段内执行交易逻辑（9:31后）
        if current_time >= start_time and self.current_vwap is not None:
            price = bar['close']
            volume = 1000000 / price
            
            # 价格高于VWAP，做多
            if price > self.current_vwap:
                if self.current_position <= 0:  # 当前无仓位或持有空仓
                    # 如果有空仓，先平仓
                    if self.current_position < 0:
                        signals.append({
                            'direction': 1,
                            'volume': volume,
                            'price': price
                        })
                    # 开多仓
                    signals.append({
                        'direction': 1,
                        'volume': volume,
                        'price': price
                    })
                    self.current_position = 1
            
            # 价格低于VWAP，做空
            elif price < self.current_vwap:
                if self.current_position >= 0:  # 当前无仓位或持有多仓
                    # 如果有多仓，先平仓
                    if self.current_position > 0:
                        signals.append({
                            'direction': -1,
                            'volume': volume,
                            'price': price
                        })
                    # 开空仓
                    signals.append({
                        'direction': -1,
                        'volume': volume,
                        'price': price
                    })
                    self.current_position = -1
        
        return signals

# 运行回测
if __name__ == "__main__":
    engine = BacktestEngine(initial_capital=1000000, commission_rate=0.00005)
    strategy = VWAPStrategy()
    
    results = engine.run_backtest(
        strategy=strategy,
        symbol="IF",
        start_date="20241101",
        end_date="20241105"
    )