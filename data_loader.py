import pandas as pd
import os

class MinuteDataLoader:
    def __init__(self, data_path="D:\\Quant\\Data\\TuShare\\FutureMinK"):
        self.data_path = data_path
        
    def load_future_data(self, symbol, start_date, end_date):
        """
        加载期货分钟数据
        
        Parameters:
        -----------
        symbol: str
            期货合约代码
        start_date: str
            开始日期，格式：'YYYYMMDD'
        end_date: str
            结束日期，格式：'YYYYMMDD'
            
        Returns:
        --------
        pd.DataFrame
            包含以下列：
            - datetime: 时间戳
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            - amount: 成交额
        """
        data_frames = []
        current_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        
        while current_date <= end_date:
            # 构建日期文件夹路径
            date_folder = current_date.strftime('%Y%m%d')
            file_path = os.path.join(self.data_path, date_folder, f"{symbol}.pkl")
            
            if os.path.exists(file_path):
                try:
                    df = pd.read_pickle(file_path)
                    # 确保时间列格式正确
                    if 'datetime' not in df.columns and 'time' in df.columns:
                        df['datetime'] = pd.to_datetime(df['time'])
                    df = df.set_index('datetime')
                    data_frames.append(df)
                except Exception as e:
                    print(f"读取文件 {file_path} 时出错: {str(e)}")
                
            current_date += pd.Timedelta(days=1)
        
        if not data_frames:
            raise ValueError(f"未找到{symbol}在指定日期范围内的数据")
            
        combined_data = pd.concat(data_frames, axis=0)
        combined_data = combined_data.sort_index()
        
        # 确保数据包含必要的列
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in combined_data.columns]
        if missing_columns:
            raise ValueError(f"数据缺少必要的列: {missing_columns}")
            
        return combined_data

    def get_available_symbols(self, date):
        """
        获取指定日期可用的期货合约列表
        
        Parameters:
        -----------
        date: str
            日期，格式：'YYYYMMDD'
            
        Returns:
        --------
        list:
            可用的期货合约代码列表
        """
        date_folder = os.path.join(self.data_path, date)
        if not os.path.exists(date_folder):
            return []
        
        symbols = []
        for file_name in os.listdir(date_folder):
            if file_name.endswith('.pkl'):
                symbols.append(file_name[:-4])  # 移除.pkl后缀
        
        return symbols