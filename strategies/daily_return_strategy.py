from .base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class DailyReturnStrategy(BaseStrategy):
    def __init__(self, return_threshold=0.02, entry_time='14:50:00'):
        """
        基于日内涨幅的策略
        
        Parameters:
        -----------
        return_threshold: float
            涨跌幅阈值，默认2%
        entry_time: str
            入场时间，默认14:50
        """
        super().__init__()
        self.name = "Daily Return Strategy"
        self.return_threshold = return_threshold
        self.entry_time = pd.Timestamp(entry_time).time()
        self.current_date = None
        self.daily_open = None
        self.position_taken = False  # 标记当天是否已经判断过
        self.return_history = []
        
    def calculate_daily_return(self, current_price):
        """计算日内涨跌幅"""
        if self.daily_open is None:
            return 0
        return (current_price - self.daily_open) / self.daily_open
        
    def on_bar(self, timestamp, bar):
        signals = []
        current_date = pd.Timestamp(timestamp).date()
        current_time = pd.Timestamp(timestamp).time()
        
        # 新的交易日
        if self.current_date != current_date:
            self.current_date = current_date
            self.daily_open = bar['open']
            self.position_taken = False
            
        # 记录涨跌幅
        daily_return = self.calculate_daily_return(bar['close'])
        self.return_history.append({
            'timestamp': timestamp,
            'daily_return': daily_return
        })
        
        # 在指定时间判断仓位
        if current_time >= self.entry_time and not self.position_taken:
            volume = self.calculate_position_volume(bar['close'])
            daily_return = self.calculate_daily_return(bar['close'])
            
            # 先平掉现有仓位
            if self.current_position != 0:
                signals.append({
                    'direction': -self.current_position,
                    'volume': volume,
                    'price': bar['close'],
                    'type': 'close'
                })
            
            # 根据涨跌幅决定新仓位
            if daily_return > self.return_threshold:
                # 做空
                signals.append({
                    'direction': -1,
                    'volume': volume,
                    'price': bar['close'],
                    'type': 'open',
                    'return': daily_return
                })
                self.current_position = -1
                
            elif daily_return < -self.return_threshold:
                # 做多
                signals.append({
                    'direction': 1,
                    'volume': volume,
                    'price': bar['close'],
                    'type': 'open',
                    'return': daily_return
                })
                self.current_position = 1
                
            else:
                # 涨跌幅在阈值范围内，空仓
                self.current_position = 0
                
            self.position_taken = True
            
        return signals
        
    def get_indicator_data(self):
        """返回涨跌幅数据用于图表展示"""
        if not self.return_history:
            return None
            
        # 添加阈值线
        threshold_data = [{
            'timestamp': record['timestamp'],
            'upper_threshold': self.return_threshold,
            'lower_threshold': -self.return_threshold
        } for record in self.return_history]
        
        return [
            {
                'name': 'Daily Return',
                'data': self.return_history,
                'value_key': 'daily_return',
                'color': 'orange',
                'alpha': 0.6
            },
            {
                'name': f'Upper Threshold ({self.return_threshold:.1%})',
                'data': threshold_data,
                'value_key': 'upper_threshold',
                'color': 'red',
                'alpha': 0.3
            },
            {
                'name': f'Lower Threshold ({-self.return_threshold:.1%})',
                'data': threshold_data,
                'value_key': 'lower_threshold',
                'color': 'green',
                'alpha': 0.3
            }
        ] 