import time
import pyupbit
from datetime import datetime, timedelta
import datetime
import requests
import math

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

# COIN 자동매매 구동
try:
    
    # 로그인
    access = "QBgTbRF0Z3f13iAbzxusZkFu21N7j6M3xfuSsPe3"
    secret = "Kh9Weug6GDkBiT4kLzLdu9jfH7hMntHHs9AZCGVV"
    upbit = pyupbit.Upbit(access, secret)
    send_message("=== 코인거래 초기화 ===")

    bStart_buy = False

    last_hour = 77
    last_min = 77

    # buy_money = 1500000.0 # 150만원
    buy_money = 150000.0 # 15만원
    profit_cut = 1.021
    lost_cut = 0.985

    # 공용 데이터
    common_data ={
    '보유': False,
    '시가': 0.0,
    '물량': 0.0,
    '익절': False,
    }

    #개별 종목 데이터
    symbol_list = { 
    'KRW-BTC':{'종목명':'비트코인 #1', #1
    '매도티커':'BTC',
    **common_data},

    'KRW-XRP':{'종목명':'리플 #2', #2
    '매도티커':'XRP',
    **common_data},
    
    'KRW-ETH':{'종목명':'이더리움 #3', #3
    '매도티커':'ETH',
    **common_data},

    'KRW-SOL':{'종목명':'솔라나 #4', #4
    '매도티커':'SOL',
    **common_data},

    'KRW-DOGE':{'종목명':'도지 #5', #5 
    '매도티커':'DOGE',
    **common_data},

    'KRW-USDT':{'종목명':'테더 #6', #6 
    '매도티커':'USDT',
    **common_data},


    }

    while True:
        
        t_now = datetime.datetime.now()
        
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
                    total_value = current_price * amount  # 평가금액
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
            message_list += f"총 보유 자산: {total_balance_krw:,.0f} KRW\n"
            message_list += "-------------------------------------------------\n"
            for data in coin_data:
                allocation = (data['total_value'] / total_balance_krw) * 100
                message_list += "{data['coin']}:\n"
                message_list += "  보유수량: {data['amount']:.6f}\n"
                message_list += "  현재가: {data['current_price']:,.0f} KRW\n"
                message_list += "  매수평균가: {data['avg_buy_price']:,.0f} KRW\n"
                message_list += "  평가금액: {data['total_value']:,.0f} KRW\n"
                message_list += "  비중: {allocation:.2f}%\n"
                message_list += f"  수익률: {data['profit_rate']:.2f}%\n"
                message_list += "-------------------------------------------------"

            send_message(message_list)

        if t_now.hour == 8 : bStart_buy = False
        if t_now.hour == 9 and bStart_buy == False: # 일봉 갱신
            bStart_buy = True

            time.sleep(0.2) # 데이터 갱신 보정

            message_list = "\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
            message_list += f">>> 일봉 갱신합니다 <<< ({t_now.hour}시)\n"
            message_list += "\n>>> "
            

            for sym in symbol_list: # 초기화
                
                # 20일 이평선
                data = pyupbit.get_ohlcv(sym, interval="day", count=20)
                if data is None: continue
                
                average_price_20 = data['close'].mean()
                current_price = get_current_price(sym)

                #########################
                # 있으면 일단 청산
                #########################
                coin = get_balance(symbol_list[sym]['매도티커'])  # 보유량
                if coin > 0:
                    time.sleep(0.02)
                    avg_price = upbit.get_avg_buy_price(sym)
                    sell_result = upbit.sell_market_order(sym, coin)
                    if sell_result is not None:
                        message_list += f"[{symbol_list[sym]['종목명']}] {round(current_price/avg_price*100-100,2)}% 청산 성공\n"
                    else:
                        message_list += f"[{symbol_list[sym]['종목명']}] 청산 실패 ({sell_result})\n"

                #########################
                # 시가 매수 (20선 위)
                #########################
                
                # 초기화
                symbol_list[sym]['보유'] = False
                symbol_list[sym]['시가'] = 0.0
                symbol_list[sym]['물량'] = 0.0
                symbol_list[sym]['익절'] = False

                formatted_amount = "{:,.0f}원".format(current_price)
                formatted_amount1 = "{:,.0f}원".format(average_price_20)

                if current_price >= average_price_20:
                    time.sleep(0.02)
                    # 예산만큼 매수
                    total_cash = get_balance("KRW")
                    if buy_money > total_cash:
                        formatted_amount2 = "{:,.0f}원".format(total_cash)
                        message_list += f"[{symbol_list[sym]['종목명']}] 잔액 부족 (잔액: {formatted_amount2})\n"
                        continue
                    message_list += f"[{symbol_list[sym]['종목명']}] 매수성공 O {formatted_amount} (20선:{formatted_amount1})\n"
                    buy_result = upbit.buy_market_order(sym, buy_money) # 현금
                    if buy_result is not None:
                        symbol_list[sym]['보유'] = True
                        symbol_list[sym]['시가'] = current_price
                        symbol_list[sym]['물량'] = get_balance(symbol_list[sym]['매도티커'])
                        message_list +="+++ 시가 매수 +++\n\n"          
                    else:
                        message_list += f"+++ 실패 +++ ({buy_result})\n\n"
                
                else:
                    message_list += f"[{symbol_list[sym]['종목명']}] 매수실패 X {formatted_amount} (20선:{formatted_amount1})\n"
    

            
                time.sleep(0.02)

                
            message_list += f"===========(시가 매매 완료)=============\n\n\n"         
            send_message(message_list)

        else: # 가지고 있다면
            df = pyupbit.get_ohlcv("KRW-BTC", interval="minute1", count=1)
            if df is None: continue

            if df.index[0].minute != last_min:    # 일봉 갱신
                last_min = df.index[0].minute

                for sym in symbol_list: # 초기화

                    if symbol_list[sym]['보유'] == False:
                        continue
                    
                    time.sleep(0.2) # 데이터 갱신 보정
                    current_price = get_current_price(sym)
                    avg_price = upbit.get_avg_buy_price(sym)

                    #########################
                    # 장중간 조건 매도
                    #########################
                    result = current_price / avg_price

                    if result >= profit_cut and symbol_list[sym]['익절'] == False:

                        symbol_list[sym]['물량'] = symbol_list[sym]['물량'] / 2 # 절반만 익절

                        sell_result = upbit.sell_market_order(sym, symbol_list[sym]['물량'])
                        if sell_result is not None:
                            
                            formatted_amount1 = "{:,.2f}%".format((current_price/avg_price)*100-100)
                            send_message(f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 1/2익절^^")

                        else:
                            send_message(f"익절 실패 ({sell_result})")

                        symbol_list[sym]['익절'] = True

                    elif result <= lost_cut or (symbol_list[sym]['익절'] == True and current_price < symbol_list[sym]['시가']) : #손절
                        
                        sell_result = upbit.sell_market_order(sym, symbol_list[sym]['물량'])
                        if sell_result is not None:
                            
                            formatted_amount1 = "{:,.2f}%".format((current_price/avg_price)*100-100)
                            send_message(f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 손절ㅠ")

                        else:
                            send_message(f"익절 실패 ({sell_result})")

                        symbol_list[sym]['보유'] = False
                        symbol_list[sym]['물량'] = 0.0
            
                
        # for문 끝 라인..

        time.sleep(1) # 없거나 짧으면 -> [오류 발생]'NoneType' object has no attribute 'index'

except Exception as e:
    print(e)
    
    send_message("#########################################")
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

