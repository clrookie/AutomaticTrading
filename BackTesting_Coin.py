import pyupbit
import matplotlib.pyplot as plt
import time
import pandas as pd

def short_trading_for_1percent(ticker):
    dfs = [ ]
    df = pyupbit.get_ohlcv(ticker, interval="minute1", to="20210414 23:00:00")
    dfs.append(df)

    for i in range(60):
        df = pyupbit.get_ohlcv(ticker, interval="minute1", to=df.index[0])
        dfs.append(df)
        time.sleep(0.2)

    df = pd.concat(dfs)
    df = df.sort_index()

    # df['close'].plot()
    # plt.show()

    # 1) 매수 일자 판별
    cond = df['high'] >= df['open'] * 1.01

    acc_ror = 1
    sell_date = None

    # 2) 매도 조건 탐색 및 수익률 계산
    for buy_date in df.index[cond]:
        if sell_date != None and buy_date <= sell_date:
            continue

        target = df.loc[ buy_date :  ]

        cond = target['high'] >= target['open'] * 1.02
        sell_candidate = target.index[cond]

        if len(sell_candidate) == 0:
            buy_price = df.loc[buy_date, 'open'] * 1.01
            sell_price = df.iloc[-1, 3]
            acc_ror *= (sell_price / buy_price)
            break
        else:
            sell_date = sell_candidate[0]
            acc_ror *= 1.005
            # 수수료 0.001 + 슬리피지 0.004

    return acc_ror

for ticker in ["KRW-BTC", "KRW-LTC", "KRW-ETH", "KRW-ADA"]:
    ror = short_trading_for_1percent(ticker)
    print(ticker, ror)
