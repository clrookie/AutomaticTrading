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

    last_min = 77
    last_current = 1
    last_result = 0
    more_last_result = 0
    
    #원금
    principal = 10000000
    withdrawal_need = 0
    cash_backup = 0

    result_rate = 0
    #lostcut = -20
    #lostcut_step = 5
    once = False
    
    # 기준 거래량 비율
    panic_volume_rate = 2
    greed_volume_rate = 1
    
    # 예치
    bbuy = 0
    min_buy = 10000 #만원씩 거래
    buy_rate = 10000 #만원씩 거래

    panic_count = 1
    panic_leverage = 1
    panic_low = 0.2       # 탐욕
    panic_mid = 0.3
    panic_high = 0.4    # 공포
    greed_leverage = 1
    greed_low = 0.2     # 탐욕
    greed_mid = 0.3
    greed_high = 0.4    # 공포
    
    # 지급
    bsell = 1
    base_sell_rate = 0
    backup_rate = 0
    backup_avg = 0

    #60분봉 데드크로스 체크
    b_60_goldencross = False
    b_60_middle = False
    b_60_deadcross = False

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

        if df.index[0].minute != last_min:    # 1분 캔들 갱신

            time.sleep(0.2) # 데이터 갱신 보정

            bbuy = 0
            bsell = 1
            backup_rate = 0
            backup_avg = 0
            

            last_min = df.index[0].minute

            message_list = "\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n"
            message_list += f">>> 1분봉 갱신합니다 <<< ({last_min}분) ({last_min}분) ({last_min}분) ({last_min}분) ({last_min}분)\n"
            message_list += "\n>>> "

            total = 0
            
            principal = 10000000
            
            formatted_amount1 = "{:,.0f}원".format(buy_rate)
            message_list += f"기준금액 {formatted_amount1} \n"
            message_list += f"공포량: {panic_volume_rate}배 / 탐욕량: {greed_volume_rate}배 / 레버리지(예치{panic_leverage}배, 지급{greed_leverage}배) \n\n"
            message_list += "------------------------------------------\n"

            for sym in symbol_list: # 초기화
                
                current_price = get_current_price(sym)
                
                formatted_amount = "{:,.0f}원".format(current_price)
                formatted_amount1 = "{:,.2f}%".format((current_price/last_current)*100-100)
                message_list += f"[{symbol_list[sym]['종목명']}] {formatted_amount}({formatted_amount1})\n"

                last_current = current_price

                qty = get_balance(symbol_list[sym]['매도티커'])

                symbol_list[sym]['total'] = current_price * qty

                symbol_list[sym]['잔여예산'] = get_balance("KRW") # 현금잔고 조회

                # 수익실현 했니?
                if cash_backup > symbol_list[sym]['잔여예산']:
                    withdrawal_need = 0 #

                # 기준금액 총 잔액 연동
                buy_rate = min_buy * (principal/(symbol_list[sym]['total']+symbol_list[sym]['잔여예산']))
                if buy_rate > min_buy: buy_rate = min_buy

                if symbol_list[sym]['total'] >= min_buy: # 최소 주문 가격 이상일 때

                    time.sleep(0.02)
                    avg_price = upbit.get_avg_buy_price(sym)
                    
                    formatted_amount = "{:,.0f}원".format(avg_price)
                    backup_avg = formatted_amount # 평균가 백업

                    formatted_amount = "{:,.0f}원".format(symbol_list[sym]['total'])
                    backup_rate = "{:,.2f}%".format(current_price/avg_price*100-100)
                    message_list += f"보유 {formatted_amount} ({backup_rate})"

                    # 수익상태에 따라 지급 결정
                    # if (current_price/avg_price*100-100) > base_sell_rate : bsell = 1

                
                average_price_20 = 0
                average_price_60 = 0
                average_price_120 = 0


                # 60분봉 데이터 가져오기 (최근 20봉)
                average_price_10_20 = 0
                average_price_10_60 = 0
                average_price_10_120 = 0

                data_10 = pyupbit.get_ohlcv(sym, interval="minute60", count=20)

                if data_10 is not None:
                    average_price_10_20 = data_10['close'].mean()
                    time.sleep(0.02)

                    # 최근 60봉
                    data_10_60 = pyupbit.get_ohlcv(sym, interval="minute60", count=60)

                    if data_10_60 is not None:
                        average_price_10_60 = data_10_60['close'].mean()
                        time.sleep(0.02)

                        # 최근 120봉
                        data_10_120 = pyupbit.get_ohlcv(sym, interval="minute60", count=120)

                        if data_10_120 is not None:
                            average_price_10_120 = data_10_120['close'].mean()

                            # 예치/지급 배율 세팅
                            if average_price_10_20 > average_price_10_60 and average_price_10_20 > average_price_10_120: #탐욕구간
                                panic_leverage = panic_low
                                greed_leverage = greed_low

                                b_60_goldencross = True
                                b_60_deadcross = False

                            elif average_price_10_20 < average_price_10_60 and average_price_10_20 < average_price_10_120: #공포구간
                                panic_leverage = panic_high
                                greed_leverage = greed_high

                                # if b_60_goldencross == True: # 데드크로스 체크

                                    # 데드크로스 청산 (오히려 이때 반등 많이 나옴)
                                    # send_message("###### 60분봉 데드크로스 ### 60분봉 데드크로스 ######")
                                    # coin = get_balance(symbol_list[sym]['매도티커'])  # 보유량
                                    # if coin > 0: # 있다면 매도
                                    #     sell_result = upbit.sell_market_order(sym, coin/3)
                                    #     if sell_result is not None:
                                    #         qty = get_balance(symbol_list[sym]['매도티커'])
                                    #         symbol_list[sym]['total'] = current_price * qty
                                    #         send_message(f"[{symbol_list[sym]['종목명']}] {coin} 1/3 매도했습니다~")
                                    #     else:
                                    #         send_message(f"[{symbol_list[sym]['매도티커']}] 매도실패 ({sell_result})")
                                        #    continue
                                
                                b_60_goldencross = False
                                b_60_deadcross = True

                            else:
                                panic_leverage = panic_mid
                                greed_leverage = greed_mid                         

                        else:
                            message_list += "10분봉 120 이평선 실패 !! \n"
                            continue
                    else:
                        message_list += "10분봉 60 이평선 실패 !! \n"
                        continue

                else:
                    message_list += "10분봉 20 이평선 실패 !! \n"
                    continue
                   
                time.sleep(0.02)

                # 1분봉 데이터 가져오기 (최근 20봉)
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
                
                formatted_amount3 = "{:,.0f}".format(current_price*average_volume)
                formatted_amount4 = "{:,.0f}".format(current_price*last_volume)
                avg1 = (current_price*last_volume) / (current_price*average_volume) * 100
                formatted_amount5 = "{:,.0f}%".format(avg1)
                message_list += f"\n\n평균: {formatted_amount3} | 직전: {formatted_amount4} [{formatted_amount5}]"

                # 직전 차트
                last_open = data.iloc[18]['open']
                last_close = data.iloc[18]['close']
                last_high = data.iloc[18]['high']
                last_low = data.iloc[18]['low']

                # 시가 120 이평선 위에
                if symbol_list[sym]['total'] >= min_buy and last_open > average_price_20 and last_open > average_price_60 and last_open > average_price_120:

                    symbol_list[sym]['공포에너지'] = 0

                    # 거래량 변동성 신호
                    if last_volume > (average_volume*greed_volume_rate):
                                           
                        # 양봉이니?
                        if last_open <= last_close and bsell == 1:
                            
                            message_list += "\n\n--- 탐욕 지급 --- 탐욕 지급 --- 탐욕 지급 --- 탐욕 지급 ---\n"

                            r_last_volume = round((current_price*last_volume)/buy_rate)

                            # 잔여예산 탄력지급 로직
                            rate = greed_leverage
                            # if symbol_list[sym]['잔여예산'] > 0:
                            #     rate = (1 - (symbol_list[sym]['잔여예산'] / (symbol_list[sym]['total']+symbol_list[sym]['잔여예산']))) * greed_leverage
                            #     rate = round(rate,2)
                            #     if rate < 0.2: rate = 0.2

                            r_last_volume *= rate
                            # else:
                                # r_last_volume *= greed_leverage

                            # r_last_volume *= greed_leverage

                            formatted_amount = "{:,.0f}원".format(r_last_volume)
                            message_list += f"{formatted_amount} 지급 (지급률 {rate}%) | "

                            sell_qty = r_last_volume / current_price
                            if sell_qty > qty: sell_qty = qty

                            time.sleep(0.02)
                            avg_price = upbit.get_avg_buy_price(sym)

                            time.sleep(0.02)
                            sell_result = upbit.sell_market_order(sym, sell_qty)
                            if sell_result is not None:
                                
                                bbuy = 1
                                message_list += f"{round(current_price/avg_price*100-100,2)}% 탐욕 매도 ^^\n"

                                time.sleep(0.02)
                                qty = get_balance(symbol_list[sym]['매도티커'])

                                symbol_list[sym]['total'] = current_price * qty
                                # formatted_amount = "{:,.0f}원".format(symbol_list[sym]['total'])
                                # message_list += f"갱신: {formatted_amount}\n"
                            else:
                                message_list += f"탐욕 매도 실패 ({sell_result})\n"

                        else: # 음봉
                            message_list += "\n20 60 120 ↑↑↑↑ '음봉' 나가리~\n"
                    else: # 변동성 조건 미달
                            message_list += " - 탐욕구간"

                # 저가 120 이평선 아래        
                elif symbol_list[sym]['잔여예산'] >= min_buy and last_open < average_price_20 and last_open < average_price_60 and last_open < average_price_120:

                    # 음봉이니?
                    if last_open >= last_close:
                    
                        symbol_list[sym]['공포에너지'] += 1
                        
                        message_list += f" - 공포구간({symbol_list[sym]['공포에너지']})"

                        # 거래량 변동성 신호
                        if symbol_list[sym]['공포에너지'] >= panic_count and last_volume > (average_volume*panic_volume_rate): # 공포에너지 체크 때문에 거래량 여기서 체크

                            price = 0
                            message_list += "\n\n+++ 공포 예치 +++ 공포 예치 +++ 공포 예치 +++ 공포 예치 +++\n"

                            r_last_volume = round((current_price*last_volume)/buy_rate)
                            r_last_volume *= panic_leverage # 

                            formatted_amount = "{:,.0f}원".format(r_last_volume)
                            message_list += f"!! {formatted_amount} 예치 !! \n"
                            
                            if symbol_list[sym]['잔여예산'] >= r_last_volume:                               
                                price = r_last_volume
                            else : price = symbol_list[sym]['잔여예산']

                            # 공포 매수
                            buy_result = upbit.buy_market_order(sym, price) # 현금
                            if buy_result is not None:          
                                
                                time.sleep(1)
                                bbuy = 1
                                qty = get_balance(symbol_list[sym]['매도티커'])

                                symbol_list[sym]['total'] = current_price * qty
                                # formatted_amount = "{:,.0f}원".format(symbol_list[sym]['total']) 
                                # message_list += f"갱신: {formatted_amount}\n"
                        
                                time.sleep(0.02)
                                avg_price = upbit.get_avg_buy_price(sym)
                                formatted_amount = "{:,.0f}원".format(avg_price)
                                backup_avg = formatted_amount # 평균가 백업  

                            else:
                                message_list += f"공포 매수 실패 ({buy_result})\n"

                    else: # 양봉
                        message_list += " - 공포구간 '양봉'\n"
                else:
                    symbol_list[sym]['공포에너지'] = 0
                    message_list += " - 관망중..'\n"

                total += symbol_list[sym]['total']
                # message_list += "\n\n------------------------------------------\n"
                
            
            
            message_list += f"\n===========({last_min}분)===========\n"

            total_cash = get_balance("KRW") # 현금잔고 조회
            cash_backup = total_cash

            formatted_amount = "{:,.2f}%".format(total/(total_cash+total)*100)
            message_list += f"코인 비중: {formatted_amount}\n"

            formatted_amount = "{:,.0f}원".format(total_cash+total)
            message_list += f"총 잔고: {formatted_amount} "

            formatted_amount = "{:,.0f}원".format(total_cash)
            message_list += f"(현금 {formatted_amount}, "
            formatted_amount = "{:,.0f}원".format(total)
            message_list += f"코인 {formatted_amount})\n"

            result_rate = ((total_cash+total) / principal * 100) - 100

            # 최초 한번 로스컷 세팅
            # if once == False:
            #     once = True
            #     while lostcut > result_rate:    # 로스컷 보다 작다면,
            #         lostcut -= lostcut_step
            # else:
            #     if lostcut+(lostcut_step*2) < result_rate:    # 로스컷 + 2단계 보다 크다면,
            #         lostcut += lostcut_step

            # 출금 필요액 갱신
            profit = (total_cash+total)-principal
            if profit > 0:
                profit *= 1 - total_cash/principal
                if withdrawal_need < profit:
                    withdrawal_need = (profit // 10000) * 10000 
                    # lostcut = -3  # 로스컷 초기화

            formatted_amount0 = "{:,.0f}원".format(withdrawal_need)
            formatted_amount1 = "{:,.2f}%".format(more_last_result)
            formatted_amount2 = "{:,.2f}%".format(last_result)
            formatted_amount3 = "{:,.2f}%".format(result_rate)
            message_list += f"추이: {formatted_amount1} > {formatted_amount2} > '{formatted_amount3}'\n"
            message_list += f"평단가: {backup_avg}\n\n"

            message_list += f"수익금: {formatted_amount0}\n"
            
            more_last_result = last_result
            last_result = result_rate

            message_list += f"===========({last_min}분)=======================\n\n\n"

            if last_min == 0:
                send_message_Report(message_list)
            
            if bbuy == 1:
                send_message(message_list)
            else:
                formatted_amount4 = "{:,.0f}원".format(total_cash+total)
                message_symplelist = f"총 잔고: {formatted_amount4} / {backup_avg}({backup_rate})"
                send_message(message_symplelist)
                
                          
        # for문 끝 라인..

        # if bbuy == 0 and lostcut > result_rate: #사이드브레이크
            
        #     formatted_amount = "{:,.2f}%".format(result_rate)
        #     send_message("###########################################")
        #     send_message("###########################################")
        #     send_message(f"총 수익율 {formatted_amount} 도달로 1/5 매도합니다ㅠ")
        #     send_message("###########################################")
        #     send_message("###########################################")

        #     lostcut -= lostcut_step
        #     for sym in symbol_list: # 있으면 일괄 매도
        #         coin = get_balance(symbol_list[sym]['매도티커'])  # 보유량
        #         if coin > 0: # 있다면 매도
        #             sell_result = upbit.sell_market_order(sym, coin/5)
        #             if sell_result is not None:
        #                 send_message(f"[{symbol_list[sym]['종목명']}] {coin} 1/5 매도했습니다~")
        #             else:
        #                 send_message(f"[{symbol_list[sym]['매도티커']}] 매도실패 ({sell_result})")
            

        time.sleep(1) # 없거나 짧으면 -> [오류 발생]'NoneType' object has no attribute 'index'

except Exception as e:
    print(e)
    
    send_message("#########################################")
    send_message("#########################################")
    send_message(f"[오류 발생]{e}")
    
    for sym in symbol_list: # 있으면 일괄 매도
        coin = get_balance(symbol_list[sym]['매도티커'])  # 보유량
        if coin > 0: # 있다면 매도
            sell_result = upbit.sell_market_order(sym, coin/5)
            if sell_result is not None:
                send_message(f"[{symbol_list[sym]['종목명']}] {coin} 1/2 매도했습니다~")
            else:
                send_message(f"[{symbol_list[sym]['매도티커']}] 매도실패 ({sell_result})")

