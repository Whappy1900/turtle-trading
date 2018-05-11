# turtle-trading
Profit using trend trading

# return
|Date|Return %|
|-|-|
|2003-08-05 to 2004-01-01|(78.28)|
|2004-01-01 to 2005-01-01|(2286.12)|
|2005-01-01 to 2006-01-01|(301.43)|
|2006-01-01 to 2007-01-01|(309.42)|
|2007-01-01 to 2008-01-01|4172.06|
|2008-01-01 to 2009-01-01|3712.64|
|2009-01-01 to 2010-01-01|53.81|
|2010-01-01 to 2011-01-01|21.81|
|2011-01-01 to 2012-01-01|(78.31)|
|2012-01-01 to 2013-01-01|2.45|
|2013-01-01 to 2014-01-01|(24.78)|
|2014-01-01 to 2015-01-01|(20.22)|
|2015-01-01 to 2016-01-01|(50.79)|
|2016-01-01 to 2017-01-01|(30.94)|
|2017-01-01 to 2017-05-26|(16.36)|

# strategy
See https://github.com/vyq/turtle-trading/raw/master/the-original-turtle-trading-rules.pdf

Exit on price hitting trailing stop of 2 times average true range.

# backtest
- Start date: 2003-08-05
- End date: 2017-05-25
- Cash: USD 1,000,000
- Trading calendar: US Futures

Suppress null warnings after first log message: https://www.quantopian.com/posts/warn-numpy-slash-lib-slash-nanfunctions-dot-py-319-runtimewarning-all-nan-slice-encountered

# initialize
Initialize parameters. Executes at 1970-01-01 7 PM UTC-4. Intersect Quantopian futures universe with Turtle Trading markets.

Universe: https://www.quantopian.com/help#available-futures

# handle-data
Process data every minute. Executes from 6:31 AM to 5 PM UTC-4.

# clear-stops
Clear stops 1 minute after market open.

# log-risks
Log long and short risk 1 minute before market close.

# get-prices
Get high, low, and close prices. Get 22 daily bars for computing average true range.

# validate-prices
Drop markets with null prices.

# compute-highs
Compute 20 and 55 day high. Get highest high for the past 20 and 55 days.

# compute-lows
Compute 20 and 55 day low. Get lowest low for the past 20 and 55 days.

# get-contracts
Get futures contracts.

# is-trade-allowed
Check if allowed to trade.

Do not trade if:
- Cash is less than or equal to 0
- Capital is less than or equal to 0
- Price is less than 1
- Open order exists for this market
- Exceed market risk limit
- Exceed direction risk limit

# compute-average-true-ranges
Compute average true ranges, or N. Use a rolling window that is 1 day larger than the moving average.

Average true range: https://mrjbq7.github.io/ta-lib/func_groups/volatility_indicators.html

TA-Lib module: https://www.quantopian.com/help#ide-module-import

# compute-dollar-volatilities
Compute dollar volatilities, or dollars per point.

`context.dollar_volatility` = `multiplier` * `average_true_range`

# compute-trade-sizes
Compute trade sizes, or amount per trade.

`context.trade_size` = `context.capital` * `context.capital_risk_per_trade` / `context.dollar_volatility`

# update-risks
Update long, short, and market risks.

# place-stop-orders
Place stop orders at 2 times average true range.

If long and `price` is greater than or equal to `cost_basis`, then `context.stop[market] = price - context.average_true_range[market] * context.stop_multiplier`.

If long and `price` is less than `cost_basis`, then `context.stop[market] = cost_basis - context.average_true_range[market] * context.stop_multiplier`.

If short and `price` is greater than or equal to `cost_basis`, then `context.stop[market] = cost_basis + context.average_true_range[market] * context.stop_multiplier`.

If short and `price` is less than `cost_basis`, then `context.stop[market] = price + context.average_true_range[market] * context.stop_multiplier`.

# detect-entry-signals
Place limit orders on 20 or 55 day breakout.

# reflect
Markets are fixed or dynamic:
- Fixed markets allow consistency over time
- Dynamic markets generate ideas over time

Context has limitations:
- Scalar value saved to context in `initialize()` is accessible in `handle_data()`
- Scalar value saved to context in `handle_data()` is accessible in `before_trading_start()` and `schedule_function()`
- Scalar value saved to context in `before_trading_start()` or `schedule_function()` is not accessible in `handle_data()`
- 3-dimensional array saved to context in `before_trading_start()` or `schedule_function()` is not accessible in `handle_data()`

Define `context` variable in `initialize()`, so that it can be used in other methods.

`data.history()` contains data from the first minute of the current market day, if called in `handle_data()`.

`before_trading_start()` should not be used for futures as it executes at 8:45 AM UTC-4.

`context.contract.multiplier` equates to dollars per point.

`context.trade_size` will be less than or equal to 0 if `context.dollar_volatility` is larger than `context.capital * context.capital_risk_per_trade`.

Orders placed at end of day may fail to fill because of insufficient liquidity.

`context.portfolio.positions[position].amount` is negative if position is short.

There are dates where `data.history()` returns null prices for all markets.

Risk limits do not account for partial fills.

Direction risk limit is not capped at 12.
