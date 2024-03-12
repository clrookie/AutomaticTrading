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
    
    #원금
    principal = 5200000
    
    # 기준 거래량 비율
    panic_volume_rate = 2
    panic_volume_rate_max = 3
    greed_volume_rate = 1.1
    
    # 매수
    allotment_budget = 1000000
    buy_rate = 0.05


    # 공용 데이터
    common_data ={
    '잔여예산': 0,
    '공포적립': 0,
    'total': 0,
    '공포에너지': 0,
    '탐욕에너지': 0,
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

            time.sleep(0.02) # 데이터 갱신 보정

            last_min = df.index[0].minute

            message_list = "\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
            message_list += f"\n>>> 코인거래 10분봉 갱신합니다 <<< ({last_min}분)\n"
            message_list += "\n"

            total = 0
            
            formatted_amount = "{:,.0f}원".format(allotment_budget)
            formatted_amount1 = "{:,.0f}원".format(allotment_budget * buy_rate)
            message_list += f"배분 예산: {formatted_amount} (분할 {formatted_amount1}) \n"
            message_list += f"공포 거래량: {panic_volume_rate}배 (패닉: {panic_volume_rate_max}배) / 탐욕 거래량: {greed_volume_rate}배 \n"
            message_list += "-----------\n\n"
            
            for sym in symbol_list: # 초기화

                message_list += f"[{symbol_list[sym]['종목명']}]\n"
                
                current_price = get_current_price(sym)
                
                formatted_amount = "{:,.0f}원".format(current_price)
                message_list += f"현재: {formatted_amount} / "

                qty = get_balance(symbol_list[sym]['매도티커'])
                symbol_list[sym]['total'] = current_price * qty

                if symbol_list[sym]['total'] >= 5000: # 최소 주문 가격 이상일 때

                    # 공포적립,잔여예산 초기화
                    symbol_list[sym]['공포적립'] = round(symbol_list[sym]['total'] / (allotment_budget * buy_rate))
                    symbol_list[sym]['잔여예산'] = allotment_budget - ((allotment_budget * buy_rate) * symbol_list[sym]['공포적립'])
                    if symbol_list[sym]['잔여예산'] < 0: symbol_list[sym]['잔여예산'] = 0

                    time.sleep(0.02)
                    avg_price = upbit.get_avg_buy_price(sym)

                    formatted_amount = "{:,.1f}원".format(avg_price)
                    formatted_amount1 = "{:,.1f}%".format(current_price/avg_price*100)
                    message_list += f"평단: {formatted_amount} ({formatted_amount1})\n"
                    
                    formatted_amount = "{:,.0f}원".format(symbol_list[sym]['total'])
                    message_list += f"보유 잔고: {formatted_amount}\n"

                else:
                    symbol_list[sym]['공포적립'] = 0
                    symbol_list[sym]['잔여예산'] = allotment_budget

                message_list += f"공포 적립: {symbol_list[sym]['공포적립']}개"
                formatted_amount = "{:,.0f}원".format(symbol_list[sym]['잔여예산'])
                message_list += f" (예산: {formatted_amount})\n\n"

                
                average_price_20 = 0
                average_price_60 = 0
                average_price_120 = 0

                # 10분봉 데이터 가져오기 (최근 20봉)
                data = pyupbit.get_ohlcv(sym, interval="minute10", count=20)

                if data is not None:
                    average_price_20 = data['close'].mean()
                    time.sleep(0.02)

                    # 최근 60봉
                    data_60 = pyupbit.get_ohlcv(sym, interval="minute10", count=60)

                    if data_60 is not None:
                        average_price_60 = data_60['close'].mean()
                        time.sleep(0.02)

                        # 최근 120봉
                        data_120 = pyupbit.get_ohlcv(sym, interval="minute10", count=120)

                        if data_120 is not None:
                            average_price_120 = data_120['close'].mean()
                        else:
                            message_list += "120 이평선 실패 !! \n"
                            continue
                    else:
                        message_list += "60 이평선 실패 !! \n"
                        continue

                else:
                    message_list += "20 이평선 실패 !! \n"
                    continue
                   
                time.sleep(0.02)
                

                # 평균 거래량 계산
                average_volume = data['volume'].mean()
                formatted_amount = "{:,.0f}".format(average_volume)
                message_list += f"평균: {formatted_amount} | "

                # 직전 거래량
                last_volume = data.iloc[18]['volume']

                avg = (last_volume / average_volume) * 100
                formatted_amount1 = "{:,.0f}".format(last_volume)
                formatted_amount2 = "{:,.0f}".format(avg)
                message_list += f"직전: {formatted_amount1} [{formatted_amount2}%]"

                # 직전 차트
                last_open = data.iloc[18]['open']
                last_close = data.iloc[18]['close']
                last_high = data.iloc[18]['high']
                last_low = data.iloc[18]['low']

                

                # 시가 120 이평선 위에
                if symbol_list[sym]['공포적립'] > 0 and last_open > average_price_20 and last_open > average_price_60 and last_open > average_price_120:

                    # 거래량 변동성 신호
                    if last_volume > (average_volume*greed_volume_rate):
                    
                        message_list += "\n\n(--- 탐욕 지급 --- 탐욕 지급 --- 탐욕 지급 --- 탐욕 지급 ---)\n"

                        # 양봉이니?
                        if last_open < last_close:
                            

                            sell_qty = qty / symbol_list[sym]['공포적립']

                            time.sleep(0.02)
                            avg_price = upbit.get_avg_buy_price(sym)

                            time.sleep(0.02)
                            sell_result = upbit.sell_market_order(sym, sell_qty)
                            if sell_result is not None:
                                
                                symbol_list[sym]['공포적립'] -= 1
                                message_list += f"{round(current_price/avg_price,4)}% 탐욕 매도합니다 ^^ ({sell_qty}개)\n"

                                time.sleep(0.02)
                                qty = get_balance(symbol_list[sym]['매도티커'])

                                symbol_list[sym]['total'] = current_price * qty
                                formatted_amount = "{:,.0f}원".format(symbol_list[sym]['total'])
                                message_list += f"공포 예탁 변화 : {symbol_list[sym]['공포적립']+1} -> {symbol_list[sym]['공포적립']}개\n"
                                message_list += f"갱신 보유 잔고: {formatted_amount}\n"
                            else:
                                message_list += f"탐욕 매도 실패 ({sell_result})\n"

                        else: # 음봉
                            message_list += "20 60 120 위 ↑↑↑↑ '음봉' 나가리~\n"
                    else: # 변동성 조건 미달
                            message_list += " - 탐욕구간\n"

                # 저가 120 이평선 아래        
                elif symbol_list[sym]['잔여예산'] >= (allotment_budget * buy_rate) and last_open < average_price_20 and last_open < average_price_60 and last_open < average_price_120:

                    # 거래량 변동성 신호
                    if last_volume > (average_volume*panic_volume_rate):
                    
                        message_list += "\n\n(+++ 공포 예탁 +++ 공포 예탁 +++ 공포 예탁 +++ 공포 예탁 +++ )\n"

                        # 음봉이니?
                        if last_open > last_close: 
                            
                            # 과공포 상태니?
                            if last_volume > (average_volume*panic_volume_rate_max) and symbol_list[sym]['잔여예산'] >= (allotment_budget * buy_rate * 2):
                                price = allotment_budget * buy_rate * 2
                                message_list += "!!! 과공포 x2 예탁 !!! \n"
                            else:
                                price = allotment_budget * buy_rate
                                if price < 5000: price = 5000 # 최소 주문량

                            # 공포 매수
                            buy_result = upbit.buy_market_order(sym, price) # 현금
                            if buy_result is not None:          
                                
                                symbol_list[sym]['공포적립'] += 1
                                
                                time.sleep(0.02)                                    
                                qty = get_balance(symbol_list[sym]['매도티커'])

                                symbol_list[sym]['total'] = current_price * qty
                                formatted_amount = "{:,.0f}원".format(symbol_list[sym]['total'])
                                message_list += f"공포 예탁 변화 : {symbol_list[sym]['공포적립']-1} -> {symbol_list[sym]['공포적립']}개\n"   
                                message_list += f"갱신 보유 잔고: {formatted_amount}\n"                      

                            else:
                                message_list += f"공포 매수 실패 ({buy_result})\n"

                        else: # 양봉
                            message_list += "20 60 120 아래 ↓↓↓↓ '양봉' 나가리~\n"
                    else: # 변동성 조건 미달
                            message_list += " - 공포구간\n"


                total += symbol_list[sym]['total']
                message_list += "\n-----------------------------------------------\n\n"
            

            total_cash = get_balance("KRW") # 현금잔고 조회
            formatted_amount = "{:,.0f}원".format(total_cash)
            message_list += f"현금 잔고: {formatted_amount}\n"
            
            formatted_amount = "{:,.0f}원".format(total)
            message_list += f"주식 잔고: {formatted_amount}\n"

            result_rate = ((total_cash+total) / principal * 100)-100
            formatted_amount = "{:,.0f}원".format(total_cash+total)
            formatted_amount1 = "{:,.2f}%".format(result_rate)
            message_list += f"총 보유 잔고: {formatted_amount} ({formatted_amount1})"

            send_message(message_list)
                          
        # for문 끝 라인..
        
        time.sleep(1) # 없거나 짧으면 -> [오류 발생]'NoneType' object has no attribute 'index'

except Exception as e:
    print(e)
    send_message(f"[오류 발생]{e}")

