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
    send_message("=== 코인거래 초기화 ===")

    last_min = 77
    last_result = 0
    more_last_result = 0
    
    #원금
    principal = 10000000
    result_rate = 0
    result_max = 0
    lostcut = 3
    
    # 기준 거래량 비율
    panic_volume_rate = 3
    greed_volume_rate = 1
    
    # 매수
    allotment_budget = 10000000
    division = 1000
    buy_rate = allotment_budget / division #만원씩 거래

    panic_count = 5
    panic_leverage = 5
    greed_leverage = 3.5


    # 공용 데이터
    common_data ={
    '잔여예산': 0,
    '공포적립': 0,
    'total': 0,
    '공포에너지': 0,
    '탐욕에너지': 0,
    '전전거래량':0,
    }

    #개별 종목 데이터
    symbol_list = { 
    'KRW-BTC':{'종목명':'비트코인',
    '매도티커':'BTC',
    **common_data},
    
    }


    while True:
        
        df = pyupbit.get_ohlcv("KRW-BTC", interval="minute1", count=1)
        if df is None: continue

        if df.index[0].minute != last_min:    # 10분 캔들 갱신

            time.sleep(0.2) # 데이터 갱신 보정

            last_min = df.index[0].minute

            message_list = "\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
            message_list += f">>> 1분봉 갱신합니다 <<< ({last_min}분) ({last_min}분) ({last_min}분) ({last_min}분) ({last_min}분)\n"
            message_list += "\n>>> "

            total = 0
            
            formatted_amount = "{:,.0f}원".format(allotment_budget)
            formatted_amount1 = "{:,.0f}원".format(buy_rate)
            formatted_amount2 = "{:,.2f}%".format(result_max - lostcut)
            message_list += f"배분: {formatted_amount} (단위 {formatted_amount1}), 로스컷 {formatted_amount2} \n"
            message_list += f"공포량: {panic_volume_rate}배 / 탐욕량: {greed_volume_rate}배 / 레버리지(예치{panic_leverage}배, 지급{greed_leverage}배) \n\n"
            message_list += "------------------------------------------\n"

            for sym in symbol_list: # 초기화
                
                message_list += f"[{symbol_list[sym]['종목명']}]"
                
                current_price = get_current_price(sym)
                qty = get_balance(symbol_list[sym]['매도티커'])

                symbol_list[sym]['total'] = current_price * qty

                if symbol_list[sym]['total'] >= buy_rate: # 최소 주문 가격 이상일 때

                    # 잔여예산 초기화
                    symbol_list[sym]['잔여예산'] = allotment_budget - symbol_list[sym]['total']
                    if symbol_list[sym]['잔여예산'] < 0: symbol_list[sym]['잔여예산'] = 0

                    time.sleep(0.02)
                    avg_price = upbit.get_avg_buy_price(sym)

                    formatted_amount = "{:,.0f}원".format(symbol_list[sym]['total'])
                    formatted_amount1 = "{:,.1f}%".format(current_price/avg_price*100)
                    message_list += f" {formatted_amount} ({formatted_amount1})"

                else:
                    symbol_list[sym]['잔여예산'] = allotment_budget

                
                average_price_20 = 0
                average_price_60 = 0
                average_price_120 = 0

                # 10분봉 데이터 가져오기 (최근 20봉)
                data = pyupbit.get_ohlcv(sym, interval="minute1", count=20)
                if data is None: continue

                last_volume = data.iloc[18]['volume']
                if symbol_list[sym]['전전거래량'] == last_volume: # 거래량 갱신 안됨
                    
                    time.sleep(1)
                    data = pyupbit.get_ohlcv(sym, interval="minute1", count=20)
                    if data is None: continue

                    last_volume = data.iloc[18]['volume']
                    
                    if symbol_list[sym]['전전거래량'] == last_volume:
                        message_list += f"\n {sym} 거래량 갱신 실패 0 세팅 !!!\n"
                        last_volume = 0
                else:
                    symbol_list[sym]['전전거래량'] = last_volume

                if data is not None:
                    average_price_20 = data['close'].mean()
                    time.sleep(0.02)

                    # 최근 60봉
                    data_60 = pyupbit.get_ohlcv(sym, interval="minute1", count=60)

                    if data_60 is not None:
                        average_price_60 = data_60['close'].mean()
                        time.sleep(0.02)

                        # 최근 120봉
                        data_120 = pyupbit.get_ohlcv(sym, interval="minute1", count=120)

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
                
                formatted_amount3 = "{:,.0f}원".format(current_price*average_volume)
                formatted_amount4 = "{:,.0f}원".format(current_price*last_volume)
                avg1 = (current_price*last_volume) / (current_price*average_volume) * 100
                formatted_amount5 = "{:,.0f}%".format(avg1)
                message_list += f"\n\n평균: {formatted_amount3} | 직전: {formatted_amount4} [{formatted_amount5}]"

                # 직전 차트
                last_open = data.iloc[18]['open']
                last_close = data.iloc[18]['close']
                last_high = data.iloc[18]['high']
                last_low = data.iloc[18]['low']

                # 시가 120 이평선 위에
                if symbol_list[sym]['total'] >= buy_rate and last_open > average_price_20 and last_open > average_price_60 and last_open > average_price_120:

                    symbol_list[sym]['공포에너지'] = 0

                    # 거래량 변동성 신호
                    if last_volume > (average_volume*greed_volume_rate):
                                           
                        # 양봉이니?
                        if last_open <= last_close:
                            
                            message_list += "\n\n--- 탐욕 지급 --- 탐욕 지급 --- 탐욕 지급 --- 탐욕 지급 ---\n"

                            r_last_volume = round((current_price*last_volume)/buy_rate)
                            r_last_volume *= greed_leverage # 레버리지 5배

                            formatted_amount = "{:,.0f}원".format(r_last_volume)
                            message_list += f"!! {formatted_amount} 지급 !! \n"

                            sell_qty = r_last_volume / current_price
                            if sell_qty > qty: sell_qty = qty

                            time.sleep(0.02)
                            avg_price = upbit.get_avg_buy_price(sym)

                            time.sleep(0.02)
                            sell_result = upbit.sell_market_order(sym, sell_qty)
                            if sell_result is not None:
                                
                                message_list += f"{round(current_price/avg_price,6)}% 탐욕 매도합니다 ^^\n"

                                time.sleep(0.02)
                                qty = get_balance(symbol_list[sym]['매도티커'])

                                symbol_list[sym]['total'] = current_price * qty
                                formatted_amount = "{:,.0f}원".format(symbol_list[sym]['total'])
                                message_list += f"갱신: {formatted_amount}\n"
                            else:
                                message_list += f"탐욕 매도 실패 ({sell_result})\n"

                        else: # 음봉
                            message_list += "\n20 60 120 ↑↑↑↑ '음봉' 나가리~\n"
                    else: # 변동성 조건 미달
                            message_list += " - 탐욕구간"

                # 저가 120 이평선 아래        
                elif symbol_list[sym]['잔여예산'] >= buy_rate and last_open < average_price_20 and last_open < average_price_60 and last_open < average_price_120:

                    # 음봉이니?
                    if last_open >= last_close:
                    
                        symbol_list[sym]['공포에너지'] += 1
                        
                        message_list += f" - 공포구간({symbol_list[sym]['공포에너지']})"

                        # 거래량 변동성 신호
                        if symbol_list[sym]['공포에너지'] >= panic_count and last_volume > (average_volume*panic_volume_rate): # 공포에너지 체크 때문에 거래량 여기서 체크

                            price = 0
                            message_list += "\n\n+++ 공포 예치 +++ 공포 예치 +++ 공포 예치 +++ 공포 예치 +++\n"

                            r_last_volume = round((current_price*last_volume)/buy_rate)
                            r_last_volume *= panic_leverage # 레버리지 5배

                            formatted_amount = "{:,.0f}원".format(r_last_volume)
                            message_list += f"!! {formatted_amount} 예치 !! \n"
                            
                            if symbol_list[sym]['잔여예산'] >= r_last_volume:                               
                                price = r_last_volume
                            else : price = symbol_list[sym]['잔여예산']

                            # 공포 매수
                            buy_result = upbit.buy_market_order(sym, price) # 현금
                            if buy_result is not None:          
                                
                                time.sleep(0.02)                                    
                                qty = get_balance(symbol_list[sym]['매도티커'])

                                symbol_list[sym]['total'] = current_price * qty
                                formatted_amount = "{:,.0f}원".format(symbol_list[sym]['total']) 
                                message_list += f"갱신: {formatted_amount}\n"                      
                            else:
                                message_list += f"공포 매수 실패 ({buy_result})\n"

                    else: # 양봉
                        message_list += " - 공포구간 '양봉'\n"
                else:
                    symbol_list[sym]['공포에너지'] = 0
                    message_list += " - 관망중..'\n"

                total += symbol_list[sym]['total']
                message_list += "\n\n------------------------------------------\n"
                
            
            
            message_list += f"\n===========({last_min}분)===========\n"

            total_cash = get_balance("KRW") # 현금잔고 조회

            formatted_amount = "{:,.2f}%".format(total/(total_cash+total)*100)
            message_list += f"코인 비중: {formatted_amount}\n"

            formatted_amount = "{:,.0f}원".format(total_cash+total)
            message_list += f"총 잔고: {formatted_amount} "

            formatted_amount = "{:,.0f}원".format(total_cash)
            message_list += f"(현금 {formatted_amount}, "
            formatted_amount = "{:,.0f}원".format(total)
            message_list += f"코인 {formatted_amount})\n"

            result_rate = ((total_cash+total) / principal * 100) - 100

            formatted_amount0 = "{:,.0f}원".format((total_cash+total)-principal)
            formatted_amount1 = "{:,.2f}%".format(more_last_result)
            formatted_amount2 = "{:,.2f}%".format(last_result)
            formatted_amount3 = "{:,.2f}%".format(result_rate)
            message_list += f"총 수익율: {formatted_amount0} ({formatted_amount1} > {formatted_amount2} > '{formatted_amount3}')"
            
            more_last_result = last_result
            last_result = result_rate
            if result_max < result_rate: result_max = result_rate # 최고 수익율 기록

            message_list += f"\n===========({last_min}분)===========\n\n\n"
            send_message(message_list)
                          
        # for문 끝 라인..

        if result_rate < (result_max - lostcut): #사이드브레이크
            result_max = result_rate
            for sym in symbol_list: # 있으면 일괄 매도
                coin = get_balance(symbol_list[sym]['매도티커'])  # 보유량
                if coin > 0: # 있다면 매도
                    sell_result = upbit.sell_market_order(sym, coin)
                    if sell_result is not None:
                        send_message(f"[{symbol_list[sym]['종목명']}] {coin} 전량 매도했습니다~")
                    else:
                        send_message(f"[{symbol_list[sym]['매도티커']}] 매도실패 ({sell_result})")
            
            formatted_amount = "{:,.2f}%".format(result_rate)
            send_message(f"총 수익율 {formatted_amount} 도달로 자동매매를 일시 중지하고 12시뒤 재가동합니다ㅠ")

            time.sleep(43200) # 12시간 뒤에 재가동

        time.sleep(1) # 없거나 짧으면 -> [오류 발생]'NoneType' object has no attribute 'index'

except Exception as e:
    print(e)
    send_message(f"[오류 발생]{e}")
    
    for sym in symbol_list: # 있으면 일괄 매도
        coin = get_balance(symbol_list[sym]['매도티커'])  # 보유량
        if coin > 0: # 있다면 매도
            sell_result = upbit.sell_market_order(sym, coin)
            if sell_result is not None:
                send_message(f"[{symbol_list[sym]['종목명']}] {coin} 전량 매도했습니다~")
            else:
                send_message(f"[{symbol_list[sym]['매도티커']}] 매도실패 ({sell_result})")
