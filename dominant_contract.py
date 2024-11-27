import pandas as pd
import os
from data_loader import MinuteDataLoader

class DominantContractLoader:
    def __init__(self, data_path="D:\\Quant\\Data\\TuShare\\FutureMinK"):
        self.data_loader = MinuteDataLoader(data_path)
        
    def get_dominant_symbol(self, product_code, date):
        """
        获取某个日期的主力合约代码
        
        Parameters:
        -----------
        product_code: str
            期货品种代码，如 'IF'
        date: str
            日期，格式：'YYYYMMDD'
            
        Returns:
        --------
        str:
            主力合约代码
        """
        available_symbols = self.data_loader.get_available_symbols(date)
        # 筛选出该品种的所有合约
        product_symbols = [s for s in available_symbols if s.startswith(product_code)]
        
        if not product_symbols:
            return None
            
        # 读取每个合约的数据，比较成交量
        volumes = {}
        for symbol in product_symbols:
            try:
                data = self.data_loader.load_future_data(symbol, date, date)
                volumes[symbol] = data['volume'].sum()
            except:
                continue
                
        if not volumes:
            return None
            
        # 返回成交量最大的合约作为主力合约
        return max(volumes.items(), key=lambda x: x[1])[0]
    
    def load_dominant_data(self, product_code, start_date, end_date):
        """
        加载主力合约数据
        
        Parameters:
        -----------
        product_code: str
            期货品种代码，如 'IF'
        start_date: str
            开始日期，格式：'YYYYMMDD'
        end_date: str
            结束日期，格式：'YYYYMMDD'
            
        Returns:
        --------
        pd.DataFrame:
            连续主力合约数据
        """
        current_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        
        # 存储每天的主力合约数据
        daily_data = []
        current_symbol = None
        last_close = None
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y%m%d')
            
            # 获取当日主力合约
            new_symbol = self.get_dominant_symbol(product_code, date_str)
            if new_symbol is None:
                current_date += pd.Timedelta(days=1)
                continue
                
            # 如果主力合约发生变化，需要处理价格跳转
            if new_symbol != current_symbol and current_symbol is not None:
                # 获取新旧合约的价格数据
                try:
                    old_data = self.data_loader.load_future_data(current_symbol, date_str, date_str)
                    new_data = self.data_loader.load_future_data(new_symbol, date_str, date_str)
                    
                    # 计算价格调整因子
                    if not old_data.empty and not new_data.empty:
                        price_ratio = old_data['close'].iloc[-1] / new_data['close'].iloc[0]
                        last_close = old_data['close'].iloc[-1]
                except:
                    price_ratio = 1.0
            
            # 加载当日数据
            try:
                data = self.data_loader.load_future_data(new_symbol, date_str, date_str)
                if not data.empty:
                    # 添加合约信息
                    data['symbol'] = new_symbol
                    daily_data.append(data)
            except:
                pass
                
            current_symbol = new_symbol
            current_date += pd.Timedelta(days=1)
            
        if not daily_data:
            raise ValueError(f"未找到{product_code}在指定日期范围内的主力合约数据")
            
        # 合并数据
        combined_data = pd.concat(daily_data)
        combined_data = combined_data.sort_index()
        
        return combined_data 