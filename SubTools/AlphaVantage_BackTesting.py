import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt

# Alpha Vantage API 키
api_key = 'ZBB6ZP5CXN008QAX'

# 종목 코드 (KODEX 레버리지 ETF: 122630)
symbol = '122630.KS'

# Alpha Vantage API 엔드포인트 및 파라미터 설정
endpoint = 'https://www.alphavantage.co/query'
function = 'TIME_SERIES_DAILY'
outputsize = 'full'

# API 호출
params = {
    'function': function,
    'symbol': symbol,
    'outputsize': outputsize,
    'apikey': api_key
}

response = requests.get(endpoint, params=params)
data = response.json()

# 데이터 가공
if 'Time Series (Daily)' in data:
    prices = pd.DataFrame(data['Time Series (Daily)']).T
    prices.index = pd.to_datetime(prices.index)
    prices['close'] = prices['4. close'].astype(float)
    prices = prices[['close']]
    prices.sort_index(inplace=True)

    # 2021년부터 2022년까지의 데이터 선택
    prices = prices['2021-01-01':'2022-12-31']

    # 간단한 이동평균 전략 구현
    short_window = 40
    long_window = 100

    signals = pd.DataFrame(index=prices.index)
    signals['signal'] = 0.0
    signals['short_mavg'] = prices['close'].rolling(window=short_window, min_periods=1, center=False).mean()
    signals['long_mavg'] = prices['close'].rolling(window=long_window, min_periods=1, center=False).mean()

    signals['signal'][short_window:] = np.where(signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1.0, 0.0)
    signals['positions'] = signals['signal'].diff()

    # 백테스팅
    initial_capital = 100000.0
    positions = pd.DataFrame(index=signals.index).fillna(0.0)
    positions['asset'] = 100 * signals['signal']  # 간단히 전체 자본을 투자

    portfolio = positions.multiply(prices['close'], axis=0)
    pos_diff = positions.diff()

    portfolio['holdings'] = (positions.multiply(prices['close'], axis=0)).sum(axis=1)
    portfolio['cash'] = initial_capital - (pos_diff.multiply(prices['close'], axis=0)).sum(axis=1).cumsum()
    portfolio['total'] = portfolio['cash'] + portfolio['holdings']
    portfolio['returns'] = portfolio['total'].pct_change()

    # 결과 시각화
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    ax1.plot(prices.index, prices['close'], label='Stock Price')
    ax1.plot(signals.index, signals['short_mavg'], label='Short MA')
    ax1.plot(signals.index, signals['long_mavg'], label='Long MA')

    ax1.plot(signals.loc[signals.positions == 1.0].index, signals.short_mavg[signals.positions == 1.0], '^', markersize=10, color='g', label='Buy Signal')
    ax1.plot(signals.loc[signals.positions == -1.0].index, signals.short_mavg[signals.positions == -1.0], 'v', markersize=10, color='r', label='Sell Signal')

    ax1.set_ylabel('Price')
    ax1.legend()

    ax2.plot(portfolio.index, portfolio['total'], label='Portfolio Value', color='b')
    ax2.set_ylabel('Portfolio Value')
    ax2.legend()

    plt.show()

else:
    print('Error fetching data. Check your API key and symbol.')