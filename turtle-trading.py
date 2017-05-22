from talib import ATR
from time import time

def initialize(context):
    """
    Initialize parameters.
    """
    context.is_debug = False
    
    if context.is_debug:
        start_time = time()
    
    context.symbols = [
        'BP',
        'CD',
        'CL',
        'ED',
        'GC',
        'HG',
        'HO',
        'HU',
        'JY',
        'SB',
        'SF',
        'SP',
        'SV',
        'TB',
        'TY',
        'US'
    ]
    context.markets = None
    context.prices = None
    context.twenty_day_breakout = 20
    context.fifty_five_day_breakout = 55
    context.twenty_day_high = {}
    context.twenty_day_low = {}
    context.fifty_five_day_high = {}
    context.fifty_five_day_low = {}
    context.contracts = None
    context.average_true_range = None
    context.dollar_volatility = None
    context.capital = context.portfolio.starting_cash
    context.profit = None
    context.capital_risk_per_trade = 0.01
    context.capital_multiplier = 2
    context.trade_size = None
    context.single_market_limit = 4
    context.closely_correlated_market_limit = 6
    context.loosely_correlated_market_limit = 6
    context.long_limit = 12
    context.short_limit = 12
    
    schedule_function(
        func=validate_markets,
        time_rule=time_rules.market_open(minutes=1)
    )
    
    if context.is_debug:
        time_taken = (time() - start_time) * 1000
        log.debug('Executed in %f ms.' % time_taken)
        assert(len(context.symbols) == 16)

def handle_data(context, data):
    """
    Process data every minute.
    """
    if context.is_debug:
        start_time = time()
        
    if context.markets is not None:
        get_prices(context, data)
        validate_prices(context)
        
        context.prices = context.prices.transpose(2, 1, 0)
        context.prices = context.prices.reindex()
        
        compute_high(context)
        compute_low(context)
        get_contracts(context, data)
        
        for market in context.prices.items:
            price = context.prices[market].close[-1]
            
            compute_average_true_range(context, market)
            compute_dollar_volatility(context, market)
            compute_trade_size(context)
            
            if price > context.twenty_day_high[market]\
                    or price > context.fifty_five_day_high[market]:
                log.info(
                    'Long %s %i @ %.2f'
                    % (market.root_symbol, context.trade_size, price)
                )
            if price < context.twenty_day_low[market]\
                    or price < context.fifty_five_day_low[market]:
                log.info(
                    'Short %s %i @ %.2f'
                    % (market.root_symbol, context.trade_size, price)
                )
        
    if context.is_debug:
        time_taken = (time() - start_time) * 1000
        log.debug('Executed in %f ms.' % time_taken)

def validate_markets(context, data):
    """
    Drop markets that stopped trading.
    """
    if context.is_debug:
        start_time = time()
        
    context.markets = map(
        lambda market: continuous_future(market),
        context.symbols
    )
    
    markets = context.markets[:]
    
    for market in markets:
        if market.end_date < get_datetime():
            context.markets.remove(market)
            
            if context.is_debug:
                log.debug(
                    '%s stopped trading. Dropped.'
                    % market.root_symbol
                )
            
    if context.is_debug:
        time_taken = (time() - start_time) * 1000
        log.debug('Executed in %f ms.' % time_taken)
        assert(len(context.markets) == 14)

def get_prices(context, data):
    """
    Get high, low, and close prices.
    """
    if context.is_debug:
        start_time = time()
        
    fields = ['high', 'low', 'close']
    bars = 22
    frequency = '1d'
    
    context.prices = data.history(
        context.markets,
        fields,
        bars,
        frequency
    )
    
    if context.is_debug:
        time_taken = (time() - start_time) * 1000
        log.debug('Executed in %f ms.' % time_taken)
        assert(context.prices.shape[0] == 3)
        assert(context.prices.shape[1] == 22)
        assert(context.prices.shape[2] > 8)

def validate_prices(context):
    """
    Drop markets with null prices.
    """
    if context.is_debug:
        start_time = time()
        
    context.prices.dropna(axis=2, inplace=True)
    
    validated_markets = map(
        lambda market: market.root_symbol,
        context.prices.axes[2]
    )
    
    markets = map(
        lambda market: market.root_symbol,
        context.markets
    )
    
    dropped_markets = list(
        set(markets) - set(validated_markets)
    )
    
    if context.is_debug and dropped_markets:
        log.debug(
            'Null prices for %s. Dropped.'
            % ', '.join(dropped_markets)
        )
        
    context.markets = map(
        lambda market: continuous_future(market),
        validated_markets
    )
    
    if context.is_debug:
        time_taken = (time() - start_time) * 1000
        log.debug('Executed in %f ms.' % time_taken)
        assert(context.prices.shape[0] == 3)
        assert(context.prices.shape[1] == 22)
        assert(context.prices.shape[2] > 8)

def compute_high(context):
    """
    Compute 20 and 55 day high.
    """
    for market in context.prices.items:
        context.twenty_day_high[market] = context\
            .prices[market]\
            .high[-context.twenty_day_breakout-1:-1]\
            .max()
        context.fifty_five_day_high[market] = context\
            .prices[market]\
            .high[-context.fifty_five_day_breakout-1:-1]\
            .max()
        
    if context.is_debug:
        assert(len(context.twenty_day_high) > 8)
        assert(len(context.fifty_five_day_high) > 8)

def compute_low(context):
    """
    Compute 20 and 55 day low.
    """
    for market in context.prices.items:
        context.twenty_day_low[market] = context\
            .prices[market]\
            .low[-context.twenty_day_breakout-1:-1]\
            .min()
        context.fifty_five_day_low[market] = context\
            .prices[market]\
            .low[-context.fifty_five_day_breakout-1:-1]\
            .min()
        
    if context.is_debug:
        assert(len(context.twenty_day_low) > 8)
        assert(len(context.fifty_five_day_low) > 8)

def get_contracts(context, data):
    """
    Get current contracts.
    """
    if context.is_debug:
        start_time = time()
        
    fields = 'contract'
    
    context.contracts = data.current(
        context.markets,
        fields
    )
    
    if context.is_debug:
        time_taken = (time() - start_time) * 1000
        log.debug('Executed in %f ms.' % time_taken)
        assert(context.contracts.shape[0] > 8)

def compute_average_true_range(context, market):
    """
    Compute average true range, or N.
    """
    if context.is_debug:
        start_time = time()
        
    rolling_window = 21
    moving_average = 20
    
    context.average_true_range = ATR(
        context.prices[market].high[-rolling_window:],
        context.prices[market].low[-rolling_window:],
        context.prices[market].close[-rolling_window:],
        timeperiod=moving_average
    )[-1]
    
    if context.is_debug:
        time_taken = (time() - start_time) * 1000
        log.debug('Executed in %f ms.' % time_taken)
        assert(context.average_true_range > 0)

def compute_dollar_volatility(context, market):
    """
    Compute dollar volatility.
    """
    if context.is_debug:
        start_time = time()
        
    contract = context.contracts[market]
    
    context.dollar_volatility = contract.tick_size\
        * context.average_true_range
    
    if context.is_debug:
        time_taken = (time() - start_time) * 1000
        log.debug('Executed in %f ms.' % time_taken)
        assert(context.dollar_volatility > 0)

def compute_trade_size(context):
    """
    Compute trade size.
    """
    if context.is_debug:
        start_time = time()
        
    context.profit = context.portfolio.portfolio_value\
        - context.portfolio.starting_cash
        
    if context.profit < 0:
        context.capital = context.portfolio.starting_cash\
            + context.profit\
            * context.capital_multiplier

    context.trade_size = int(context.capital\
        * context.capital_risk_per_trade\
        / context.dollar_volatility)
        
    if context.is_debug:
        time_taken = (time() - start_time) * 1000
        log.debug('Executed in %f ms.' % time_taken)
        assert(context.trade_size > 0)