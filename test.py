import time
from datetime import datetime, timedelta
import pyupbit
import requests
# import math


access = "your-access"
secret = "your-secret"
myToken = "xoxb-your-token"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

# def get_balance(ticker):
#     """잔고 조회"""
#     balances = upbit.get_balances()
#     for b in balances:
#         if b['currency'] == ticker:
#             if b['balance'] is not None:
#                 return float(b['balance'])
#             else:
#                 return 0
#     return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def aaa():
    aa = 34790.0000
    return int(aa) 

print(f"### total_cash ###")

# try:
      # # 코스피(KOSPI) 종목 코드
    # kospi_code = "005930"  # 삼성전자 예시

    # # 코스피 종목의 일별 데이터 가져오기
    # df_daily = fdr.DataReader(kospi_code, exchange="KRX", start="2024-03-07", end="2024-03-07")
    
    # df = pyupbit.get_ohlcv("396500", interval="minute10", count=1) 

    # aa = df.index[0].minute

    # data = pyupbit.get_ohlcv("KRW-00593", interval="minute10", count=20)

    # average_price_20 = data['close'].mean()

    # total_cash = 144560
    # b = 40000
    # b = total_cash % b
    
    # print(b)
    
    # if total_cash > b:
    #     total_cash -= b

    # print(total_cash)

    # # 소수점을 올림할 값
    # floating_point_number = 59999 / 40000

    # # 소수점을 올림하여 정수로 만들기
    # rounded_integer = round(floating_point_number)

    # print(f"올림된 정수: {rounded_integer}")

    # time.sleep(1)
# except Exception as e:
#     print(e)
#     time.sleep(1)

# while True:
#     # 현재 시간 가져오기
#     current_time = datetime.now()
    

#     # 시간 간격 계산
#     time_difference = current_time - previous_time

#     # 1분이 지났는지 확인
#     if time_difference >= timedelta(seconds=10):
#         print("1분이 지났습니다.")

#         # 현재 시간을 이전 시간으로 업데이트
#         previous_time = current_time

#     # 결과 출력
#     print("현재 시간:", current_time)
    

# # 로그인
#  upbit = pyupbit.Upbit(access, secret)
# print("autotrade start")
# # 시작 메세지 슬랙 전송
# post_message(myToken,"#crypto", "autotrade start")

# while True:
#     try:
#         now = datetime.datetime.now()
#         start_time = get_start_time("KRW-BTC")
#         end_time = start_time + datetime.timedelta(days=1)

#         if start_time < now < end_time - datetime.timedelta(seconds=10):
#             target_price = get_target_price("KRW-BTC", 0.5)
#             ma15 = get_ma15("KRW-BTC")
#             current_price = get_current_price("KRW-BTC")
#             if target_price < current_price and ma15 < current_price:
#                 krw = get_balance("KRW")
#                 if krw > 5000:
#                     buy_result = upbit.buy_market_order("KRW-BTC", krw*0.9995)
#                     post_message(myToken,"#crypto", "BTC buy : " +str(buy_result))
#         else:
#             btc = get_balance("BTC")
#             if btc > 0.00008:
#                 sell_result = upbit.sell_market_order("KRW-BTC", btc*0.9995)
#                 post_message(myToken,"#crypto", "BTC buy : " +str(sell_result))
#         time.sleep(1)
#     except Exception as e:
#         print(e)
#         post_message(myToken,"#crypto", e)
#         time.sleep(1)