import pandas as pd

class BaseStrategy:
    def __init__(self):
        self.name = "BaseStrategy"
        self.positions = {}  # 记录当前持仓 {symbol: position}
        self.current_position = 0  # 当前持仓方向
        self.trading_times = {
            'start_time': pd.Timestamp('09:31:00').time(),  # 开始交易时间
            'close_time': pd.Timestamp('14:55:00').time()   # 收盘平仓时间
        }
        self.indicator_history = []  # 存储策略指标历史数据
        
    def on_bar(self, timestamp, bar):
        """
        处理每个K线数据
        
        Parameters:
        -----------
        timestamp: datetime
            当前K线的时间戳
        bar: pd.Series
            当前K线数据，包含 ['open', 'high', 'low', 'close', 'volume'] 等字段
            
        Returns:
        --------
        list: 交易信号列表，每个信号为字典格式：
            {
                'direction': int,  # 1买入，-1卖出
                'volume': float,   # 交易数量
                'price': float     # 交易价格（可选）
            }
        """
        raise NotImplementedError("on_bar method must be implemented")
        
    def on_init(self):
        """策略初始化时调用"""
        pass
        
    def on_exit(self):
        """策略结束时调用"""
        pass
    
    def check_trading_time(self, timestamp):
        """
        检查是否在交易时间内
        
        Parameters:
        -----------
        timestamp: datetime
            当前时间戳
            
        Returns:
        --------
        bool: 是否在交易时间内
        """
        current_time = pd.Timestamp(timestamp).time()
        return (current_time >= self.trading_times['start_time'] and 
                current_time < self.trading_times['close_time'])
    
    def should_close_position(self, timestamp):
        """
        检查是否需要收盘平仓
        
        Parameters:
        -----------
        timestamp: datetime
            当前时间戳
            
        Returns:
        --------
        bool: 是否需要平仓
        """
        current_time = pd.Timestamp(timestamp).time()
        return current_time >= self.trading_times['close_time']
    
    def generate_close_signals(self, bar):
        """
        生成平仓信号
        
        Parameters:
        -----------
        bar: pd.Series
            当前K线数据
            
        Returns:
        --------
        list: 平仓信号列表
        """
        signals = []
        if self.current_position != 0:
            volume = 1000000 / bar['close']  # 默认交易金额
            signals.append({
                'direction': -self.current_position,
                'volume': volume,
                'price': bar['close']
            })
        return signals
    
    def calculate_position_volume(self, price, amount=1000000):
        """
        计算持仓数量
        
        Parameters:
        -----------
        price: float
            交易价格
        amount: float
            目标交易金额
            
        Returns:
        --------
        float: 交易数量
        """
        return amount / price
    
    def get_indicator_data(self):
        """
        获取策略指标数据，用于图表展示
        
        Returns:
        --------
        dict: {
            'name': str,       # 指标名称
            'data': list,      # 指标数据列表
            'color': str,      # 指标线颜色
            'alpha': float     # 透明度
        }
        """
        return None
 