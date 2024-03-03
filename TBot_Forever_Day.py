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
    send_message("=== 코인거래 초기화 합니다 ===")

    last_day = 0
    t_0 = True
    t_30 = True

    # # 익절 기준선
    # profit_rate07 = 1.016
    # profit_rate12 = 1.021
    # profit_rate17 = 1.026
    # profit_rate22 = 1.031
    
    # 익절 기준선
    profit_rate07 = 1.0056
    profit_rate12 = 1.0086
    profit_rate17 = 1.0116
    profit_rate22 = 1.0146
    
    # 손절 기준선
    loss_cut1 = 0.992
    loss_cut2 = 0.990
    loss_cut3 = 0.988

    # 익절비율
    sell_rate = 0.2
    
    # 매수
    buy_rate = 0.2
    buy_max_cnt = 5
    buy_interval = 30
    
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
        
    '매매유무': False,
    '매수카운트':0,
    '손절_1차': False,
    '손절_2차': False,
    '손절_3차': False,
    '손절청산': False,
    '익절청산': False,
        
    'profit_rate07_up': True,
    'profit_rate12_up': True,
    'profit_rate17_up': True,
    'profit_rate22_up': True,
    'profit_rate07_down': False,
    'profit_rate12_down': False,
    'profit_rate17_down': False
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


    while True:
        
        df = pyupbit.get_ohlcv("KRW-BTC", interval="day", count=1)    
        
        if df.index[0].day != last_day:    # 240분 캔들 갱신
            last_day = df.index[0].day
            
            message_list = ""
            message_list += f"=== 코인거래 일봉 갱신합니다 === ({last_day}일)\n"
            message_list += "\n"

            t_0 = True
            t_30 = True

            target_buy_count = int(len(symbol_list)) # 매수종목 수량

            for sym in symbol_list: # 있으면 일괄 매도

                coin = get_balance(symbol_list[sym]['매도티커'])  # 보유량
                if coin >= 0.001 : # 최소 거래량
                    sell_result = upbit.sell_market_order(sym, coin)
                    if sell_result is not None:
                        send_message(f"[{symbol_list[sym]['종목명']}] {coin} 전량 매도했습니다~")
                    else:
                        send_message(f"[{symbol_list[sym]['매도티커']}] 매도실패 ({sell_result})")
            
            
            time.sleep(1)

            total_cash = get_balance("KRW") # 현금잔고 조회
        
            formatted_amount = "{:,.0f}원".format(total_cash)
            message_list += f"현금 잔고: {formatted_amount}\n"
            message_list += "\n"

            # 고정 시드머니 설정 (10만원대 날리기)
            b = 5000000
            b = total_cash % b
            
            if total_cash > b:
                total_cash -= b

            for sym in symbol_list: # 초기화
                message_list += f"[{symbol_list[sym]['종목명']}]\n"
                symbol_list[sym]['배분예산'] = round((total_cash * (1/target_buy_count) * symbol_list[sym]['예산_가중치']),2)
                formatted_amount = "{:,.1f}원".format(symbol_list[sym]['배분예산'])
                message_list += f"- 배분예산: {formatted_amount}\n"

                symbol_list[sym]['시가'] = round(get_stck_oprc(sym),2)
                formatted_amount = "{:,.1f}원".format(symbol_list[sym]['시가'])
                message_list += f"- 시가: {formatted_amount}\n"   

                # send_message(f"{sym}111")
                target_price,profit_rate = get_target_price(sym,(((profit_rate22-1)*symbol_list[sym]['익절_가중치'])+1))
                # send_message("222")
                
                symbol_list[sym]['익절_가중치'] *= profit_rate

                symbol_list[sym]['목표매수가'] = round(target_price,2)
                formatted_amount = "{:,.1f}원".format(symbol_list[sym]['목표매수가'])
                message_list += f"- 목표매수가: {formatted_amount}\n"   

                message_list += f"- 타겟%: {round((symbol_list[sym]['목표매수가'])/symbol_list[sym]['시가'],4)}\n"

                
                symbol_list[sym]['보유'] = False
                symbol_list[sym]['손절_1차'] = False
                symbol_list[sym]['손절_2차'] = False
                symbol_list[sym]['손절_3차'] = False
                symbol_list[sym]['매매유무'] = False
                symbol_list[sym]['매수카운트'] = 0
                symbol_list[sym]['매수최대량'] = 0
                symbol_list[sym]['손절청산'] = False
                symbol_list[sym]['익절청산'] = False

                message_list += "---------------------------------\n"
            
            
            previous_time = datetime.datetime.now()
            message_list += "\n"
            message_list += "코인 매매를 시작합니다~~\n"
            message_list += "\n"

            send_message(message_list)

        else:   # 거래 루프        
            # 시간 간격 분할 매수
            time_difference = t_now - previous_time
            # n시간이 지났는지 확인
            if time_difference >= timedelta(seconds=buy_interval):
                # 현재 시간을 이전 시간으로 업데이트
                previous_time = t_now
                
                for sym in symbol_list:

                    current_price = get_current_price(sym)

                    if symbol_list[sym]['목표매수가'] < current_price and symbol_list[sym]['매수카운트'] < buy_max_cnt: # 목표매수가와 횟수 체크
                        
                        qty = math.floor(symbol_list[sym]['배분예산']/current_price* buy_rate * 1000 )/1000  # 소수점 3자리 반내림 # 분할 매수
                        qty = round(qty,4)
                        if qty <= 0: qty = 0.001

                        price = symbol_list[sym]['배분예산'] * buy_rate # 소수점 3자리 반내림 # 분할 매수
                        if price < 5000: price = 5000 # 최소 주문량

                        message_list = ""
                        message_list += f"[{symbol_list[sym]['종목명']}] 매수 시도 ({qty}개)\n"
                        
                        buy_result = upbit.buy_market_order(sym, price) # 현금
                        if buy_result is not None:          
                            symbol_list[sym]['매수카운트'] += 1                  
                            symbol_list[sym]['실매수가'] = current_price
                            symbol_list[sym]['보유'] = True
                            symbol_list[sym]['매매유무'] = True
                            
                            symbol_list[sym]['매수최대량'] += qty

                            # 손절 1차 unlock... ;;
                            symbol_list[sym]['손절_1차'] = False
                            symbol_list[sym]['손절_2차'] = False
                            symbol_list[sym]['손절_3차'] = False     

                            
                            message_list += f"++++ {symbol_list[sym]['매수카운트']}차 매수 성공 ++++\n"
                            
                            formatted_amount = "{:,.1f}원".format(symbol_list[sym]['시가'])
                            message_list += f"- 시가: {formatted_amount}\n"
                            formatted_amount = "{:,.1f}원".format(symbol_list[sym]['목표매수가'])
                            message_list += f"- 목표매수가: {formatted_amount}\n"   
                            formatted_amount = "{:,.1f}원".format(symbol_list[sym]['실매수가'])
                            message_list += f"- 실매수가: {formatted_amount}\n"
                            
                            
                            avg_price = upbit.get_avg_buy_price(sym)
                            formatted_amount = "{:,.1f}원".format(avg_price)
                            message_list += f"- 평단가: {formatted_amount}\n"                            

                            #분할매도 조건 초기화
                            symbol_list[sym]['profit_rate07_up'] = True
                            symbol_list[sym]['profit_rate12_up'] = True
                            symbol_list[sym]['profit_rate17_up'] = True
                            symbol_list[sym]['profit_rate22_up'] = True
                            symbol_list[sym]['profit_rate07_down'] = False
                            symbol_list[sym]['profit_rate12_down'] = False
                            symbol_list[sym]['profit_rate17_down'] = False
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

                    #상향 익절
                    if current_price > avg_price*(((profit_rate22-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate22_up']:
                        symbol_list[sym]['profit_rate22_up'] = False
                        symbol_list[sym]['profit_rate17_up'] = False
                        symbol_list[sym]['profit_rate12_up'] = False
                        symbol_list[sym]['profit_rate07_up'] = False

                        symbol_list[sym]['profit_rate17_down'] = True
                        symbol_list[sym]['profit_rate12_down'] = True
                        symbol_list[sym]['profit_rate07_down'] = True

                        sell_fix = True

                    elif current_price > avg_price*(((profit_rate17-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate17_up']:
                        symbol_list[sym]['profit_rate17_up'] = False
                        symbol_list[sym]['profit_rate12_up'] = False
                        symbol_list[sym]['profit_rate07_up'] = False

                        symbol_list[sym]['profit_rate12_down'] = True
                        symbol_list[sym]['profit_rate07_down'] = True

                        sell_fix = True

                    elif current_price > avg_price*(((profit_rate12-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate12_up']:
                        symbol_list[sym]['profit_rate12_up'] = False
                        symbol_list[sym]['profit_rate07_up'] = False

                        symbol_list[sym]['profit_rate07_down'] = True

                        sell_fix = True

                    elif current_price > avg_price*(((profit_rate07-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate07_up']:
                        symbol_list[sym]['profit_rate07_up'] = False

                        sell_fix = True

                    # 하향 익절
                    elif current_price <= avg_price*(((profit_rate17-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate17_down']:
                        symbol_list[sym]['profit_rate17_down'] = False

                        symbol_list[sym]['profit_rate22_up'] = True

                        sell_fix = True

                    elif current_price <= avg_price*(((profit_rate12-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate12_down']:
                        symbol_list[sym]['profit_rate12_down'] = False

                        symbol_list[sym]['profit_rate22_up'] = True
                        symbol_list[sym]['profit_rate17_up'] = True

                        sell_fix = True


                    elif current_price <= avg_price*(((profit_rate07-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate07_down']:
                        symbol_list[sym]['profit_rate07_down'] = False

                        symbol_list[sym]['profit_rate22_up'] = True
                        symbol_list[sym]['profit_rate17_up'] = True
                        symbol_list[sym]['profit_rate12_up'] = True

                        sell_fix = True

                    # 익절하거나 손절하거나 if절
                    if sell_fix:
                        qty = get_balance(symbol_list[sym]['매도티커']) # 보유주식 정보 최신화 

                        if qty > 0:
                            
                            sell_qty = math.floor(symbol_list[sym]['매수최대량'] * sell_rate * 1000)/1000 # 소수점 3자리 반내림

                            if(sell_qty < 0.001): sell_qty = 0.001
                            # sell_qty = round(sell_qty,4) 불필요한 로직인듯??

                            if qty > sell_qty: # 분할 익절
                                send_message(f"[{symbol_list[sym]['종목명']}]: 분할 익절 시도 ({sell_qty}/{qty}개)")
                                qty = sell_qty
                            else:
                                symbol_list[sym]['보유'] = False # 전량 익절
                                symbol_list[sym]['익절청산'] = True
                                send_message(f"[{symbol_list[sym]['종목명']}]: 전량 익절 시도 ({qty}개)")

                            
                            sell_result = upbit.sell_market_order(sym, qty)
                            if sell_result is not None:
                                send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/avg_price,4)}% 익절매합니다 ^^ ({qty}개)")
                                send_message(f"[{symbol_list[sym]['종목명']}]: 익절가({current_price}) 평단가({avg_price})")
                            else:
                                send_message(f"매도 실패 ({sell_result})")

    
                        

                    # 1차 손절하거나
                    elif(avg_price*loss_cut1 > current_price and symbol_list[sym]['손절_1차'] == False): # 오늘 시가 보다 떨어지면 
                                     
                        qty = get_balance(symbol_list[sym]['매도티커']) # 보유주식 정보 최신화
                        
                        if qty > 0:
                            
                            total_qty = qty
                            qty = float(qty) * 0.33 # 분할 손절

                            sell_qty = math.floor(qty * 1000)/1000 # 소수점 3자리 반내림

                            if(sell_qty < 0.001): sell_qty = 0.001
                            
                            send_message(f"[{symbol_list[sym]['종목명']}]: 1차 손절매 시도 ({sell_qty}/{total_qty}개)")
                            
                            sell_result = upbit.sell_market_order(sym, sell_qty)
                            if sell_result is not None:
                                symbol_list[sym]['손절_1차'] = True
                                symbol_list[sym]['매수최대량'] -= sell_qty     
                                send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/avg_price,4)}% 1차 손절매")
                                send_message(f"[{symbol_list[sym]['종목명']}]: 손절가({current_price}) 평단가({avg_price})") 
                            else:
                                send_message(f"매도 실패 ({sell_result})")  
                            
                    # 2차 손절하거나
                    elif(avg_price*loss_cut2 > current_price and symbol_list[sym]['손절_2차'] == False): # 오늘 시가 보다 떨어지면 
                                     
                        qty = get_balance(symbol_list[sym]['매도티커']) # 보유주식 정보 최신화
                        
                        if qty > 0:
                            
                            total_qty = qty
                            qty = float(qty) * 0.5 # 분할 손절
                            
                            sell_qty = math.floor(qty * 1000)/1000 # 소수점 3자리 반내림
                            if(sell_qty < 0.001): sell_qty = 0.001
                            
                            send_message(f"[{symbol_list[sym]['종목명']}]: 2차 손절매 시도 ({sell_qty}/{total_qty}개)")
                            

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
                            
                            send_message(f"[{symbol_list[sym]['종목명']}]: 3차 전량 손절매 시도 ({total_qty}개)")
                            
                            sell_result = upbit.sell_market_order(sym, total_qty)
                            if sell_result is not None:
                                symbol_list[sym]['손절_3차'] = True
                                symbol_list[sym]['손절청산'] = True
                                symbol_list[sym]['매수카운트'] = 5
                                symbol_list[sym]['매수최대량'] = 0
                                symbol_list[sym]['보유'] = False # 전량 손절     
                                send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/avg_price,4)}% 3차 전량 손절매")
                                send_message(f"[{symbol_list[sym]['종목명']}]: 손절가({current_price}) 평단가({avg_price})") 
                            else:
                                send_message(f"매도 실패 ({sell_result})")  

#---------------------- 여기까지 보유중 루프 -----------------------------------------------------------------------------
                            

        # for문 끝 라인..

        time.sleep(1)

        t_now = datetime.datetime.now()
        if t_now.minute == 30 and t_30: 
            t_30 = False
            t_0 = True
            message_list = ""
            message_list += "===30분===30분===30분===30분===\n"
            message_list += "\n"

            for sym in symbol_list:
                if symbol_list[sym]['익절청산']:
                    message_list += f"[{symbol_list[sym]['종목명']}] : ++익절청산++ ^^ \n"
                elif symbol_list[sym]['손절청산']:
                    message_list += f"[{symbol_list[sym]['종목명']}] : --손절청산-- ㅠ \n"

            total_cash = get_balance("KRW") # 현금잔고 조회
            formatted_amount = "{:,.0f}원".format(total_cash)
            message_list += f"현금 잔고: {formatted_amount}\n\n"

            for sym in symbol_list:
                qty = get_balance(symbol_list[sym]['매도티커'])
                if qty > 0:
                    message_list += f"{symbol_list[sym]['종목명']}: {qty}개\n"
                    
                    current_price = get_current_price(sym)
                    total = current_price * qty
                    formatted_amount = "{:,.0f}원".format(total)
                    message_list += f"{symbol_list[sym]['종목명']}: {formatted_amount}\n"
                    total_cash += total

            
            formatted_amount = "{:,.0f}원".format(total_cash)
            message_list += f"보유 자산: {formatted_amount}\n\n"
            send_message(message_list)

        
        if t_now.minute == 0 and t_0:
            t_0 = False
            t_30 = True
            message_list = ""
            message_list += "===0분===0분===0분===0분===\n"
            message_list += "\n"
            
            for sym in symbol_list:
                if symbol_list[sym]['익절청산']:
                    message_list += f"[{symbol_list[sym]['종목명']}] : ++익절청산++ ^^ \n"
                elif symbol_list[sym]['손절청산']:
                    message_list += f"[{symbol_list[sym]['종목명']}] : --손절청산-- ㅠ \n"

            total_cash = get_balance("KRW") # 현금잔고 조회
            formatted_amount = "{:,.0f}원".format(total_cash)
            message_list += f"현금 잔고: {formatted_amount}\n\n"

            for sym in symbol_list:
                qty = get_balance(symbol_list[sym]['매도티커'])
                if qty > 0:
                    message_list += f"{symbol_list[sym]['종목명']}: {qty}개\n"

                    current_price = get_current_price(sym)
                    total = current_price * qty
                    formatted_amount = "{:,.0f}원".format(total)
                    message_list += f"{symbol_list[sym]['종목명']}: {formatted_amount}\n"
                    total_cash += total

            
            formatted_amount = "{:,.0f}원".format(total_cash)
            message_list += f"보유 자산: {formatted_amount}\n\n"
            
            send_message(message_list)


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
