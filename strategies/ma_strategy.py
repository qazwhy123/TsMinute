from .base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class MAStrategy(BaseStrategy):
    def __init__(self, short_period=5, long_period=20):
        super().__init__()
        self.name = "MA Strategy"
        self.short_period = short_period
        self.long_period = long_period
        self.prices = []
        self.current_position = 0
        self.ma_history = []
        
    def calculate_ma(self, period):
        if len(self.prices) < period:
            return None
        return np.mean(self.prices[-period:])
        
    def on_bar(self, timestamp, bar):
        self.prices.append(bar['close'])
        
        # 计算并记录均线
        short_ma = self.calculate_ma(self.short_period)
        long_ma = self.calculate_ma(self.long_period)
        
        if short_ma is not None and long_ma is not None:
            self.ma_history.append({
                'timestamp': timestamp,
                'short_ma': short_ma,
                'long_ma': long_ma
            })
            
        signals = []
        
        # 计算短期和长期均线
        short_ma = self.calculate_ma(self.short_period)
        long_ma = self.calculate_ma(self.long_period)
        
        if short_ma is None or long_ma is None:
            return signals
            
        price = bar['close']
        volume = 1000000 / price
        
        # 短均线上穿长均线，做多
        if short_ma > long_ma and self.current_position <= 0:
            if self.current_position < 0:  # 平空仓
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
            
        # 短均线下穿长均线，做空
        elif short_ma < long_ma and self.current_position >= 0:
            if self.current_position > 0:  # 平多仓
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
    
    def get_indicator_data(self):
        if not self.ma_history:
            return None
        return [
            {
                'name': f'MA{self.short_period}',
                'data': self.ma_history,
                'value_key': 'short_ma',
                'color': 'red',
                'alpha': 0.8
            },
            {
                'name': f'MA{self.long_period}',
                'data': self.ma_history,
                'value_key': 'long_ma',
                'color': 'blue',
                'alpha': 0.8
            }
        ]