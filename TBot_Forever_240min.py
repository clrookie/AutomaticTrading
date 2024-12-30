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

def get_240min_20ma(sym):
    # 240분봉 데이터 가져오기
    data = pyupbit.get_ohlcv(sym, interval="minute240", count=20)
    
    # 데이터가 없으면 None 반환
    if data is None:
        return None
    
    # 20개 이동평균선 계산 (종가 기준)
    average_price_20 = data['close'].mean()
    
    return average_price_20

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
    send_message("=== 코인거래 초기화 ===")

    bStart_buy = False

    last_hour = 77
    last_240 = 9
    last_total_balance_krw = 1

    buy_money = 2500000.0 # 150만원
    profit_cut222 = 1.031
    profit_cut555 = 1.061
    profit_cut888 = 1.091
    lost_cut = 0.970

    # 공용 데이터
    common_data ={
    '보유': False,
    '1차익절가': 0.0,
    '물량': 0.0,
    '익절222': False,
    '익절555': False,
    '익절888': False,
    }

    #개별 코인 데이터
    # last_symbol_list = {} # 백업용
    symbol_list = { 
    'KRW-BTC':{'종목명':'비트코인 #1', #1
    '매도티커':'BTC',
    **common_data},

    # 'KRW-ETH':{'종목명':'이더리움 #2', #3
    # '매도티커':'ETH',
    # **common_data},

    # 'KRW-USDT':{'종목명':'테더 #3', #6 
    # '매도티커':'USDT',
    # **common_data},

    'KRW-XRP':{'종목명':'리플 #3', #2
    '매도티커':'XRP',
    **common_data},

    'KRW-SOL':{'종목명':'솔라나 #4', #4
    '매도티커':'SOL',
    **common_data},

    # 'KRW-DOGE':{'종목명':'도지 #5', #5 
    # '매도티커':'DOGE',
    # **common_data},

    # 'KRW-SHIB':{'종목명':'시바이누 #6', #5 
    # '매도티커':'SHIB',
    # **common_data},
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

            # 거래대금 TOP6 잠시 보류 (순환매 돌아올 때 다시?)
            # last_symbol_list = symbol_list
            # common_data ={'보유': False,'시가': 0.0,'물량': 0.0,'익절222': False,'익절555': False,}
            # top_tickers = get_top_tickers()
            # symbol_list = update_symbol_list(top_tickers, common_data)

            #########################
            # 있으면 일단 청산
            #########################
            # for sym in symbol_list: # 초기화
                
            #     # 20일 이평선
            #     time.sleep(0.2) # 데이터 갱신 보정
            #     current_price = get_current_price(sym)
                
            #     coin = get_balance(symbol_list[sym]['매도티커'])  # 보유량
            #     if coin > 0:
            #         time.sleep(0.02)
            #         avg_price = upbit.get_avg_buy_price(sym)
            #         if avg_price <= 0 : continue

            #         sell_result = upbit.sell_market_order(sym, coin)
            #         if sell_result is not None:
            #             message_list += f"[{symbol_list[sym]['종목명']}] {round(current_price/avg_price*100-100,2)}% 청산 매도\n"
            #         else:
            #             message_list += f"[{symbol_list[sym]['종목명']}] 청산 실패 ({sell_result})\n"

            # message_list += f"------(청산 완료)------\n\n" 

            #########################
            # 롤오버 체크 (이익 길게~)
            #########################
            for sym in symbol_list: # 초기화
                
                # 20일 이평선
                time.sleep(0.2) # 데이터 갱신 보정
                current_price = get_current_price(sym)
                coin = get_balance(symbol_list[sym]['매도티커'])  # 보유량

                have = current_price * coin
                if have > 5000:
                    symbol_list[sym]['보유'] = True
                    symbol_list[sym]['물량'] = coin
                    
                    formatted_amount = "{:,.0f}원".format(have)             
                    avg_price = upbit.get_avg_buy_price(sym)
                    message_list += f"[{symbol_list[sym]['종목명']}] 보유중.. {formatted_amount}({round(current_price/avg_price*100-100,2)}%)\n"

            message_list += f"------(보유 체크 완료)------\n\n" 

            #########################
            # 시가 매수 (10선 위)
            #########################
            for sym in symbol_list: # 초기화
                
                if symbol_list[sym]['보유'] == True: # 보유중이면 시가 매수 안함
                    message_list += f"[{symbol_list[sym]['종목명']}] 보유중 매수 스킵..\n"
                    continue
                
                # 20일 이평선
                time.sleep(0.2) # 데이터 갱신 보정
                
                # 초기화
                symbol_list[sym]['보유'] = False
                symbol_list[sym]['1차익절가'] = 0.0
                symbol_list[sym]['물량'] = 0.0
                symbol_list[sym]['익절222'] = False
                symbol_list[sym]['익절555'] = False
                symbol_list[sym]['익절888'] = False
                
                current_price = get_current_price(sym)
                average_price_240_ma = get_240min_10ma(sym)
                formatted_amount = "{:,.0f}원".format(current_price)
                formatted_amount1 = "{:,.0f}원".format(average_price_240_ma)

                # 240분봉 데이터 가져오기 (최근 20봉)
                data = pyupbit.get_ohlcv(sym, interval="minute240", count=20)
                if data is None: continue

                # 직전 캔들의 시가와 종가 확인
                prev_candle = data.iloc[-2]  # 직전 캔들
                open_price = prev_candle['open']
                close_price = prev_candle['close']

                # 양봉/음봉 판별
                stick_plus = False
                if close_price > open_price: # 양봉
                    stick_plus = True

                # 평균/직전 거래량
                average_volume = data['volume'].mean()
                prev_volume = data.iloc[-2]['volume']  # 직전 캔들

                volume_2x = False
                if prev_volume >= (average_volume*2):
                    volume_2x = True

                
                if current_price >= average_price_240_ma:
                    # # 시가 매수 훼피 (직전 + 이평선 위 + 양봉 + 거래량 2배)
                    # if stick_plus and volume_2x:
                    #     message_list += f"\n[{symbol_list[sym]['종목명']}] !!! 매수 훼피 !!! (10선↑+양봉+2배)\n"
                    #     continue

                    time.sleep(0.02)

                    # 예산만큼 매수
                    total_cash = get_balance("KRW")
                    buy = buy_money
                    if buy_money > total_cash:
                        formatted_amount2 = "{:,.0f}원".format(total_cash)
                        message_list += f"[{symbol_list[sym]['종목명']}] 잔액 부족 매수 (잔액: {formatted_amount2})\n"
                        buy = total_cash
                    message_list += f"[{symbol_list[sym]['종목명']}] 매수성공 O {formatted_amount} (10선:{formatted_amount1})\n"
                    buy_result = upbit.buy_market_order(sym, buy) # 현금
                    if buy_result is not None:
                        symbol_list[sym]['보유'] = True
                        symbol_list[sym]['물량'] = get_balance(symbol_list[sym]['매도티커'])
                        message_list +="+++ 시가 매수 +++\n\n"          
                    else:
                        message_list += f"+++ 실패 +++ ({buy_result})\n\n"
                
                else:
                    # 시가 매수 신호 (직전 + 이평선 아래 + 음봉 + 거래량 2배)
                    if stick_plus == False and volume_2x:
                        time.sleep(0.02)

                        # 예산만큼 매수
                        total_cash = get_balance("KRW")
                        buy = buy_money
                        if buy_money > total_cash:
                            formatted_amount2 = "{:,.0f}원".format(total_cash)
                            message_list += f"[{symbol_list[sym]['종목명']}] 잔액 부족 매수 (잔액: {formatted_amount2})\n"
                            buy = total_cash
                        message_list += f"\n[{symbol_list[sym]['종목명']}] @@@ 매수 신호 @@@ (10선↓+음봉+2배)\n"
                        message_list += f"[{symbol_list[sym]['종목명']}] 매수성공 O {formatted_amount} (10선:{formatted_amount1})\n"
                        buy_result = upbit.buy_market_order(sym, buy) # 현금
                        if buy_result is not None:
                            symbol_list[sym]['보유'] = True
                            symbol_list[sym]['물량'] = get_balance(symbol_list[sym]['매도티커'])
                            message_list +="+++ 시가 매수 +++\n\n"          
                        else:
                            message_list += f"+++ 실패 +++ ({buy_result})\n\n"
                    else:
                        message_list += f"[{symbol_list[sym]['종목명']}] 매수실패 X {formatted_amount} (10선:{formatted_amount1})\n"

                
            message_list += f"\n===========(시가 매매 완료)=============\n\n\n"    
            send_message(message_list)

        else: # 가지고 있다면
            
            for sym in symbol_list: # 초기화

                if symbol_list[sym]['보유'] == False:
                    
                    # # 청산 이후 시가 위를 넘어설 때
                    # if symbol_list[sym]['청산'] == True and (symbol_list[sym]['시가'] < get_current_price(sym)):

                    #     time.sleep(0.02)
                    #     current_price = get_current_price(sym)

                    #     # 예산만큼 매수
                    #     total_cash = get_balance("KRW")
                    #     buy = buy_money
                    #     if buy_money > total_cash:
                    #         formatted_amount2 = "{:,.0f}원".format(total_cash)
                    #         message_list += f"[{symbol_list[sym]['종목명']}] 잔액 부족 매수 (잔액: {formatted_amount2})\n"
                    #         buy = total_cash
                    #     message_list += f"[\n{symbol_list[sym]['종목명']}] ### 청산후 시가 재매수 ###\n"
                    #     buy_result = upbit.buy_market_order(sym, buy) # 현금
                    #     if buy_result is not None:
                    #         symbol_list[sym]['보유'] = True
                    #         symbol_list[sym]['청산'] == False
                    #         symbol_list[sym]['물량'] = get_balance(symbol_list[sym]['매도티커'])
                    #         message_list +="+++ 매수 성공 +++\n\n"          
                    #     else:
                    #         message_list += f"+++ 매수 실패 +++ ({buy_result})\n\n"

                    continue
                
                time.sleep(0.2) # 데이터 갱신 보정
                current_price = get_current_price(sym)
                avg_price = upbit.get_avg_buy_price(sym)
                if avg_price <= 0 : continue

                #########################
                # 장중간 조건 매도
                #########################
                result = current_price / avg_price

                # 2% 익절
                if result >= profit_cut222 and symbol_list[sym]['익절222'] == False:

                    sell = symbol_list[sym]['물량'] / 3 # 33% 
                    symbol_list[sym]['물량'] = symbol_list[sym]['물량'] - sell

                    sell_result = upbit.sell_market_order(sym, sell)
                    if sell_result is not None:
                        
                        formatted_amount1 = "{:,.2f}%".format((current_price/avg_price)*100-100)
                        send_message(f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 1차 익절^^")
            
                        symbol_list[sym]['익절222'] = True
                        symbol_list[sym]['1차익절가'] = current_price

                    else:
                        send_message(f"1차 익절 실패 ({sell_result})")


                # 5% 익절
                elif result >= profit_cut555 and symbol_list[sym]['익절555'] == False:

                    symbol_list[sym]['물량'] = symbol_list[sym]['물량'] / 2 # 33% 익절

                    sell_result = upbit.sell_market_order(sym, symbol_list[sym]['물량'])
                    if sell_result is not None:
                        
                        formatted_amount1 = "{:,.2f}%".format((current_price/avg_price)*100-100)
                        send_message(f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 2차 익절^^")
                        
                        symbol_list[sym]['익절555'] = True

                    else:
                        send_message(f"2차 익절 실패 ({sell_result})")


                # 8% 청산 익절
                elif result >= profit_cut888 and symbol_list[sym]['익절888'] == False:

                    sell_result = upbit.sell_market_order(sym, symbol_list[sym]['물량'])
                    if sell_result is not None:
                        
                        formatted_amount1 = "{:,.2f}%".format((current_price/avg_price)*100-100)
                        send_message(f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 청산 익절^^")
                        
                        symbol_list[sym]['보유'] = False
                        symbol_list[sym]['물량'] = 0.0
                        symbol_list[sym]['익절888'] = True

                    else:
                        send_message(f"청산 익절 실패 ({sell_result})")


                # 청산 손절 처리 ##############
                elif (result <= lost_cut
                    or (symbol_list[sym]['익절222'] == True and current_price < avg_price)
                    or (symbol_list[sym]['익절555'] == True and current_price < symbol_list[sym]['1차익절가'])):
                    
                    sell_result = upbit.sell_market_order(sym, symbol_list[sym]['물량'])
                    if sell_result is not None:
                        
                        formatted_amount1 = "{:,.2f}%".format((current_price/avg_price)*100-100)
                        send_message(f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 청산 손절ㅠ")
                        
                        symbol_list[sym]['보유'] = False
                        symbol_list[sym]['물량'] = 0.0

                    else:
                        send_message(f"손절 실패 ({sell_result})")

                
        # for문 끝 라인..
        time.sleep(10) # 없거나 짧으면 -> [오류 발생]'NoneType' object has no attribute 'index'

except Exception as e:
    print(e)
    
    send_message("#########################################")
    send_message(f"[오류 발생]{e}")
    
    for sym in symbol_list: # 있으면 일괄 매도
        coin = get_balance(symbol_list[sym]['매도티커'])  # 보유량
        if coin > 0: # 있다면 매도
            sell_result = upbit.sell_market_order(sym, coin)
            if sell_result is not None:
                send_message(f"[{symbol_list[sym]['종목명']}] 에러 전량 매도")
            else:
                send_message(f"[{symbol_list[sym]['매도티커']}] 매도실패 ({sell_result})")

