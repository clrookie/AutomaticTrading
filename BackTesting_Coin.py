import pyupbit
import numpy as np


total_period = 60
half = int(total_period / 2)
delta = 0
cnt = 0
target_price = 0

df = pyupbit.get_ohlcv("KRW-BTC", interval="minute240", count=total_period)


for i in range(0,half):
        stck_hgpr = int(df.iloc[i]['high']) #고가
        stck_clpr = int(df.iloc[i]['close']) #종가
        stck_oprc = int(df.iloc[i]['open']) #시가

        if stck_oprc >= stck_clpr : #음봉
            delta += stck_hgpr - stck_oprc
            cnt += 1
    
if cnt > 0:
    delta /= cnt # 평균

target_price = int(df.iloc[data_period-1]['open']) #현재 구간 시가
target_price += delta


df = pyupbit.get_ohlcv("KRW-BTC", interval="minute240", count=half)



df['range'] = delta
df['target'] = target_price

df['ror'] = np.where(df['high'] > df['target'],
                        df['close'] / df['target'],
                    1)

print(df)
    
#     ror = df['ror'].cumprod().iloc[-2]
#     return ror

# for k in np.arange(0.1, 1.0, 0.1):
#     ror = get_ror(k)
#     print("%.1f %f" % (k, ror))