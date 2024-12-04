import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
from matplotlib.dates import DateFormatter, AutoDateLocator
import matplotlib as mpl
import sys
import platform

def setup_chinese_font():
    """设置中文字体"""
    system = platform.system()
    
    if system == "Windows":
        # Windows系统
        font_list = [
            'Microsoft YaHei',
            'SimHei',
            'STSong',
            'SimSun'
        ]
    elif system == "Darwin":
        # macOS系统
        font_list = [
            'Arial Unicode MS',
            'Heiti TC',
            'STHeiti'
        ]
    else:
        # Linux系统
        font_list = [
            'WenQuanYi Micro Hei',
            'Droid Sans Fallback',
            'Noto Sans CJK JP'
        ]

    # 遍历字体列表，尝试设置
    for font in font_list:
        try:
            plt.rcParams['font.sans-serif'] = [font]
            plt.rcParams['axes.unicode_minus'] = False
            # 测试是否可以正常显示中文
            fig = plt.figure()
            plt.text(0.5, 0.5, '测试中文')
            plt.close(fig)
            # print(f"成功设置字体: {font}")
            return True
        except:
            continue
    
    # 如果上述方法都失败，尝试使用系统默认字体
    try:
        import matplotlib.font_manager as fm
        path = fm.findfont(fm.FontProperties(family='sans-serif'))
        plt.rcParams['font.sans-serif'] = [path]
        return True
    except:
        print("警告：无法设置中文字体，图表中的中文可能无法正常显示")
        return False

# 在程序启动时调用此函数
setup_chinese_font()

# 设置全局绘图样式
plt.style.use('seaborn')
mpl.rcParams['figure.dpi'] = 100
mpl.rcParams['savefig.dpi'] = 100

class BacktestVisualizer:
    def __init__(self, trades, data_df, pnl_df, strategy):
        self.trades = trades
        self.trades_df = pd.DataFrame(trades)
        self.data_df = data_df
        self.pnl_df = pnl_df
        self.strategy = strategy
        
    def plot_trades_and_indicators(self, figsize=(15, 8)):
        """绘制价格、交易点位和策略指标"""
        fig, ax = plt.subplots(figsize=figsize)
        
        # 只保留交易时段的数据
        trading_data = self._get_trading_data(self.data_df)
        
        # 绘制价格走势
        ax.plot(range(len(trading_data)), trading_data['close'], 
                label='Price', color='gray', alpha=0.7)
        
        # 绘制策略指标
        indicator_data = self.strategy.get_indicator_data()
        if indicator_data:
            if isinstance(indicator_data, list):
                # 多个指标
                for indicator in indicator_data:
                    self._plot_indicator(ax, trading_data, indicator)
            else:
                # 单个指标
                self._plot_indicator(ax, trading_data, indicator_data)
        
        # 绘制交易点位
        normal_trades = self.trades_df[self.trades_df['type'] == 'trade']
        buy_trades = normal_trades[normal_trades['direction'] == 1]
        sell_trades = normal_trades[normal_trades['direction'] == -1]
        
        # 买入点（绿色上箭头）
        if not buy_trades.empty:
            buy_trades['timestamp'] = pd.to_datetime(buy_trades['timestamp'])
            # 找到买入时间点在trading_data中的位置
            buy_indices = [trading_data.index.get_loc(t) for t in buy_trades['timestamp']
                          if t in trading_data.index]
            ax.scatter(buy_indices, buy_trades['price'], 
                      marker='^', color='green', s=100, label='Buy')
        
        # 卖出点（红色下箭头）
        if not sell_trades.empty:
            sell_trades['timestamp'] = pd.to_datetime(sell_trades['timestamp'])
            # 找到卖出时间点在trading_data中的位置
            sell_indices = [trading_data.index.get_loc(t) for t in sell_trades['timestamp']
                           if t in trading_data.index]
            ax.scatter(sell_indices, sell_trades['price'], 
                      marker='v', color='red', s=100, label='Sell')
        
        # 标记主力合约切换点
        switch_trades = self.trades_df[self.trades_df['type'] == 'switch_close']
        if not switch_trades.empty:
            switch_trades['timestamp'] = pd.to_datetime(switch_trades['timestamp'])
            for _, trade in switch_trades.iterrows():
                if trade['timestamp'] in trading_data.index:
                    switch_idx = trading_data.index.get_loc(trade['timestamp'])
                    ax.axvline(x=switch_idx, color='blue', linestyle='--', alpha=0.3)
            ax.axvline(x=switch_idx, color='blue', linestyle='--', 
                      alpha=0.3, label='Contract Switch')
        
        # 设置x轴刻度和标签
        num_points = len(trading_data)
        step = max(num_points // 8, 1)
        xticks_pos = range(0, num_points, step)
        xticks_labels = trading_data.index[::step]
        
        ax.set_xticks(xticks_pos)
        ax.set_xticklabels([x.strftime('%Y-%m-%d %H:%M') for x in xticks_labels], rotation=45)
        
        ax.set_title('Price and Trade Points')
        ax.set_xlabel('Time')
        ax.set_ylabel('Price')
        ax.legend()
        plt.tight_layout()
        return fig
    
    def _plot_indicator(self, ax, trading_data, indicator):
        """绘制单个指标"""
        df = pd.DataFrame(indicator['data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        trading_indicator = self._get_trading_data(df.set_index('timestamp'))
        
        if not trading_indicator.empty:
            ax.plot(range(len(trading_indicator)), 
                   trading_indicator[indicator['value_key']], 
                   label=indicator['name'],
                   color=indicator['color'],
                   alpha=indicator['alpha'])
    
    def _get_trading_data(self, df):
        """获取交易时段的数据"""
        # 确保索引是datetime类型
        df.index = pd.to_datetime(df.index)
        
        # 只保留交易时段的据
        trading_mask = (df.index.time >= pd.Timestamp('09:30:00').time()) & \
                      (df.index.time <= pd.Timestamp('15:00:00').time())
        trading_data = df[trading_mask]
        
        return trading_data
    
    def plot_pnl_curve(self, figsize=(15, 12)):
        """绘制净值曲线和仓位变化"""
        # 创建两个子图
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[2, 1], sharex=True)
        
        # 确保时间戳格式正确并只保留交易时段数据
        trading_data = self._get_trading_data(self.pnl_df)
        
        # 绘制净值曲线（上图）
        ax1.plot(range(len(trading_data)), trading_data['net_value'], 
                label='Strategy Net Value', color='blue')
        
        # 添加基准线
        ax1.axhline(y=1, color='gray', linestyle='--', alpha=0.5, label='Benchmark')
        
        # 设置上图标题和标签
        ax1.set_title('Strategy Net Value Curve')
        ax1.set_ylabel('Net Value')
        ax1.grid(True)
        ax1.legend()
        
        # 绘制仓位变化（下图）
        ax2.plot(range(len(trading_data)), trading_data['position'], 
                label='Position', color='orange', alpha=0.8)
        ax2.fill_between(range(len(trading_data)), trading_data['position'], 
                         0, alpha=0.2, color='orange')
        
        # 添加零线
        ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        
        # 设置下图标题和标签
        ax2.set_title('Position')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Position Size')
        ax2.grid(True)
        
        # 设置x轴刻度和标签
        num_points = len(trading_data)
        step = max(num_points // 8, 1)
        xticks_pos = range(0, num_points, step)
        xticks_labels = trading_data.index[::step]
        
        ax2.set_xticks(xticks_pos)
        ax2.set_xticklabels([x.strftime('%Y-%m-%d %H:%M') for x in xticks_labels], rotation=45)
        
        # 调整子图间距
        plt.tight_layout()
        return fig