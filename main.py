from backtest_engine import BacktestEngine
from strategies.vwap_strategy import VWAPStrategy
from strategies.ma_strategy import MAStrategy
from strategies.grid_strategy import GridStrategy

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
    start_date = "20241101"
    end_date = "20241105"
    
    # 测试VWAP策略
    vwap_strategy = VWAPStrategy()
    vwap_results = run_strategy_backtest(
        vwap_strategy, 
        symbol, 
        start_date, 
        end_date
    )
    
    # 测试MA策略
    ma_strategy = MAStrategy(short_period=5, long_period=20)
    ma_results = run_strategy_backtest(
        ma_strategy, 
        symbol, 
        start_date, 
        end_date
    )
    
    # 测试网格策略
    grid_strategy = GridStrategy(grid_num=10, price_range_ratio=0.02)
    grid_results = run_strategy_backtest(
        grid_strategy,
        symbol,
        start_date,
        end_date
    ) 