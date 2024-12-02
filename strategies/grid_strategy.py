from .base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class GridStrategy(BaseStrategy):
    def __init__(self, grid_num=10, price_range_ratio=0.02):
        """
        网格交易策略
        
        Parameters:
        -----------
        grid_num: int
            网格数量
        price_range_ratio: float
            价格区间比例（相对于初始价格的上下浮动比例）
        """
        super().__init__()
        self.name = "Grid Strategy"
        self.grid_num = grid_num
        self.price_range_ratio = price_range_ratio
        self.grids = None
        self.init_price = None
        self.grid_positions = {}  # 记录每个网格的持仓状态
        self.grid_history = []    # 记录网格线历史数据
        
    def initialize_grids(self, price):
        """初始化网格"""
        self.init_price = price
        price_range = price * self.price_range_ratio
        
        # 计算网格价格
        self.grids = np.linspace(
            price - price_range,
            price + price_range,
            self.grid_num
        )
        
        # 初始化网格持仓状态
        for grid_price in self.grids:
            self.grid_positions[grid_price] = 0
            
        # 记录网格线
        self.grid_history.append({
            'timestamp': pd.Timestamp.now(),
            'grids': self.grids.copy()
        })
        
    def get_grid_signals(self, price):
        """获取网格交易信号"""
        if self.grids is None:
            return []
            
        signals = []
        volume = self.calculate_position_volume(price)
        
        # 检查是否触及网格线
        for grid_price in self.grids:
            # 价格上穿网格线，做空
            if self.last_price < grid_price <= price and self.grid_positions[grid_price] >= 0:
                signals.append({
                    'direction': -1,
                    'volume': volume,
                    'price': price,
                    'grid_price': grid_price
                })
                self.grid_positions[grid_price] = -1
                
            # 价格下穿网格线，做多
            elif price <= grid_price < self.last_price and self.grid_positions[grid_price] <= 0:
                signals.append({
                    'direction': 1,
                    'volume': volume,
                    'price': price,
                    'grid_price': grid_price
                })
                self.grid_positions[grid_price] = 1
                
        return signals
        
    def on_bar(self, timestamp, bar):
        signals = []
        price = bar['close']
        
        # 初始化网格
        if self.init_price is None:
            self.initialize_grids(price)
            self.last_price = price
            return signals
            
        # 收盘前平仓
        if self.should_close_position(timestamp):
            # 平掉所有网格持仓
            for grid_price, position in self.grid_positions.items():
                if position != 0:
                    signals.append({
                        'direction': -position,
                        'volume': self.calculate_position_volume(price),
                        'price': price
                    })
                    self.grid_positions[grid_price] = 0
            return signals
            
        # 检查是否需要重新初始化网格
        if abs(price - self.init_price) / self.init_price > self.price_range_ratio:
            self.initialize_grids(price)
            
        # 获取网格交易信号
        if self.check_trading_time(timestamp):
            grid_signals = self.get_grid_signals(price)
            signals.extend(grid_signals)
            
        # 更新上一次价格
        self.last_price = price
        
        # 记录网格线
        if self.grids is not None:
            self.grid_history.append({
                'timestamp': timestamp,
                'grids': self.grids.copy()
            })
            
        return signals
        
    def get_indicator_data(self):
        """返回网格线数据用于图表展示"""
        if not self.grid_history:
            return None
            
        # 为每个网格线创建一个指标
        indicators = []
        for i, grid_price in enumerate(self.grids):
            grid_data = [{
                'timestamp': record['timestamp'],
                f'grid_{i}': record['grids'][i]
            } for record in self.grid_history]
            
            indicators.append({
                'name': f'Grid {i+1}',
                'data': grid_data,
                'value_key': f'grid_{i}',
                'color': 'gray',
                'alpha': 0.3
            })
            
        return indicators 