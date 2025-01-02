import time
import pyupbit
from datetime import datetime, timedelta
import datetime
import requests
import pandas as pd

def send_message(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post('https://discord.com/api/webhooks/1200644595919360010/IGX1ctpFUQLHuMchUET2N7qfIkV4VedBfzg3JRppv3SyHAm3v6pV1tGrz-UvLXdnpmBj', data=message)
    print(message)

def send_message_Report(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post('https://discord.com/api/webhooks/1265969591839096935/HH4m0PWkhBhnNf61JhsfHjlw4iPUDeoA5ZEfIKWx35Go2rtX_eJOwSGlcFboReoNUntg', data=message)
    print(message)

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_top_tickers():
    """업비트 현시점 거래대금 상위 6개 티커 가져오기"""
    url_markets = "https://api.upbit.com/v1/market/all"
    url_ticker = "https://api.upbit.com/v1/ticker"

    # 모든 KRW-마켓 티커 가져오기
    markets = requests.get(url_markets).json()
    krw_markets = [market['market'] for market in markets if market['market'].startswith('KRW-')]

    # 실시간 거래 데이터 가져오기
    ticker_data = requests.get(url_ticker, params={"markets": ','.join(krw_markets)}).json()

    # 데이터프레임 생성 및 정렬
    df = pd.DataFrame(ticker_data)
    df = df[['market', 'acc_trade_price_24h']].sort_values(by='acc_trade_price_24h', ascending=False).head(6)
    return df

def update_symbol_list(top_tickers_df, common_data):
    """
    상위 6개 티커 정보를 기반으로 symbol_list 생성
    :param top_tickers_df: 상위 6개 티커 DataFrame
    :param common_data: 공통 데이터
    :return: 갱신된 symbol_list
    """
    symbol_list = {}
    for idx, row in enumerate(top_tickers_df.itertuples(), start=1):
        market = row.market
        symbol_list[market] = {
            '종목명': f"{market.split('-')[-1]} #{idx}",
            '매도티커': market.split('-')[-1],
            **common_data
        }
    return symbol_list

def get_240min_10ma(sym):
    # 240분봉 데이터 가져오기
    data = pyupbit.get_ohlcv(sym, interval="minute240", count=10)
    
    # 데이터가 없으면 None 반환
    if data is None:
        return None
    
    # 20개 이동평균선 계산 (종가 기준)
    average_price_10 = data['close'].mean()
    
    return average_price_10

def get_10min_40ma(sym):
    # 240분봉 데이터 가져오기
    data = pyupbit.get_ohlcv(sym, interval="minute10", count=40)
    
    # 데이터가 없으면 None 반환
    if data is None:
        return None
    
    # 20개 이동평균선 계산 (종가 기준)
    average_price_40 = data['close'].mean()
    
    return average_price_40

###################################################
###################################################
###################################################
# COIN 자동매매 구동
###################################################
###################################################
###################################################
try:
    
    # 로그인
    access = "QBgTbRF0Z3f13iAbzxusZkFu21N7j6M3xfuSsPe3"
    secret = "Kh9Weug6GDkBiT4kLzLdu9jfH7hMntHHs9AZCGVV"
    upbit = pyupbit.Upbit(access, secret)
    send_message("======================")
    send_message("=== 코인거래 초기화 ===")
    send_message("======================")

    last_240 = 77
    last_hour = 77
    last_10 = 77

    last_total_balance_krw = 1
    
    trading_buy = 100000 # 10만원
    trading_sell = 50000 # 5만원

    # 공용 데이터
    common_data ={
    '240': False,
    }

    #개별 코인 데이터
    symbol_list = { 
    'KRW-XRP':{'종목명':'리플 #1', #2
    '매도티커':'XRP',
    **common_data},

    'KRW-BTC':{'종목명':'비트코인 #2', #1
    '매도티커':'BTC',
    **common_data},

    'KRW-DOGE':{'종목명':'도지코인 #3', #5 
    '매도티커':'DOGE',
    **common_data},

    'KRW-SOL':{'종목명':'솔라나 #4', #4
    '매도티커':'SOL',
    **common_data},
    }

    while True:
        
        t_now = datetime.datetime.now()
        
        #########################
        # 1시간 주기 리포팅
        #########################
        if t_now.hour != last_hour:
            last_hour = t_now.hour
            message_list = f"ForeverOn... ({last_hour}시)\n\n"

            # 전체 잔고 가져오기
            balances = upbit.get_balances()

            total_balance_krw = 0
            coin_data = []

            # 각 코인의 현재 가격, 평가금액, 매수평균가 계산
            krw_balance = 0
            for balance in balances:
                coin = balance['currency']
                if coin == "KRW":
                    krw_balance = float(balance['balance'])  # 원화 잔고
                    total_balance_krw += krw_balance
                else:
                    coin_ticker = f"KRW-{coin}"
                    current_price = pyupbit.get_current_price(coin_ticker)  # 현재가
                    if current_price is None:
                        continue
                    
                    amount = float(balance['balance'])  # 보유 수량
                    avg_buy_price = float(balance['avg_buy_price'])  # 매수평균가
                    if avg_buy_price <= 0 : continue

                    total_value = current_price * amount  # 평가금액
                    if total_value < 5000: continue # 소액이면 스킵!
                    profit_rate = ((current_price - avg_buy_price) / avg_buy_price) * 100  # 수익률(%)

                    coin_data.append({
                        "coin": coin,
                        "amount": amount,
                        "current_price": current_price,
                        "avg_buy_price": avg_buy_price,
                        "total_value": total_value,
                        "profit_rate": profit_rate
                    })
                    total_balance_krw += total_value

            # 비중과 수익률 출력
            formatted_amount = 222
            if last_total_balance_krw != 0:
                formatted_amount = "{:,.2f}%".format((total_balance_krw - last_total_balance_krw) / last_total_balance_krw * 100)
            
            temp_money = total_balance_krw-last_total_balance_krw
            last_total_balance_krw = total_balance_krw

            message_list += f"총 보유 자산: {total_balance_krw:,.0f}원 {formatted_amount}({(temp_money):,.0f}원)\n"
            message_list += f"잔여 현금: {krw_balance:,.0f}원\n"
            message_list += "-------------------------------------------------\n"
            for data in coin_data:
                allocation = (data['total_value'] / total_balance_krw) * 100
                message_list += f"{data['coin']}:\n"
                message_list += f"  평가금액: {data['total_value']:,.0f}원\n"
                message_list += f"  수익률: {data['profit_rate']:.2f}%\n"
                message_list += "-------------------------------------------------\n"

            send_message(message_list)

        #########################
        # 240시간 주기 매매
        #########################

        df = pyupbit.get_ohlcv("KRW-BTC", interval="minute240", count=1)
        if df is None: continue

        if df.index[0].hour != last_240:    # 240분 캔들 갱신

            last_240 = df.index[0].hour

            time.sleep(0.2) # 데이터 갱신 보정
            message_list = "\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
            message_list += f">>> 240분 갱신합니다 <<< ({last_240}시)\n\n"

            #########################
            # 240분봉 10선 위/아래 체크
            #########################
            for sym in symbol_list: # 초기화
                                
                # 20일 이평선
                time.sleep(0.2) # 데이터 갱신 보정
                current_price = get_current_price(sym)
                average_price_240_ma = get_240min_10ma(sym)
                
                if current_price >= average_price_240_ma:
                    symbol_list[sym]['240'] = True
                
                else:
                    symbol_list[sym]['240'] = False

                message_list += f"[{symbol_list[sym]['종목명']}] 240선↑ : {symbol_list[sym]['240']}\n"
                 
            send_message(message_list)

        else:
            
            #########################
            # 10분 주기 트레이딩
            #########################
            df = pyupbit.get_ohlcv("KRW-BTC", interval="minute10", count=1)
            if df is None: continue

            if df.index[0].minute != last_10:    # 10분 캔들 갱신
                last_10 = df.index[0].minute

                message_list = "\n---------------------------------------------\n"
                message_list += f">>> 10분 트레이딩 <<< ({last_10}분)\n\n"

                for sym in symbol_list:
                    
                    time.sleep(0.2) # 데이터 갱신 보정

                    # 10분봉 데이터 (최근 10개)
                    data_10 = pyupbit.get_ohlcv(sym, interval="minute10", count=10)
                    if data_10 is None: continue

                    # 직전 캔들 시가와 종가 확인
                    prev_candle = data_10.iloc[-2]  # 직전 캔들
                    open_price = float(prev_candle['open'])
                    close_price = float(prev_candle['close'])
                    average_price_10 = float(data_10['close'].mean()) # 10선 이평선

                    # 평균/직전 거래량
                    data_40 = pyupbit.get_ohlcv(sym, interval="minute10", count=40)
                    if data_40 is None: continue
                    average_volume_40min = float(data_40['volume'].mean())
                    prev_volume = float(data_40.iloc[-2]['volume'])  # 직전 캔들

                    message_list += f"[{symbol_list[sym]['종목명']}]\n"
                    message_list += f"  종가({close_price:,.0f}) / 10선({average_price_10:,.0f})\n"
                    message_list += f"  직전({prev_volume:,.0f}) / 40거래량({average_volume_40min:,.0f})\n"

                    if prev_volume >= average_volume_40min: # 거래량 증가 신호

                        current_price = float(get_current_price(sym))

                        # 매도신호
                        if ((current_price > average_price_10)
                            and (close_price > open_price)
                            and (open_price > average_price_10)): 

                            sell = trading_sell
                            if symbol_list[sym]['240'] == False: # 240 하방이면 2배씩 매도
                                sell *= 2

                            message_list += f"  --- 트레이딩 매도 --- ({sell:,.0f}원) \n\n"

                            sell_quantity = sell / current_price
                            coin = get_balance(symbol_list[sym]['매도티커'])
                            if coin > 0: # 있다면 매도
                                sell_result = upbit.sell_market_order(sym, sell_quantity)
                                if sell_result is not None:
                                    message_list +="!!! 매도 성공 !!!\n\n"  
                                else:
                                    message_list += f"!!! 매도 실패 !!! ({sell_result})\n\n"

                        #매수신호 (240아래 매수안함!!)
                        elif (symbol_list[sym]['240'] == True
                              and (current_price < average_price_10)
                              and (close_price < open_price)
                              and (open_price < average_price_10)): 
                            
                            total_cash = float(get_balance("KRW"))
                            buy = float(trading_buy) # 예산만큼 매수
                            if buy > total_cash:
                                message_list += f"[{symbol_list[sym]['종목명']}] 잔액 부족 매수 (잔액: {total_cash:,.0f})\n"
                                buy = total_cash
                            
                            message_list += f"  +++ 트레이딩 매수 +++ ({buy:,.0f}원) \n\n"

                            buy_result = upbit.buy_market_order(sym, buy)
                            if buy_result is not None:
                                message_list +="+++ 매수 성공 +++\n\n"          
                            else:
                                message_list += f"+++ 매수 실패 +++ ({buy_result})\n\n"

                        else: #나가리
                            message_list += f"+++ 거래량 만족 + (240아래 or 시가/음봉/양봉 실패) +++\n\n"

                send_message(message_list)

                
        # for문 끝 라인..
        time.sleep(10) # 없거나 짧으면 -> [오류 발생]'NoneType' object has no attribute 'index'

except Exception as e:
    print(e)
    
    send_message("#########################################")
    send_message(f"[오류 발생]{e}")
    
    for sym in symbol_list: # 있으면 일괄 매도
        coin = get_balance(symbol_list[sym]['매도티커'])  # 보유량
        if coin > 0: # 있다면 매도
            sell_result = upbit.sell_market_order(sym, coin/2)
            if sell_result is not None:
                send_message(f"[{symbol_list[sym]['종목명']}] 에러 절반 매도")
            else:
                send_message(f"[{symbol_list[sym]['매도티커']}] 매도실패 ({sell_result})")

