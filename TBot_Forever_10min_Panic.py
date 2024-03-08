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
    send_message("")
    send_message("======================")
    send_message("=== 코인거래 초기화 ===")
    send_message("======================")

    last_min = 77
    
    # 기준 거래량 비율
    volume_rate = 2
    
    # 매수
    allotment_budget = 1000000
    buy_rate = 0.2


    # 공용 데이터
    common_data ={
    '잔여예산':0,
    '공포적립': 0,
    }

    #개별 종목 데이터
    symbol_list = { 
    'KRW-BTC':{'종목명':'비트코인 #1', #1
    '매도티커':'BTC',
    **common_data},

    'KRW-ETH':{'종목명':'이더리움 #2', #2
    '매도티커':'ETH',
    **common_data},

    'KRW-SOL':{'종목명':'솔라나 #3', #2
    '매도티커':'SOL',
    **common_data},

    'KRW-XRP':{'종목명':'리플 #4', #3 
    '매도티커':'XRP',
    **common_data},

    'KRW-ADA':{'종목명':'에이다 #5', #3 
    '매도티커':'ADA',
    **common_data},
    }


    while True:
        
        df = pyupbit.get_ohlcv("KRW-BTC", interval="minute10", count=1)    
    

        if df.index[0].minute != last_min:    # 10분 캔들 갱신

            last_min = df.index[0].minute

            message_list = ""
            message_list += f">>> 코인거래 10분봉 갱신합니다 <<< ({last_min}분)\n"
            message_list += "\n"

            # target_buy_count = int(len(symbol_list)) # 매수종목 수량

            total_cash = get_balance("KRW") # 현금잔고 조회
            
            formatted_amount = "{:,.0f}원".format(total_cash)
            message_list += f"현금잔고: {formatted_amount}\n"

            formatted_amount = "{:,.0f}원".format(allotment_budget)
            formatted_amount1 = "{:,.0f}원".format(allotment_budget * buy_rate)
            message_list += f"기준예산: {formatted_amount} (분할매수 {formatted_amount1}) \n"
            message_list += "-----------\n\n"
            
            for sym in symbol_list: # 초기화
                
                temp = 0

                message_list += f"[{symbol_list[sym]['종목명']}]\n"
                
                current_price = get_current_price(sym)
                
                formatted_amount = "{:,.0f}원".format(current_price)
                message_list += f"현재가: {formatted_amount}\n"

                qty = get_balance(symbol_list[sym]['매도티커'])
                current_total = current_price * qty

                if current_total >= 5000: # 최소 주문 가격 이상일 때

                    # 공포적립,잔여예산 초기화
                    symbol_list[sym]['공포적립'] = round(current_total / (allotment_budget * buy_rate))
                    symbol_list[sym]['잔여예산'] = allotment_budget - ((allotment_budget * buy_rate) * symbol_list[sym]['공포적립'])
                    if symbol_list[sym]['잔여예산'] < 0: symbol_list[sym]['잔여예산'] = 0

                    avg_price = upbit.get_avg_buy_price(sym)
                    formatted_amount = "{:,.1f}원".format(avg_price)
                    formatted_amount1 = "{:,.1f}%".format(current_price/avg_price*100)
                    message_list += f"평단가: {formatted_amount} ({formatted_amount1})\n"
                    
                    temp = current_price * qty
                    formatted_amount = "{:,.0f}원".format(temp)
                    message_list += f"보유 잔고: {formatted_amount} (수량 {qty}개) \n"

                    total_cash += temp
                else:
                    symbol_list[sym]['공포적립'] = 0
                    symbol_list[sym]['잔여예산'] = allotment_budget

                message_list += f"공포 적립: {symbol_list[sym]['공포적립']}개\n"
                formatted_amount = "{:,.0f}원".format(symbol_list[sym]['잔여예산'])
                message_list += f"잔여 예산: {formatted_amount}\n\n"

                # 10분봉 데이터 가져오기 (최근 20봉)
                data = pyupbit.get_ohlcv(sym, interval="minute10", count=20)
                   
                time.sleep(0.02)

                # 최근 60봉
                # data_60 = pyupbit.get_ohlcv(sym, interval="minute10", count=60)
                # average_price_60 = 0

                # if data_60 is not None:
                #     average_price_60 = data_60['close'].mean()

                #     time.sleep(0.02)

                # else:
                #     message_list += "60 이평선 실패 !! \n"
                #     continue

                # 최근 120봉
                data_120 = pyupbit.get_ohlcv(sym, interval="minute10", count=120)
                average_price_120 = 0

                if data_120 is not None:
                    average_price_120 = data_120['close'].mean()
                else:
                    message_list += "120 이평선 실패 !! \n"
                    continue
                
                

                

                # 평균 거래량 계산
                average_volume = data['volume'].mean()
                formatted_amount = "{:,.0f}".format(average_volume)
                message_list += f"평균: {formatted_amount} | "

                # 직전 거래량
                last_volume = data.iloc[18]['volume']
                avg = (last_volume / average_volume) * 100
                formatted_amount1 = "{:,.0f}".format(last_volume)
                formatted_amount2 = "{:,.0f}".format(avg)
                message_list += f"직전: {formatted_amount1} ({formatted_amount2}%)\n"

                # 직전 차트
                last_open = data.iloc[18]['open']
                last_close = data.iloc[18]['close']
                last_high = data.iloc[18]['high']
                last_low = data.iloc[18]['low']

                # 거래량 변동성 신호
                if last_volume > (average_volume*volume_rate):
                    
                    message_list += "\n>>>>>>>>>>>> !-!-!-! 변동성 발생 !-!-!-! <<<<<<<<<<<<<\n\n"

                    # 고가 120 이평선 위에
                    if last_high > average_price_120:

                        # 양봉이니?
                        if last_open < last_close:

                            # 탐욕 매도
                            if symbol_list[sym]['공포적립'] > 0:

                                sell_qty = qty / symbol_list[sym]['공포적립']

                                sell_result = upbit.sell_market_order(sym, sell_qty)
                                if sell_result is not None:
                                    
                                    message_list += "(--- 탐욕 매도 ---)\n\n"
                                    symbol_list[sym]['공포적립'] -= 1
                                    avg_price = upbit.get_avg_buy_price(sym)
                                    message_list += f"{round(current_price/avg_price,4)}% 탐욕 매도합니다 ^^ ({sell_qty}개)\n"


                                    qty = get_balance(symbol_list[sym]['매도티커'])
                                    current_total = current_price * qty
                                    
                                    message_list += f"갱신 보유 수량: {qty}개\n"

                                    total = current_price * qty
                                    formatted_amount = "{:,.0f}원".format(total)
                                    message_list += f"갱신 보유 잔고: {formatted_amount}\n"

                                    total_cash -= temp
                                    total_cash += total

                                    message_list += f"공포 적립 변화 : {symbol_list[sym]['공포적립']+1} -> {symbol_list[sym]['공포적립']}개)\n"
                                else:
                                    message_list += f"탐욕 매도 실패 ({sell_result})\n"
                            else:
                                message_list += "공포 적립이 없습니다 ㅠ\n"


                        else: # 음봉
                            message_list += "120 위 + '음봉' 나가리~\n"

                    # 저가 120 이평선 아래        
                    elif last_low < average_price_120:
                        # 음봉이니?
                        if last_open > last_close: 

                            # 잔여예산 있니?
                            if symbol_list[sym]['잔여예산'] >= (allotment_budget * buy_rate):                            

                                price = allotment_budget * buy_rate
                                if price < 5000: price = 5000 # 최소 주문량

                                # 공포 매수
                                buy_result = upbit.buy_market_order(sym, price) # 현금
                                if buy_result is not None:          
                                    
                                    message_list += "(+++ 공포 매수 +++)\n\n"
                                    symbol_list[sym]['공포적립'] += 1
                                    
                                    avg_price = upbit.get_avg_buy_price(sym)
                                    formatted_amount = "{:,.1f}원".format(avg_price)
                                    formatted_amount1 = "{:,.1f}%".format(current_price/avg_price*100)
                                    message_list += f"갱신 평단가: {formatted_amount} ({formatted_amount1})\n"  
                                    
                                    qty = get_balance(symbol_list[sym]['매도티커'])
                                    current_total = current_price * qty
                                    
                                    message_list += f"갱신 보유 수량: {qty}개\n"

                                    total = current_price * qty
                                    formatted_amount = "{:,.0f}원".format(total)
                                    message_list += f"갱신 보유 잔고: {formatted_amount}\n"

                                    total_cash -= temp
                                    total_cash += total

                                    message_list += f"공포 적립 변화 : {symbol_list[sym]['공포적립']-1} -> {symbol_list[sym]['공포적립']}개)\n"                         

                                else:
                                    message_list += f"공포 매수 실패 ({buy_result})\n"
                            else:
                                message_list += "잔여 예산이 고갈 됐습니다 ㅠ\n"

                        else: # 양봉
                            message_list += "120 아래 + '양봉' 나가리~\n"
                             

                message_list += "---------------------------------\n\n"
            
            formatted_amount = "{:,.0f}원".format(total_cash)
            message_list += f"\n총 보유 잔고: {formatted_amount}\n\n"

            send_message(message_list)
                          

        # for문 끝 라인..
                                
        time.sleep(0.2)

except Exception as e:
    print(e)
    send_message(f"[오류 발생]{e}")

    time.sleep(1)
