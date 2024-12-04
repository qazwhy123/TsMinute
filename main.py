from backtest_engine import BacktestEngine
from strategies.vwap_strategy import VWAPStrategy
from strategies.ma_strategy import MAStrategy
from strategies.grid_strategy import GridStrategy
from strategies.daily_return_strategy import DailyReturnStrategy

def run_strategy_backtest(strategy, symbol, start_date, end_date):
    engine = BacktestEngine(initial_capital=1000000, commission_rate=0.00005)
    results = engine.run_backtest(
        strategy=strategy,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date
    )
    return results

if __name__ == "__main__":
    # 回测参数
    symbol = "IF"
    start_date = "20200101"
    end_date = "20241105"
    
    # # 测试VWAP策略
    # vwap_strategy = VWAPStrategy()
    # vwap_results = run_strategy_backtest(
    #     vwap_strategy, 
    #     symbol, 
    #     start_date, 
    #     end_date
    # )
    
    # # 测试MA策略
    # ma_strategy = MAStrategy(short_period=5, long_period=20)
    # ma_results = run_strategy_backtest(
    #     ma_strategy, 
    #     symbol, 
    #     start_date, 
    #     end_date
    # )
    
    # # 测试网格策略
    # grid_strategy = GridStrategy(grid_num=5, price_range_ratio=0.025)
    # grid_results = run_strategy_backtest(
    #     grid_strategy,
    #     symbol,
    #     start_date,
    #     end_date
    # )
    
    # 测试每日涨幅策略
    daily_return_strategy = DailyReturnStrategy(
        return_threshold=0.01,  # 2%的阈值
        entry_time='14:50:00'  # 14:50开仓
    )
    daily_return_results = run_strategy_backtest(
        daily_return_strategy,
        symbol,
        start_date,
        end_date
    ) 