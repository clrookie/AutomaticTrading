import time
import pyupbit
import datetime
import requests
import math

access = "your-access"
secret = "your-secret"

def send_message(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post('https://discord.com/api/webhooks/1200644595919360010/IGX1ctpFUQLHuMchUET2N7qfIkV4VedBfzg3JRppv3SyHAm3v6pV1tGrz-UvLXdnpmBj', data=message)
    print(message)

def get_target_price(ticker): # 음봉 윗꼬리 평균 + 보정

    data_period = 180 # 최근 추출 기간
    cnt = 0 # 음봉 카운트
    target_price = 0 # 초기화
    delta = 0 # 윗꼬리값

    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=data_period)

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

    target_price += delta

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

    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=1)
    stck_oprc = int(df.iloc[0]['open']) #오늘 시가
    
    return stck_oprc

# COIN 자동매매 구동
try:
    
    # 로그인
    access = ""
    secret = ""
    upbit = pyupbit.Upbit(access, secret)
    send_message("=== 코인거래 초기화 합니다 ===")

    last240_hour = 0
    t_0 = True
    t_30 = True

    buy_cnt = 0
    good_sell_cnt = 0
    bad_sell_cnt = 0
    end_sell_cnt = 0

    total_cash = 0

 # 분할매도 기준선
    profit_rate07 = 1.007
    profit_rate12 = 1.012
    profit_rate17 = 1.017
    profit_rate22 = 1.022
    sell_rate = 0.2

    symbol_list = {
    'KRW-BTC':{'종목명':'비트코인',
    '배분예산':0,
    '목표매수가':0,
    '실매수가':0,
    '시가':0,
    '보유':False,
    '예산_가중치':1.0,
    '익절_가중치':1.0,
    'profit_rate07_up':True,
    'profit_rate12_up':True,
    'profit_rate17_up':True,
    'profit_rate22_up':True,
    'profit_rate07_down':False,
    'profit_rate12_down':False,
    'profit_rate17_down':False,
    'profit_rate22_down':False},

    'KRW-ZRX':{'종목명':'제로엑스',
    '배분예산':0,
    '목표매수가':0,
    '실매수가':0,
    '시가':0,
    '보유':False,
    '예산_가중치':1.0,
    '익절_가중치':1.0,
    'profit_rate07_up':True,
    'profit_rate12_up':True,
    'profit_rate17_up':True,
    'profit_rate22_up':True,
    'profit_rate07_down':False,
    'profit_rate12_down':False,
    'profit_rate17_down':False,
    'profit_rate22_down':False},

    'KRW-ETC':{'종목명':'이더리움클래식',
    '배분예산':0,
    '목표매수가':0,
    '실매수가':0,
    '시가':0,
    '보유':False,
    '예산_가중치':1.0,
    '익절_가중치':1.0,
    'profit_rate07_up':True,
    'profit_rate12_up':True,
    'profit_rate17_up':True,
    'profit_rate22_up':True,
    'profit_rate07_down':False,
    'profit_rate12_down':False,
    'profit_rate17_down':False,
    'profit_rate22_down':False},

    'KRW-XRP':{'종목명':'리플',
    '배분예산':0,
    '목표매수가':0,
    '실매수가':0,
    '시가':0,
    '보유':False,
    '예산_가중치':1.0,
    '익절_가중치':1.0,
    'profit_rate07_up':True,
    'profit_rate12_up':True,
    'profit_rate17_up':True,
    'profit_rate22_up':True,
    'profit_rate07_down':False,
    'profit_rate12_down':False,
    'profit_rate17_down':False,
    'profit_rate22_down':False},
    }


    while True:
        
        df = pyupbit.get_ohlcv("KRW-BTC", interval="minute240", count=1)

        if df.index[0].hour != last240_hour:    # 240분 캔들 갱신
            last240_hour = df.index[0].hour
            
            send_message("")
            send_message(f"=== 코인거래 240분봉 갱신합니다 === ({last240_hour}시)")
            send_message("")
    
            t_0 = True
            t_30 = True

            send_message("[last240 매매 카운트]")
            send_message(f" -buy: {buy_cnt}")
            send_message(f" -good Sell: {good_sell_cnt}")
            send_message(f" -bad Sell: {bad_sell_cnt}")
            send_message(f" -end Sell: {end_sell_cnt}")
            
            buy_cnt = 0
            good_sell_cnt = 0
            bad_sell_cnt = 0
            end_sell_cnt = 0

            total_cash = get_balance("KRW") # 현금잔고 조회
        
            formatted_amount = "{:,.0f}원".format(total_cash)
            send_message(f"현금 잔고: {formatted_amount}")

            # 일단 테스팅 ===============================================================================
            total_cash /= 10

            target_buy_count = int(len(symbol_list)) # 매수종목 수량

            for sym in symbol_list: # 있으면 일괄 매도
                coin = get_balance(sym)  # 보유량
                if coin > 0 : # 5000원 이상일 때
                    sell_result = upbit.sell_market_order(sym, coin)
                    send_message(f">>> [{symbol_list[sym]['종목명']}] {coin} 수량을 시가({sell_result})에 매도했습니다~")

            for sym in symbol_list: # 초기화
                send_message(f"[{symbol_list[sym]['종목명']}]")
                symbol_list[sym]['배분예산'] = total_cash * (1/target_buy_count) * symbol_list[sym]['예산_가중치']
                formatted_amount = "{:,.0f}원".format(symbol_list[sym]['배분예산'])
                send_message(f" - 배분예산: {formatted_amount}")

                symbol_list[sym]['시가'] = get_stck_oprc(sym)
                formatted_amount = "{:,.0f}원".format(symbol_list[sym]['시가'])
                send_message(f" - 시가: {formatted_amount}")   

                symbol_list[sym]['목표매수가'] = get_target_price(sym)
                formatted_amount = "{:,.0f}원".format(symbol_list[sym]['목표매수가'])
                send_message(f" - 목표매수가: {formatted_amount}")   

                send_message(f" - 타겟%: {round((symbol_list[sym]['목표매수가'])/symbol_list[sym]['시가'],4)}")

                symbol_list[sym]['보유'] = False
                send_message("---------------------------------")
            
            send_message("")
            send_message("코인 매매를 시작합니다~")
            send_message("")

        else:   # 거래 루프
            for sym in symbol_list:
                current_price = get_current_price(sym)

                if symbol_list[sym]['보유']: # 보유중이면

                    sell_fix = False
                    
                    #상향 익절
                    if current_price > symbol_list[sym]['목표매수가']*profit_rate22*symbol_list[sym]['익절_가중치'] and symbol_list[sym]['profit_rate22_up']:
                        symbol_list[sym]['profit_rate22_up'] = False
                        symbol_list[sym]['profit_rate17_up'] = False
                        symbol_list[sym]['profit_rate12_up'] = False
                        symbol_list[sym]['profit_rate07_up'] = False

                        symbol_list[sym]['profit_rate17_down'] = True
                        symbol_list[sym]['profit_rate12_down'] = True
                        symbol_list[sym]['profit_rate07_down'] = True

                        sell_fix = True

                    elif current_price > symbol_list[sym]['목표매수가']*profit_rate17*symbol_list[sym]['익절_가중치'] and symbol_list[sym]['profit_rate17_up']:
                        symbol_list[sym]['profit_rate17_up'] = False
                        symbol_list[sym]['profit_rate12_up'] = False
                        symbol_list[sym]['profit_rate07_up'] = False

                        symbol_list[sym]['profit_rate12_down'] = True
                        symbol_list[sym]['profit_rate07_down'] = True

                        sell_fix = True

                    elif current_price > symbol_list[sym]['목표매수가']*profit_rate12*symbol_list[sym]['익절_가중치'] and symbol_list[sym]['profit_rate12_up']:
                        symbol_list[sym]['profit_rate12_up'] = False
                        symbol_list[sym]['profit_rate07_up'] = False

                        symbol_list[sym]['profit_rate07_down'] = True

                        sell_fix = True

                    elif current_price > symbol_list[sym]['목표매수가']*profit_rate07*symbol_list[sym]['익절_가중치'] and symbol_list[sym]['profit_rate07_up']:
                        symbol_list[sym]['profit_rate07_up'] = False

                        sell_fix = True

                    # 하향 익절
                    elif current_price <= symbol_list[sym]['목표매수가']*profit_rate17*symbol_list[sym]['익절_가중치'] and symbol_list[sym]['profit_rate17_down']:
                        symbol_list[sym]['profit_rate17_down'] = False

                        symbol_list[sym]['profit_rate22_up'] = True

                        sell_fix = True

                    elif current_price <= symbol_list[sym]['목표매수가']*profit_rate12*symbol_list[sym]['익절_가중치'] and symbol_list[sym]['profit_rate12_down']:
                        symbol_list[sym]['profit_rate12_down'] = False

                        symbol_list[sym]['profit_rate22_up'] = True
                        symbol_list[sym]['profit_rate17_up'] = True

                        sell_fix = True


                    elif current_price <= symbol_list[sym]['목표매수가']*profit_rate07*symbol_list[sym]['익절_가중치'] and symbol_list[sym]['profit_rate07_down']:
                        symbol_list[sym]['profit_rate07_down'] = False

                        symbol_list[sym]['profit_rate22_up'] = True
                        symbol_list[sym]['profit_rate17_up'] = True
                        symbol_list[sym]['profit_rate12_up'] = True

                        sell_fix = True


                    #익절
                    if sell_fix:
                        qty = get_balance(sym) # 보유주식 정보 최신화 

                        if qty > 0:
                            sell_qty = math.floor(symbol_list[sym]['배분예산']/current_price*1000)/1000  # 소수점 3자리 반내림
                            sell_qty *= sell_rate

                            if qty > sell_qty: # sell_rate 분할매도
                                qty = sell_qty

                            sell_result = upbit.sell_market_order(sym, qty)
                            
                            good_sell_cnt += 1
                            send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/symbol_list[sym]['실매수가'],4)}% 익절매합니다 ^^")
                            
                            continue
                        

                    #시가 손절 : 99.5% 보정
                    elif(symbol_list[sym]['시가']*0.995 > current_price): # 오늘 시가 보다 떨어지면 
                                     
                        qty = get_balance(sym) # 보유주식 정보 최신화
                        
                        if qty > 0:
                            sell_result = upbit.sell_market_order(sym, qty)
                            
                            symbol_list[sym]['보유'] = False      
                            bad_sell_cnt += 1
                            send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/symbol_list[sym]['실매수가'],4)}% 시가 손절매합니다 ㅠ")
                            continue

                    
                    continue # 보유 주식 있으면 매수하지 않는다.

                # 목표가 매수
                elif symbol_list[sym]['목표매수가'] <= current_price and symbol_list[sym]['보유'] == False:
                    
                    qty = math.floor(symbol_list[sym]['배분예산']/current_price*1000)/1000  # 소수점 3자리 반내림
                    if qty > 0:
                        sell_result = upbit.buy_market_order(sym, qty)
                        send_message(sell_result)
                        buy_cnt += 1
                        symbol_list[sym]['실매수가'] = current_price
                        symbol_list[sym]['보유'] = True

                        send_message(f"[{symbol_list[sym]['종목명']}] -+-+-매수 성공-+-+-")
                        
                        formatted_amount = "{:,.0f}원".format(symbol_list[sym]['목표매수가'])
                        send_message(f" - 목표매수가: {formatted_amount}")   

                        formatted_amount = "{:,.0f}원".format(symbol_list[sym]['실매수가'])
                        qty = get_balance(sym) # 보유주식 정보 최신화
                        send_message(f" - 실매수가: {formatted_amount} / 수량({qty})")

                        #분할매도 조건 초기화
                        symbol_list[sym]['profit_rate07_up'] = True
                        symbol_list[sym]['profit_rate12_up'] = True
                        symbol_list[sym]['profit_rate17_up'] = True
                        symbol_list[sym]['profit_rate22_up'] = True
                        symbol_list[sym]['profit_rate07_down'] = False
                        symbol_list[sym]['profit_rate12_down'] = False
                        symbol_list[sym]['profit_rate17_down'] = False
                        symbol_list[sym]['profit_rate22_down'] = False

        # for문 끝 라인..

        time.sleep(1)

        t_now = datetime.datetime.now()
        if t_now.minute == 30 and t_30: 
            t_30 = False
            t_0 = True
            send_message("")
            send_message("===30분===30분===30분===30분===")
            send_message("")
            total_cash = get_balance("KRW") # 현금잔고 조회
            formatted_amount = "{:,.0f}원".format(total_cash)
            send_message(f"현금 잔고: {formatted_amount}")

            for sym in symbol_list:
                qty = get_balance(sym)
                if qty > 0:
                    send_message(f"{symbol_list[sym]['종목명']}: {qty}개 보유중")
        
        if t_now.minute == 0 and t_0:
            t_0 = False
            t_30 = True
            send_message("")
            send_message("===0분===0분===0분===0분===")
            send_message("")
            total_cash = get_balance("KRW") # 현금잔고 조회
            formatted_amount = "{:,.0f}원".format(total_cash)
            send_message(f"현금 잔고: {formatted_amount}")

            for sym in symbol_list:
                qty = get_balance(sym)
                if qty > 0:
                    send_message(f"{symbol_list[sym]['종목명']}: {qty}개 보유중")


except Exception as e:
    print(e)
    send_message(f"[오류 발생]{e}")
    time.sleep(1)
