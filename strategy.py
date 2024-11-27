class BaseStrategy:
    def __init__(self):
        self.positions = {}
    
    def on_bar(self, timestamp, bar):
        """
        处理每个分钟的数据
        
        Parameters:
        -----------
        timestamp: pd.Timestamp
            当前时间戳
        bar: pd.Series
            当前分钟的OHLCV数据
            
        Returns:
        --------
        list of dict:
            交易信号列表，每个信号为字典格式：
            {
                'direction': int,  # 1买入，-1卖出
                'volume': float,   # 交易数量
                'price': float     # 交易价格
            }
        """
        raise NotImplementedError("策略类必须实现on_bar方法") 