import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 가상의 주식 가격 데이터 생성
np.random.seed(42)
dates = pd.date_range(start='2022-01-01', end='2023-01-01', freq='B')
prices = np.cumprod(1 + np.random.normal(0, 0.01, len(dates)))
df = pd.DataFrame({'Date': dates, 'Price': prices})
df.set_index('Date', inplace=True)

# 간단한 이동평균 전략 구현
def moving_average_strategy(data, short_window, long_window):
    signals = pd.DataFrame(index=data.index)
    signals['signal'] = 0.0

    # 이동평균 계산
    signals['short_mavg'] = data['Price'].rolling(window=short_window, min_periods=1, center=False).mean()
    signals['long_mavg'] = data['Price'].rolling(window=long_window, min_periods=1, center=False).mean()

    # 이동평균 크로스오버 신호 생성
    signals['signal'][short_window:] = np.where(signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1.0, 0.0)

    # 신호의 차이를 계산하여 포지션을 나타내는 열 생성
    signals['positions'] = signals['signal'].diff()

    return signals

# 백테스팅 함수
def backtest(data, signals):
    initial_capital = 100000.0
    positions = pd.DataFrame(index=signals.index).fillna(0.0)
    positions['asset'] = 100 * signals['signal']   # 간단히 전체 자본을 투자

    portfolio = positions.multiply(data['Price'], axis=0)
    pos_diff = positions.diff()

    # 초기 자본 대비 수익률 계산
    portfolio['holdings'] = (positions.multiply(data['Price'], axis=0)).sum(axis=1)
    portfolio['cash'] = initial_capital - (pos_diff.multiply(data['Price'], axis=0)).sum(axis=1).cumsum()
    portfolio['total'] = portfolio['cash'] + portfolio['holdings']
    portfolio['returns'] = portfolio['total'].pct_change()

    return portfolio

# 전략 파라미터 설정
short_window = 40
long_window = 100

# 전략 수행
signals = moving_average_strategy(df, short_window, long_window)

# 백테스팅
portfolio = backtest(df, signals)

# 결과 시각화
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

ax1.plot(df.index, df['Price'], label='Stock Price')
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