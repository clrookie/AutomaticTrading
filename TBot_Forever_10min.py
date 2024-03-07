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

def get_target_price(ticker,profit_max): # 음봉 윗꼬리 평균 + 보정

    data_period = 30 # 최근 추출 기간
    cnt = 0 # 음봉 카운트
    target_price = 0 # 초기화
    delta = 0 # 윗꼬리값

    # df = pyupbit.get_ohlcv(ticker, interval="day", count=data_period)
    try:
        df = pyupbit.get_ohlcv(ticker, interval="day", count=data_period)
    except Exception as e:
        send_message(f"Error fetching data: {e}")
        return None, None  # 데이터를 가져오지 못할 경우 None을 반환

    for i in range(0,data_period-1):
        stck_hgpr = int(df.iloc[i]['high']) #고가
        stck_clpr = int(df.iloc[i]['close']) #종가
        stck_oprc = int(df.iloc[i]['open']) #시가

        if stck_oprc >= stck_clpr : #음봉
            delta += stck_hgpr - stck_oprc
            cnt += 1

    target_price = int(df.iloc[data_period-1]['open']) #현재 구간 시가
    
    if cnt > 0:
        delta /= cnt # 평균

    target_price += int(delta)

    # 5일 이평선 ----------------------------------------------------------------
    # df_5 = pyupbit.get_ohlcv(ticker, interval="day", count=5)
    try:
        df_5 = pyupbit.get_ohlcv(ticker, interval="day", count=5)
    except Exception as e:
        send_message(f"Error fetching data: {e}")
        return None, None  # 데이터를 가져오지 못할 경우 None을 반환

    stck_clpr_5 = 0
    for i in range(0,5):
        stck_clpr_5 += int(df_5.iloc[i]['close']) #종가

    stck_clpr_5 /= 5
    stck_oprc_day = int(df_5.iloc[4]['open'])

    profit_rate = 1
    
    # 시가 이평선 아래
    if stck_oprc_day < stck_clpr_5:
        profit_limit = target_price * profit_max

        # 이격도가 크면
        if stck_clpr_5 > profit_limit:
            return target_price,profit_rate
        
        else: # 이격도가 작으면
            profit_limit = target_price * (((profit_max-1)/2)+1)
            
            if stck_clpr_5 > profit_limit:
                return target_price, (profit_rate/2) # 익절선 짧게
            
            else: # 이격도가 '매우' 작으면
                target_price = stck_clpr_5 + int(delta)
                return target_price,profit_rate

    # 이평선 위에 시가 시작이면 평소처럼
    return target_price, profit_rate


def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

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

def get_stck_oprc(ticker):

    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    stck_oprc = int(df.iloc[0]['open']) #오늘 시가
    
    return stck_oprc

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
    
    # 손절 기준선
    loss_cut1 = 0.991
    loss_cut2 = 0.990
    loss_cut3 = 0.989

    # 손절 기준선 (테스트용)
    # loss_cut1 = 0.999
    # loss_cut2 = 0.998
    # loss_cut3 = 0.997

    # 익절비율
    sell_rate = 0.35
    
    # 매수
    buy_rate = 0.33
    buy_max_cnt = 3
    buy_interval = 0.2
    
    previous_time = datetime.datetime.now()

    # 공용 데이터
    common_data ={
    '배분예산':0,
    '목표매수가':0,
    '실매수가':0,
    '시가':0,
    '평단가':0,
    '보유': False,
    '매수최대량':0,
        
    '공포상태': False,
    '익절준비': False,
    '매수카운트':0,
    '손절_1차': False,
    '손절_2차': False,
    '손절_3차': False,
    '손절청산': False,
    '익절청산': False,
        
    'profit_rate_touch': 1.007,
    'profit_rate_last': 1.007
    }

    #개별 종목 데이터
    symbol_list = { 
    'KRW-BTC':{'종목명':'비트코인 #1', #1
    '매도티커':'BTC',
    '예산_가중치':1.0,
    '익절_가중치':1.0,
    **common_data},

    'KRW-ETH':{'종목명':'이더리움 #2', #2
    '매도티커':'ETH',
    '예산_가중치':1.0,
    '익절_가중치':1.0,
    **common_data},

    'KRW-SOL':{'종목명':'솔라나 #3', #2
    '매도티커':'SOL',
    '예산_가중치':1.0,
    '익절_가중치':1.0,
    **common_data},

    'KRW-XRP':{'종목명':'리플 #4', #3 
    '매도티커':'XRP',
    '예산_가중치':1.0,
    '익절_가중치':1.0,
    **common_data},

    'KRW-ADA':{'종목명':'에이다 #5', #3 
    '매도티커':'ADA',
    '예산_가중치':1.0,
    '익절_가중치':1.0,
    **common_data},
    }


    for sym in symbol_list: # 있으면 일괄 매도
        coin = get_balance(symbol_list[sym]['매도티커'])  # 보유량
        if coin > 0 : # 최소 거래량
            sell_result = upbit.sell_market_order(sym, coin)
            if sell_result is not None:
                send_message(f"[{symbol_list[sym]['종목명']}] {coin} 전량 매도했습니다~")
            else:
                send_message(f"[{symbol_list[sym]['매도티커']}] 매도실패 ({sell_result})")


    while True:
        
        df = pyupbit.get_ohlcv("KRW-BTC", interval="minute10", count=1)    
    

        if df.index[0].minute != last_min:    # 10분 캔들 갱신

            last_min = df.index[0].minute

            message_list = ""
            message_list += f">>> 코인거래 10분봉 갱신합니다 <<< ({last_min}분)\n"
            message_list += "\n"


            target_buy_count = int(len(symbol_list)) # 매수종목 수량


            total_cash = get_balance("KRW") # 현금잔고 조회
            
            total_cash /= 5 # 임시코드
        
            formatted_amount = "{:,.0f}원".format(total_cash)
            message_list += f"현금잔고: {formatted_amount}\n"
            message_list += "\n"

            # 고정 시드머니 설정 (500만원대 잔액 날리기)
            b = 1000000
            b = total_cash % b
            
            if total_cash > b:
                total_cash -= b



            for sym in symbol_list: # 초기화
                message_list += f"[{symbol_list[sym]['종목명']}]\n"

                symbol_list[sym]['배분예산'] = round((total_cash * (1/target_buy_count) * symbol_list[sym]['예산_가중치']),2)
                formatted_amount = "{:,.1f}원".format(symbol_list[sym]['배분예산'])
                message_list += f"배분예산: {formatted_amount}\n"
                    
                qty = get_balance(symbol_list[sym]['매도티커'])
                
                current_price = get_current_price(sym)
                current_total = current_price * qty

                if current_total >= 5000: # 최소 주문 가격 이상일 때
                    
                    symbol_list[sym]['보유'] = True

                    formatted_amount = "{:,.1f}원".format(current_price)
                    message_list += f"현재가: {formatted_amount}\n"

                    avg_price = upbit.get_avg_buy_price(sym)
                    formatted_amount = "{:,.1f}원".format(avg_price)
                    formatted_amount1 = "{:,.1f}%".format(current_price/avg_price*100)
                    message_list += f"평단가: {formatted_amount} ({formatted_amount1})\n"
                    
                    message_list += f"보유 수량: {qty}개\n"

                    total = current_price * qty
                    formatted_amount = "{:,.0f}원".format(total)
                    message_list += f"보유 잔고: {formatted_amount}\n\n"
                    total_cash += total

                elif symbol_list[sym]['공포상태'] == False:

                    # KRW-BTC 페어의 10분봉 데이터 가져오기 (최근 20봉)
                    data = pyupbit.get_ohlcv(sym, interval="minute10", count=20)

                    # 음봉일때만
                    last_open = data.iloc[18]['open']
                    last_close = data.iloc[18]['close']
                    
                    # 평균 거래량 계산
                    average_volume = data['volume'].mean()
                    formatted_amount = "{:,.0f}".format(average_volume)
                    message_list += f"평균 거래량: {formatted_amount}\n"

                    # 직전 거래량
                    last_volume = data.iloc[18]['volume']
                    avg = (last_volume / average_volume) * 100
                    formatted_amount1 = "{:,.0f}".format(last_volume)
                    formatted_amount2 = "{:,.0f}".format(avg)
                    message_list += f"직전 거래량: {formatted_amount1} ({formatted_amount2}%) - "
                    
                    if last_open > last_close: 
                        message_list += "(---음봉---)\n\n"

                        # 공포상태 체크
                        if last_volume > (average_volume*2):
                            
                            # 전전 정보
                            last2_open = data.iloc[17]['open']
                            last2_close = data.iloc[17]['close']
                            last2_volume = data.iloc[17]['volume']
                            if last2_open < last2_close and last2_volume > average_volume*1.5:
                                message_list += "!!! 상투 패턴이라 패스 !!!\n"
                                message_list += "---------------------------------\n"
                                continue

                            symbol_list[sym]['공포상태'] = True
                            message_list += "!-!-!-! 공포패턴 !-!-!-!\n"

                            symbol_list[sym]['보유'] = False
                            symbol_list[sym]['손절_1차'] = False
                            symbol_list[sym]['손절_2차'] = False
                            symbol_list[sym]['손절_3차'] = False
                            symbol_list[sym]['매수카운트'] = 0
                            symbol_list[sym]['매수최대량'] = 0

                            symbol_list[sym]['profit_rate_touch'] = 1.007
                            symbol_list[sym]['profit_rate_last'] = 1.007
                            symbol_list[sym]['익절준비'] = False

                    else:
                        message_list += "(+++양봉+++)\n"
                        
                        # # 탐욕상태 체크
                        # if last_volume > (average_volume*2):
                            
                        #     # 전전 정보
                        #     last2_open = data.iloc[17]['open']
                        #     last2_close = data.iloc[17]['close']
                        #     last2_volume = data.iloc[17]['volume']
                        #     if last2_volume > average_volume*1.5:
                        #         message_list += "!!! 상투 패턴이라 패스 !!!\n"
                        #         message_list += "---------------------------------\n"
                        #         continue
                            
                        #     symbol_list[sym]['공포상태'] = True
                        #     message_list += "!+!+!+! 탐욕패턴 !+!+!+!\n"

                        #     symbol_list[sym]['보유'] = False
                        #     symbol_list[sym]['손절_1차'] = False
                        #     symbol_list[sym]['손절_2차'] = False
                        #     symbol_list[sym]['손절_3차'] = False
                        #     symbol_list[sym]['매수카운트'] = 0
                        #     symbol_list[sym]['매수최대량'] = 0

                        #     symbol_list[sym]['profit_rate_touch'] = 1.007
                        #     symbol_list[sym]['profit_rate_last'] = 1.007
                        #     symbol_list[sym]['익절준비'] = False

                message_list += "---------------------------------\n"
            
            formatted_amount = "{:,.0f}원".format(total_cash)
            message_list += f"총 보유 잔고: {formatted_amount}\n\n"

            previous_time = datetime.datetime.now()

            send_message(message_list)

        else:   # 거래 루프        
            # 시간 간격 분할 매수
            time_difference = t_now - previous_time
            # n시간이 지났는지 확인
            if time_difference >= timedelta(seconds=buy_interval):
                # 현재 시간을 이전 시간으로 업데이트
                previous_time = t_now
                
                for sym in symbol_list:

                    if symbol_list[sym]['공포상태'] == True and symbol_list[sym]['매수카운트'] < buy_max_cnt: # 목표매수가와 횟수 체크
                        
                        current_price = get_current_price(sym)

                        qty = math.floor(symbol_list[sym]['배분예산']/current_price* buy_rate * 1000 )/1000  # 소수점 3자리 반내림 # 분할 매수
                        qty = round(qty,4)
                        if qty <= 0: qty = 0.001

                        price = symbol_list[sym]['배분예산'] * buy_rate # 소수점 3자리 반내림 # 분할 매수
                        if price < 5000: price = 5000 # 최소 주문량

                        message_list = ""
                        message_list += f"[{symbol_list[sym]['종목명']}] 매수시도 ({qty}개)\n"
                        
                        buy_result = upbit.buy_market_order(sym, price) # 현금
                        if buy_result is not None:          
                            symbol_list[sym]['매수카운트'] += 1                  
                            symbol_list[sym]['실매수가'] = current_price
                            symbol_list[sym]['보유'] = True
                            
                            symbol_list[sym]['매수최대량'] += qty

                            # 손절 1차 unlock... ;;
                            symbol_list[sym]['손절_1차'] = False
                            symbol_list[sym]['손절_2차'] = False
                            symbol_list[sym]['손절_3차'] = False

                            
                            message_list += f"+++ {symbol_list[sym]['매수카운트']}차 매수 성공 +++\n"
                            
                            formatted_amount = "{:,.1f}원".format(symbol_list[sym]['실매수가'])
                            message_list += f"- 실매수가: {formatted_amount}\n"
                            
                            avg_price = upbit.get_avg_buy_price(sym)
                            formatted_amount = "{:,.1f}원".format(avg_price)
                            message_list += f"- 평단가: {formatted_amount}\n"                            

                        else:
                            message_list += f"매수 실패 ({buy_result})\n"
                        
                        send_message(message_list)

# -------------- 분할 매수 -------------------------------------------------------


# -------------- 보유중 -------------------------------------------------------
                                
           
            for sym in symbol_list:

                if symbol_list[sym]['보유']: # 보유중이면

                    sell_fix = False
                    
                    avg_price = upbit.get_avg_buy_price(sym)
                    current_price = get_current_price(sym)

                    # 익절 최소 조건
                    if current_price > avg_price * symbol_list[sym]['profit_rate_touch']:
                        
                        # 로그 추가
                        send_message(f"{symbol_list[sym]['종목명']} 익절 터치값 ({symbol_list[sym]['profit_rate_touch']}%)")

                        symbol_list[sym]['profit_rate_last'] = symbol_list[sym]['profit_rate_touch'] - 0.0015
                        symbol_list[sym]['profit_rate_touch'] += 0.0045
                        symbol_list[sym]['익절준비'] = True

                    # 하향 익절
                    elif symbol_list[sym]['익절준비'] == True and current_price <= avg_price * symbol_list[sym]['profit_rate_last']:
                        symbol_list[sym]['profit_rate_last'] -= 0.0015
                        symbol_list[sym]['profit_rate_touch'] -= 0.0015
                        sell_fix = True


                    # 익절하거나
                    if sell_fix:
                        qty = get_balance(symbol_list[sym]['매도티커']) # 보유주식 정보 최신화 

                        if qty > 0:
                            
                            sell_qty = symbol_list[sym]['매수최대량'] * sell_rate

                            if(sell_qty < 0.001): sell_qty = 0.001

                            if qty > sell_qty: # 분할 익절
                                send_message(f"[{symbol_list[sym]['종목명']}]: 분할 익절 ({sell_qty}/{qty}개)")
                                qty = sell_qty
                            else:
                                symbol_list[sym]['보유'] = False # 전량 익절
                                symbol_list[sym]['공포상태'] = False
                                send_message(f"[{symbol_list[sym]['종목명']}]: 전량 익절 ({qty}개)")

                            
                            sell_result = upbit.sell_market_order(sym, qty)
                            if sell_result is not None:
                                send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/avg_price,4)}% 익절매합니다 ^^ ({qty}개)")
                                send_message(f"[{symbol_list[sym]['종목명']}]: 익절가({current_price}) 평단가({avg_price})")
                            else:
                                send_message(f"매도 실패 ({sell_result})")

                    # 1차 손절하거나
                    elif(avg_price*loss_cut1 > current_price and symbol_list[sym]['손절_1차'] == False): 
                                     
                        qty = get_balance(symbol_list[sym]['매도티커']) # 보유주식 정보 최신화
                        
                        if qty > 0:
                            
                            total_qty = qty
                            sell_qty = float(qty) * 0.33 # 분할 손절

                            # sell_qty = math.floor(qty * 1000)/1000 # 소수점 3자리 반내림
                            # if(sell_qty < 0.001): sell_qty = 0.001
                            
                            send_message(f"[{symbol_list[sym]['종목명']}]: 1차 손절매 ({sell_qty}/{total_qty}개)")
                            
                            sell_result = upbit.sell_market_order(sym, sell_qty)
                            if sell_result is not None:
                                symbol_list[sym]['손절_1차'] = True
                                symbol_list[sym]['매수최대량'] -= sell_qty     
                                send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/avg_price,4)}% 1차 손절매")
                                send_message(f"[{symbol_list[sym]['종목명']}]: 손절가({current_price}) 평단가({avg_price})") 
                            else:
                                send_message(f"매도 실패 ({sell_result})")  
                            
                    # 2차 손절하거나
                    elif(avg_price*loss_cut2 > current_price and symbol_list[sym]['손절_2차'] == False): 
                                     
                        qty = get_balance(symbol_list[sym]['매도티커']) # 보유주식 정보 최신화
                        
                        if qty > 0:
                            
                            total_qty = qty
                            sell_qty = float(qty) * 0.5 # 분할 손절
                            
                            # sell_qty = math.floor(qty * 1000)/1000 # 소수점 3자리 반내림
                            # if(sell_qty < 0.001): sell_qty = 0.001
                            
                            send_message(f"[{symbol_list[sym]['종목명']}]: 2차 손절매 ({sell_qty}/{total_qty}개)")
                            

                            sell_result = upbit.sell_market_order(sym, sell_qty)
                            if sell_result is not None:
                                symbol_list[sym]['손절_2차'] = True
                                symbol_list[sym]['매수최대량'] -= sell_qty     
                                send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/avg_price,4)}% 2차 손절매")
                                send_message(f"[{symbol_list[sym]['종목명']}]: 손절가({current_price}) 평단가({avg_price})") 
                            else:
                                send_message(f"매도 실패 ({sell_result})")  

                    # 3차 손절
                    elif(avg_price*loss_cut3 > current_price and symbol_list[sym]['손절_3차'] == False):
                        
                        qty = get_balance(symbol_list[sym]['매도티커']) # 보유주식 정보 최신화
                        
                        if qty > 0:
                            
                            total_qty = qty
                            
                            send_message(f"[{symbol_list[sym]['종목명']}]: 3차 전량 손절매 ({total_qty}개)")
                            
                            sell_result = upbit.sell_market_order(sym, total_qty)
                            if sell_result is not None:
                                symbol_list[sym]['손절_3차'] = True
                                symbol_list[sym]['보유'] = False # 전량 손절
                                symbol_list[sym]['공포상태'] = False
                                send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/avg_price,4)}% 3차 전량 손절매")
                                send_message(f"[{symbol_list[sym]['종목명']}]: 손절가({current_price}) 평단가({avg_price})") 
                            else:
                                send_message(f"매도 실패 ({sell_result})")  

#---------------------- 여기까지 보유중 루프 -----------------------------------------------------------------------------
                            

        # for문 끝 라인..
                                
        time.sleep(0.2)
        t_now = datetime.datetime.now()

except Exception as e:
    print(e)
    send_message(f"[오류 발생]{e}")

    for sym in symbol_list: # 오류나면 일괄 매도
        coin = get_balance(symbol_list[sym]['매도티커'])  # 보유량
        if coin >= 0.001 : # 최소 거래량
            sell_result = upbit.sell_market_order(sym, coin)
            if sell_result is not None:
                send_message(f"[{symbol_list[sym]['종목명']}] {coin} 오류 전량 매도했습니다~")
            else:
                send_message(f"[{symbol_list[sym]['매도티커']}] 오류 매도실패 ({sell_result})")

    time.sleep(1)
