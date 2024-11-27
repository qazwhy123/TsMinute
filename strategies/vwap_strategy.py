from .base_strategy import BaseStrategy
import pandas as pd

class VWAPStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.name = "VWAP Strategy"
        self.daily_data = []
        self.current_date = None
        self.current_vwap = None
        self.vwap_history = []
        self.first_bar_of_day = True
        
    def calculate_vwap(self):
        if not self.daily_data:
            return None
        df = pd.DataFrame(self.daily_data)
        return (df['price'] * df['volume']).sum() / df['volume'].sum()
        
    def on_bar(self, timestamp, bar):
        current_date = pd.Timestamp(timestamp).date()
        signals = []
        
        # 处理新交易日
        if self.current_date != current_date:
            self.current_date = current_date
            self.daily_data = []
            self.first_bar_of_day = True
            self.current_position = 0
        
        # 收盘前平仓检查
        if self.should_close_position(timestamp):
            return self.generate_close_signals(bar)
        
        # 添加数据计算VWAP
        self.daily_data.append({
            'price': (bar['high'] + bar['low'] + bar['close']) / 3,
            'volume': bar['volume']
        })
        
        # 计算并记录VWAP
        self.current_vwap = self.calculate_vwap()
        if self.current_vwap is not None:
            self.vwap_history.append({
                'timestamp': timestamp,
                'vwap': self.current_vwap
            })
        
        # 跳过每天第一根K线
        if self.first_bar_of_day:
            self.first_bar_of_day = False
            return signals
        
        # 交易逻辑
        if self.check_trading_time(timestamp) and self.current_vwap is not None:
            price = bar['close']
            volume = self.calculate_position_volume(price)
            
            if price > self.current_vwap and self.current_position <= 0:
                signals.extend([
                    {'direction': 1, 'volume': volume} if self.current_position < 0 else None,
                    {'direction': 1, 'volume': volume}
                ])
                self.current_position = 1
                
            elif price < self.current_vwap and self.current_position >= 0:
                signals.extend([
                    {'direction': -1, 'volume': volume} if self.current_position > 0 else None,
                    {'direction': -1, 'volume': volume}
                ])
                self.current_position = -1
                
        return [s for s in signals if s is not None]
        
    def get_indicator_data(self):
        if not self.vwap_history:
            return None
        return {
            'name': 'VWAP',
            'data': self.vwap_history,
            'value_key': 'vwap',  # 数据中的值字段名
            'color': 'purple',
            'alpha': 0.8
        }