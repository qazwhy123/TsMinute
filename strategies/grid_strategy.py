from .base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class GridStrategy(BaseStrategy):
    def __init__(self, grid_num=10, price_range_ratio=0.02):
        super().__init__()
        self.name = "Grid Strategy"
        self.grid_num = grid_num
        self.price_range_ratio = price_range_ratio
        self.grids = None
        self.base_price = None  # 基准价格（每日开盘价）
        self.grid_positions = {}  # 记录每个网格的持仓状态
        self.grid_history = []    # 记录网格线历史数据
        self.current_date = None
        self.last_price = None
        self.target_position = 0.5  # 目标仓位比例
        
    def initialize_grids(self, price):
        """初始化网格"""
        self.base_price = price
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
        if self.grids is None or self.last_price is None:
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
        
    def adjust_to_target_position(self, price):
        """调整到目标仓位"""
        signals = []
        if self.current_position == 0:
            return signals
            
        # 计算目标仓位数量
        target_volume = self.calculate_position_volume(price) * self.target_position
        current_volume = abs(self.current_position) * self.calculate_position_volume(price)
        
        # 如果当前持仓方向与数量都正确，不需要调整
        if self.current_position > 0 and abs(current_volume - target_volume) < 0.0001:
            return signals
            
        # 先平掉当前仓位
        if self.current_position != 0:
            signals.append({
                'direction': -self.current_position,
                'volume': current_volume,
                'price': price,
                'type': 'position_adjust'
            })
            
        # 建立目标仓位（始终做多）
        signals.append({
            'direction': 1,
            'volume': target_volume,
            'price': price,
            'type': 'position_adjust'
        })
        
        return signals
        
    def on_bar(self, timestamp, bar):
        signals = []
        current_date = pd.Timestamp(timestamp).date()
        price = bar['close']
        
        # 新的交易日
        if self.current_date != current_date:
            self.current_date = current_date
            # 使用开盘价初始化网格
            self.initialize_grids(bar['open'])
            self.last_price = bar['open']
            
        # 收盘前调整仓位
        if self.should_close_position(timestamp):
            return self.adjust_to_target_position(price)
            
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