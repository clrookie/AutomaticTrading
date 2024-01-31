import requests
import json
import datetime
from pytz import timezone
import time
import yaml

# Nasdaq


with open('config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL_USA']
URL_BASE = _cfg['URL_BASE']

def send_message(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    print(message)

def get_access_token():
    """토큰 발급"""
    headers = {"content-type":"application/json"}
    body = {"grant_type":"client_credentials",
    "appkey":APP_KEY, 
    "appsecret":APP_SECRET}
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    ACCESS_TOKEN = res.json()["access_token"]
    return ACCESS_TOKEN
    
def hashkey(datas): #사고팔때 필요함
    """암호화"""
    PATH = "uapi/hashkey"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
    'content-Type' : 'application/json',
    'appKey' : APP_KEY,
    'appSecret' : APP_SECRET,
    }
    res = requests.post(URL, headers=headers, data=json.dumps(datas))
    hashkey = res.json()["HASH"]
    return hashkey

# 뉴욕증시 함수
def get_holiday(day="YYYYMMDD"):
    date = ["20240219",
    "20240329",
    "20240527",
    "20240619",
    "20240704",
    "20240902",
    "20241128",
    "20241225"]

    i =""
    for i in date:
        if i == day:
            return True
    return False

def get_current_price(market="NAS", code="AAPL"):
    """현재가 조회"""
    PATH = "uapi/overseas-price/v1/quotations/price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey":APP_KEY,
            "appSecret":APP_SECRET,
            "tr_id":"HHDFS00000300"}
    params = {
        "AUTH": "",
        "EXCD":market,
        "SYMB":code,
    }
    res = requests.get(URL, headers=headers, params=params)
    return float(res.json()['output']['last'])

def get_stck_oprc(market="NAS", code="AAPL"):
    PATH = "uapi/overseas-price/v1/quotations/dailyprice"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"HHDFS76240000"}
    params = {
        "AUTH":"",
        "EXCD":market,
        "SYMB":code,
        "GUBN":"0",
        "BYMD":"",
        "MODP":"0"
    }
    res = requests.get(URL, headers=headers, params=params)

    stck_oprc = float(res.json()['output2'][0]['open']) #오늘 시가
    
    return stck_oprc

def get_target_price_new(market="NAS", code="AAPL"): # 음봉 윗꼬리 평균 + 보정
    PATH = "uapi/overseas-price/v1/quotations/dailyprice"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"HHDFS76240000"}
    params = {
        "AUTH":"",
        "EXCD":market,
        "SYMB":code,
        "GUBN":"0",
        "BYMD":"",
        "MODP":"0"
    }
    res = requests.get(URL, headers=headers, params=params)

    data_period = 30 # 최근 추출 기간
    cnt = 0 # 음봉 카운트

    target_price = 0 # 초기화
    delta = 0 # 윗꼬리값

    for i in range(0,data_period):
        stck_hgpr = float(res.json()['output2'][i]['high']) #고가
        stck_clpr = float(res.json()['output2'][i]['clos']) #종가
        stck_oprc = float(res.json()['output2'][i]['open']) #시가

        if stck_oprc >= stck_clpr : #음봉
            delta += stck_hgpr - stck_oprc
            cnt += 1

    target_price = float(res.json()['output2'][0]['open']) #오늘 시가
    
    if cnt > 0:
        delta /= cnt # 평균

    target_price += delta

    return target_price

def get_real_total():
    PATH = "uapi/overseas-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTS3012R",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",
        "TR_CRCY_CD": "USD",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": ""
    }
    res = requests.get(URL, headers=headers, params=params)

    evaluation1 = float(res.json()['output2']['tot_evlu_pfls_amt'])
    evaluation2 = float(res.json()['output2']['tot_pftrt'])

    
    return evaluation1, evaluation2

def get_stock_balance():
    """주식 잔고조회"""
    PATH = "uapi/overseas-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"JTTT3012R",
        "custtype":"P"
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",
        "TR_CRCY_CD": "USD",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    send_message(f"====주식 보유잔고====")
    for stock in stock_list:
        if int(stock['ovrs_cblc_qty']) > 0:
            stock_dict[stock['ovrs_pdno']] = stock['ovrs_cblc_qty']
            send_message(f"{stock['ovrs_item_name']}({stock['ovrs_pdno']}): {stock['ovrs_cblc_qty']}주")
            time.sleep(0.1)
    send_message(f"주식 평가 금액: ${evaluation['tot_evlu_pfls_amt']}")
    time.sleep(0.1)
    send_message(f"평가 손익 합계: ${evaluation['ovrs_tot_pfls']}")
    time.sleep(0.1)
    send_message(f"=================")
    return stock_dict

def get_balance():
    """현금 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8908R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "005930",
        "ORD_UNPR": "65500",
        "ORD_DVSN": "01",
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "OVRS_ICLD_YN": "Y"
    }
    res = requests.get(URL, headers=headers, params=params)
    cash = res.json()['output']['ord_psbl_cash']
    send_message("===============================")
    formatted_amount = "{:,.0f}원".format(int(cash))
    send_message(f"현금 잔고: {formatted_amount}")
    return int(cash)

def buy(market="NASD", code="AAPL", qty="1", price="0"):
    """미국 주식 지정가 매수"""
    PATH = "uapi/overseas-stock/v1/trading/order"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": market,
        "PDNO": code,
        "ORD_DVSN": "00",
        "ORD_QTY": str(int(qty)),
        "OVRS_ORD_UNPR": f"{round(price,2)}",
        "ORD_SVR_DVSN_CD": "0"
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"JTTT1002U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(f"-+-+-매수 성공-+-+-")
        return True
    else:
        send_message(f"[매수 실패]{str(res.json())}")
        return False

def sell(market="NASD", code="AAPL", qty="1", price="0"):
    """미국 주식 지정가 매도"""
    PATH = "uapi/overseas-stock/v1/trading/order"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": market,
        "PDNO": code,
        "ORD_DVSN": "00",
        "ORD_QTY": str(int(qty)),
        "OVRS_ORD_UNPR": f"{round(price,2)}",
        "ORD_SVR_DVSN_CD": "0"
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"JTTT1006U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(f"-#-#-매도 성공-#-#-")
        return True
    else:
        send_message(f"[매도 실패]{str(res.json())}")
        return False

def get_exchange_rate():
    """환율 조회"""
    PATH = "uapi/overseas-stock/v1/trading/inquire-present-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey":APP_KEY,
            "appSecret":APP_SECRET,
            "tr_id":"CTRP6504R"}
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "OVRS_EXCG_CD": "NASD",
        "WCRC_FRCR_DVSN_CD": "01",
        "NATN_CD": "840",
        "TR_MKET_CD": "01",
        "INQR_DVSN_CD": "00"
    }
    res = requests.get(URL, headers=headers, params=params)
    exchange_rate = 1270.0
    if len(res.json()['output2']) > 0:
        exchange_rate = float(res.json()['output2'][0]['frst_bltn_exrt'])
    return exchange_rate

# 자동 매매 코드
try:        
    send_message("")
    send_message("=== 뉴욕증시를 초기화합니다 ===")
    send_message("")
    
    holiday = False
    startoncebyday = False
    t_0 = True
    t_30 = True

    buy_cnt = 0
    good_sell_cnt = 0
    bad_sell_cnt = 0
    end_sell_cnt = 0

    # 분할매도 기준선
    profit_rate07 = 1.007
    profit_rate12 = 1.012
    profit_rate17 = 1.017
    profit_rate22 = 1.022
    
    # 익절비율
    sell_rate = 0.2
    
    # 매수비율
    buy_rate = 0.33
    
    # 시가 분할손절 기준선
    loss_cut1 = 0.996
    loss_cut2 = 0.991
    loss_cut3 = 0.986

    # 공용 데이터
    common_data ={
    '배분예산':0,
    '목표매수가':0,
    '목표매수가_up': False,
    '목표매수가_down': False,
    '실매수가':0,
    '시가':0,
    '보유':False,
        
    '최대보유':0,
    '매수_1차': False,
    '매수_2차': False,
    '매수_3차': False,
    '손절_1차': False,
    '손절_2차': False,
    '손절_3차': False,
        
    'profit_rate07_up':True,
    'profit_rate12_up':True,
    'profit_rate17_up':True,
    'profit_rate22_up':True,
    'profit_rate07_down':False,
    'profit_rate12_down':False,
    'profit_rate17_down':False
    }

    #개별 종목 데이터
    symbol_list = {
    'DDM':{'종목명':'다우_레버리지X2', #1
    '마켓':'AMS',
    '마켓_sb':'AMEX',
    '예산_가중치':1.35,
    '익절_가중치':0.65,
    **common_data},

    'DXD':{'종목명':'다우_인버스X2', #2
    '마켓':'AMS',
    '마켓_sb':'AMEX',
    '예산_가중치':1.35,
    '익절_가중치':0.65,
    **common_data},

    'SSO':{'종목명':'S&P_레버리지X2', #3
    '마켓':'AMS',
    '마켓_sb':'AMEX',
    '예산_가중치':1.35,
    '익절_가중치':0.65,
    **common_data},

    'SDS':{'종목명':'S&P_인버스X2', #4
    '마켓':'AMS',
    '마켓_sb':'AMEX',
    '예산_가중치':1.35,
    '익절_가중치':0.65,
    **common_data},

    'QLD':{'종목명':'나스닥_레버리지X2', #5
    '마켓':'AMS',
    '마켓_sb':'AMEX',
    '예산_가중치':1.35,
    '익절_가중치':0.65,
    **common_data},

    'QID':{'종목명':'나스닥 인버스X2', #6
    '마켓':'AMS',
    '마켓_sb':'AMEX',
    '예산_가중치':1.35,
    '익절_가중치':0.65,
    **common_data},         
    # ---------
    'UDOW':{'종목명':'다우_레버리지X3', #7
    '마켓':'AMS',
    '마켓_sb':'AMEX',
    '예산_가중치':1,
    '익절_가중치':1,
    **common_data},

    'SDOW':{'종목명':'다우_인버스X3',   #8
    '마켓':'AMS',
    '마켓_sb':'AMEX',
    '예산_가중치':1,
    '익절_가중치':1,
    **common_data},

    'UPRO':{'종목명':'S&P_레버리지X3',  #9
    '마켓':'AMS',
    '마켓_sb':'AMEX',
    '예산_가중치':1,
    '익절_가중치':1,
    **common_data},

    'SPXU':{'종목명':'S&P_인버스X3', #10
    '마켓':'AMS',
    '마켓_sb':'AMEX',
    '예산_가중치':1,
    '익절_가중치':1,
    **common_data},

    'TQQQ':{'종목명':'나스닥_레버리지X3',   #11
    '마켓':'NAS',
    '마켓_sb':'NASD',
    '예산_가중치':1,
    '익절_가중치':1,
    **common_data},

    'SQQQ':{'종목명':'나스닥 인버스X3', #12
    '마켓':'NAS',
    '마켓_sb':'NASD',
    '예산_가중치':1,
    '익절_가중치':1,
    **common_data},            
    }

    while True:
        t_now = datetime.datetime.now(timezone('America/New_York')) # 뉴욕 기준 현재 시간
        today = t_now.weekday()
        today_date = t_now.strftime("%Y%m%d")
        
        if today == 5 or today == 6 or get_holiday(today_date):  # 토,일 자동종료, 2024 공휴일 포함
            if holiday == False:
                send_message("뉴욕증시 휴장일 입니다~")
                holiday = True
            continue
        else:
            t_now = datetime.datetime.now(timezone('America/New_York')) # 뉴욕 기준 현재 시간
            
            t_ready = t_now.replace(hour=9, minute=31, second=0, microsecond=0)
            t_start = t_now.replace(hour=9, minute=41, second=0, microsecond=0)
            t_10 = t_now.replace(hour=10, minute=0, second=0, microsecond=0)
            t_1330 = t_now.replace(hour=13, minute=30, second=0, microsecond=0)
            t_1550 = t_now.replace(hour=15, minute=40, second=0, microsecond=0)
            t_exit = t_now.replace(hour=15, minute=50, second=0,microsecond=0)
            
            if t_ready < t_now < t_exit and startoncebyday == False: # 매매 준비
            
                send_message("")
                send_message("=== 뉴욕증시 자동매매를 준비합니다 ===")
                send_message("")

                
                # 토큰 세팅
                ACCESS_TOKEN = get_access_token()
                
                startoncebyday = True
                holiday = False
                
                t_0 = True
                t_30 = True
                            
                buy_cnt = 0
                good_sell_cnt = 0
                bad_sell_cnt = 0
                end_sell_cnt = 0
                
                total_cash = get_balance() # 보유 현금 조회
                exchange_rate = get_exchange_rate() # 환율 조회

                # 일단 200만원으로 테스팅 ===============================================================================
                # total_cash /= 5 

                stock_dict = get_stock_balance() # 보유 주식 조회
                target_buy_count = int(len(symbol_list)) # 매수종목 수량

                for sym, qty in stock_dict.items(): # 있으면 일괄 매도
                    
                    send_message(f">>> [{symbol_list[sym]['종목명']}] {get_current_price(symbol_list[sym]['마켓'],sym)}$에 매도 시도 ({sym}개)")

                    if sell(symbol_list[sym]['마켓_sb'], sym, int(qty),get_current_price(symbol_list[sym]['마켓'],sym)):
                        send_message(f">>> open [{symbol_list[sym]['종목명']}] 일괄 매도 성공 !!")


                for sym in symbol_list: # 초기화

                    send_message(f"[{symbol_list[sym]['종목명']}]")
                    symbol_list[sym]['배분예산'] = round(((total_cash * (1/target_buy_count))*symbol_list[sym]['예산_가중치'] / exchange_rate),4) # 환율 적용
                    formatted_amount = "{:,.4f}$".format(symbol_list[sym]['배분예산'])
                    send_message(f" - 배분예산: {formatted_amount}")

                    symbol_list[sym]['시가'] = round(get_stck_oprc(symbol_list[sym]['마켓'],sym),4)
                    formatted_amount = "{:,.4f}$".format(symbol_list[sym]['시가'])
                    send_message(f" - 시가: {formatted_amount}")   

                    symbol_list[sym]['목표매수가'] = round(get_target_price_new(symbol_list[sym]['마켓'],sym),4)
                    formatted_amount = "{:,.4f}$".format(symbol_list[sym]['목표매수가'])
                    send_message(f" - 목표매수가: {formatted_amount}")   

                    send_message(f" - 타겟%: {round((symbol_list[sym]['목표매수가'])/symbol_list[sym]['시가'],4)}")

                    symbol_list[sym]['보유'] = False
                    symbol_list[sym]['최대보유'] = 0
                    symbol_list[sym]['매수_1차'] = False
                    symbol_list[sym]['매수_2차'] = False
                    symbol_list[sym]['매수_3차'] = False
                    symbol_list[sym]['손절_1차'] = False
                    symbol_list[sym]['손절_2차'] = False
                    symbol_list[sym]['손절_3차'] = False
                    symbol_list[sym]['목표매수가_down'] = False
                    send_message("---------------------------------")
                    

                send_message("")
                send_message("9시 40분부터 매매를 시작합니다~~")
                send_message("")

            if t_start < t_now < t_exit and startoncebyday == True:  # AM 09:40 ~ PM 03:58 : 매수

                for sym in symbol_list:
                    current_price = get_current_price(symbol_list[sym]['마켓'],sym)

                    # 반템포 늦은 장진입 시, 목표매수가 밑에서 매수하려고..
                    if current_price < symbol_list[sym]['목표매수가'] and symbol_list[sym]['목표매수가_down'] == False:
                        symbol_list[sym]['목표매수가_down'] = True
                        send_message(f"[{symbol_list[sym]['종목명']}] 목표매수가 보다 하향~")

                    if symbol_list[sym]['보유']: # 보유중이면

                        sell_fix = False
                        
                        #상향 익절
                        if current_price > symbol_list[sym]['목표매수가']*(((profit_rate22-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate22_up']:
                            symbol_list[sym]['profit_rate22_up'] = False
                            symbol_list[sym]['profit_rate17_up'] = False
                            symbol_list[sym]['profit_rate12_up'] = False
                            symbol_list[sym]['profit_rate07_up'] = False

                            symbol_list[sym]['profit_rate17_down'] = True
                            symbol_list[sym]['profit_rate12_down'] = True
                            symbol_list[sym]['profit_rate07_down'] = True

                            sell_fix = True

                        elif current_price > symbol_list[sym]['목표매수가']*(((profit_rate17-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate17_up']:
                            symbol_list[sym]['profit_rate17_up'] = False
                            symbol_list[sym]['profit_rate12_up'] = False
                            symbol_list[sym]['profit_rate07_up'] = False

                            symbol_list[sym]['profit_rate12_down'] = True
                            symbol_list[sym]['profit_rate07_down'] = True

                            sell_fix = True

                        elif current_price > symbol_list[sym]['목표매수가']*(((profit_rate12-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate12_up']:
                            symbol_list[sym]['profit_rate12_up'] = False
                            symbol_list[sym]['profit_rate07_up'] = False

                            symbol_list[sym]['profit_rate07_down'] = True

                            sell_fix = True

                        elif current_price > symbol_list[sym]['목표매수가']*(((profit_rate07-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate07_up']:
                            symbol_list[sym]['profit_rate07_up'] = False

                            sell_fix = True

                        # 하향 익절
                        elif current_price <= symbol_list[sym]['목표매수가']*(((profit_rate17-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate17_down']:
                            symbol_list[sym]['profit_rate17_down'] = False

                            symbol_list[sym]['profit_rate22_up'] = True

                            sell_fix = True

                        elif current_price <= symbol_list[sym]['목표매수가']*(((profit_rate12-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate12_down']:
                            symbol_list[sym]['profit_rate12_down'] = False

                            symbol_list[sym]['profit_rate22_up'] = True
                            symbol_list[sym]['profit_rate17_up'] = True

                            sell_fix = True


                        elif current_price <= symbol_list[sym]['목표매수가']*(((profit_rate07-1)*symbol_list[sym]['익절_가중치'])+1) and symbol_list[sym]['profit_rate07_down']:
                            symbol_list[sym]['profit_rate07_down'] = False

                            symbol_list[sym]['profit_rate22_up'] = True
                            symbol_list[sym]['profit_rate17_up'] = True
                            symbol_list[sym]['profit_rate12_up'] = True

                            sell_fix = True


                        # 익절 하거나,,
                        if sell_fix:
                            stock_dict = get_stock_balance() # 보유주식 최신화
                            for symtemp, qty in stock_dict.items():
                                if sym == symtemp:
                                    qty = int(qty)
                                    sell_qty = int(float(symbol_list[sym]['최대보유']) * sell_rate)
                                    if sell_qty < 1:
                                        sell_qty = 1

                                    if qty > sell_qty: # 분할 익절
                                        send_message(f"[{symbol_list[sym]['종목명']}]: 분할 익절 시도 ({sell_qty}/{qty}개)")
                                        qty = sell_qty
                                    else:
                                        symbol_list[sym]['보유'] = False # 전량 익절
                                        send_message(f"[{symbol_list[sym]['종목명']}]: 전량 익절 시도 ({qty}개)")

                                    current_price = get_current_price(symbol_list[sym]['마켓'],sym) # 가격 최신화
                                    if sell(symbol_list[sym]['마켓_sb'], sym, qty, current_price):
                                        send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/symbol_list[sym]['실매수가'],4)}% 익절매 성공 ^^")
                                        send_message(f"[{symbol_list[sym]['종목명']}]: 익절가({current_price}) 실매수가({symbol_list[sym]['실매수가']})")            
                            
                        # 1차 손절하거나
                        elif(symbol_list[sym]['시가']*loss_cut1 > current_price and symbol_list[sym]['손절_1차'] == False):
                            stock_dict = get_stock_balance() # 보유주식 정보 최신화
                            for symtemp, qty in stock_dict.items():
                                if sym == symtemp:
                                    total_qty = qty
                                    qty = float(qty) * 0.34 # 분할 손절
                                    if qty < 1:
                                        qty = 1
                                    else:
                                        qty = int(qty)
                                    
                                    send_message(f"[{symbol_list[sym]['종목명']}]: 1차 손절매 시도 ({qty}/{total_qty}개)")
                                    current_price = get_current_price(symbol_list[sym]['마켓'],sym) # 가격 최신화
                                    if sell(symbol_list[sym]['마켓_sb'], sym, qty, current_price):
                                        symbol_list[sym]['손절_1차'] = True         
                                        symbol_list[sym]['최대보유'] -= qty # 최대보유 감소
                                        send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/symbol_list[sym]['실매수가'],4)}% 1차 손절매 성공")
                                        send_message(f"[{symbol_list[sym]['종목명']}]: 손절가({current_price}) 실매수가({symbol_list[sym]['실매수가']})")      
                        # 2차 손절
                        elif(symbol_list[sym]['시가']*loss_cut2 > current_price and symbol_list[sym]['손절_2차'] == False):
                            stock_dict = get_stock_balance() # 보유주식 정보 최신화
                            for symtemp, qty in stock_dict.items():
                                if sym == symtemp:
                                    total_qty = qty
                                    qty = float(qty) * 0.5 # 분할 손절
                                    if qty < 1:
                                        qty = 1
                                    else:
                                        qty = int(qty)

                                    send_message(f"[{symbol_list[sym]['종목명']}]: 2차 손절매 시도 ({qty}/{total_qty}개)")
                                    
                                    current_price = get_current_price(symbol_list[sym]['마켓'],sym)
                                    if sell(symbol_list[sym]['마켓_sb'], sym, qty, current_price):
                                        symbol_list[sym]['손절_2차'] = True            
                                        symbol_list[sym]['최대보유'] -= qty # 최대보유 감소
                                        send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/symbol_list[sym]['실매수가'],4)}% 2차 손절매 성공")
                                        send_message(f"[{symbol_list[sym]['종목명']}]: 손절가({current_price}) 실매수가({symbol_list[sym]['실매수가']})")     
                        # 3차 손절
                        elif(symbol_list[sym]['시가']*loss_cut3 > current_price and symbol_list[sym]['손절_3차'] == False):
                            stock_dict = get_stock_balance() # 보유주식 정보 최신화
                            for symtemp, qty in stock_dict.items():
                                if sym == symtemp: # 전량 손절
                                    
                                    send_message(f"[{symbol_list[sym]['종목명']}]: 3차 전량 손절매 시도 ({qty}개)")
                                    
                                    current_price = get_current_price(symbol_list[sym]['마켓'],sym)
                                    if sell(symbol_list[sym]['마켓_sb'], sym, int(qty), current_price):
                                        symbol_list[sym]['손절_3차'] = True
                                        
                                        # 1차 매수 unlock... ;;
                                        symbol_list[sym]['보유'] = False
                                        symbol_list[sym]['최대보유'] = 0
                                        symbol_list[sym]['매수_1차'] = False
                                        symbol_list[sym]['매수_2차'] = False
                                        symbol_list[sym]['매수_3차'] = False  

                                        send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/symbol_list[sym]['실매수가'],4)}% 3차 손절매 성공")
                                        send_message(f"[{symbol_list[sym]['종목명']}]: 손절가({current_price}) 실매수가({symbol_list[sym]['실매수가']})")     
                        
#---------------------- 보유중 루프 -----------------------------------------------------------------------------

                    # 보유하고 있던 아니던,,
                    # 목표가 1차 매수
                    if symbol_list[sym]['목표매수가_down'] == True and symbol_list[sym]['목표매수가'] < current_price and symbol_list[sym]['매수_1차'] == False:

                        qty = int((symbol_list[sym]['배분예산'] // current_price) * buy_rate) # 33% 분할 매수
                        send_message(f"[{symbol_list[sym]['종목명']}] 1차 매수 시도 ({qty}개)")
                        if qty > 0:
                            if buy(symbol_list[sym]['마켓_sb'], sym, qty, current_price):
                                
                                symbol_list[sym]['매수_1차'] = True
                                symbol_list[sym]['최대보유'] += qty  # 익절매 분할 기준값
                                symbol_list[sym]['실매수가'] = current_price
                                symbol_list[sym]['보유'] = True

                                # 손절 1차 unlock... ;;
                                symbol_list[sym]['손절_1차'] = False
                                symbol_list[sym]['손절_2차'] = False
                                symbol_list[sym]['손절_3차'] = False  

                                send_message(f"[{symbol_list[sym]['종목명']}] 1차 매수")
                                
                                formatted_amount = "{:,.4f}$".format(symbol_list[sym]['목표매수가'])
                                send_message(f" - 목표매수가: {formatted_amount}")   
                                formatted_amount = "{:,.4f}$".format(symbol_list[sym]['실매수가'])
                                send_message(f" - **실매수가**: {formatted_amount}")
                                formatted_amount = "{:,.4f}$".format(symbol_list[sym]['시가'])
                                send_message(f" - 시가: {formatted_amount}")

                                #분할매도 조건 초기화
                                symbol_list[sym]['profit_rate07_up'] = True
                                symbol_list[sym]['profit_rate12_up'] = True
                                symbol_list[sym]['profit_rate17_up'] = True
                                symbol_list[sym]['profit_rate22_up'] = True
                                symbol_list[sym]['profit_rate07_down'] = False
                                symbol_list[sym]['profit_rate12_down'] = False
                                symbol_list[sym]['profit_rate17_down'] = False
                                
                                time.sleep(3)
                                stock_dict= get_stock_balance()
                    
                    elif t_now < t_1330:    # 점심 이후로 추매 안함
                        middle_target   = (((symbol_list[sym]['목표매수가']-symbol_list[sym]['시가'])/1.136)+symbol_list[sym]['시가'])
                        last_target     = (((symbol_list[sym]['목표매수가']-symbol_list[sym]['시가'])/1.333)+symbol_list[sym]['시가'])

                        # 2차 매수
                        if (middle_target > current_price and
                            symbol_list[sym]['매수_1차'] == True and
                            symbol_list[sym]['매수_2차'] == False):
                            
                            qty = int((symbol_list[sym]['배분예산'] // current_price) * buy_rate) # 33% 분할 매수
                            send_message(f"[{symbol_list[sym]['종목명']}] 2차 매수 시도 ({qty}개)")
                            if qty > 0:
                                if buy(symbol_list[sym]['마켓_sb'], sym, qty, current_price):
                                    
                                    symbol_list[sym]['매수_2차'] = True
                                    symbol_list[sym]['최대보유'] += qty  # 익절매 분할 기준값
                                    symbol_list[sym]['실매수가'] = current_price
                                    symbol_list[sym]['보유'] = True

                                    send_message(f"[{symbol_list[sym]['종목명']}] 2차 매수 성공")
                                    formatted_amount = "{:,.4f}$".format(symbol_list[sym]['목표매수가'])
                                    send_message(f" - 목표매수가: {formatted_amount}")   
                                    formatted_amount = "{:,.4f}$".format(symbol_list[sym]['실매수가'])
                                    send_message(f" - **실매수가**: {formatted_amount}")
                                    formatted_amount = "{:,.4f}$".format(symbol_list[sym]['시가'])
                                    send_message(f" - 시가: {formatted_amount}")

                                    #분할매도 조건 초기화
                                    symbol_list[sym]['profit_rate07_up'] = True
                                    symbol_list[sym]['profit_rate12_up'] = True
                                    symbol_list[sym]['profit_rate17_up'] = True
                                    symbol_list[sym]['profit_rate22_up'] = True
                                    symbol_list[sym]['profit_rate07_down'] = False
                                    symbol_list[sym]['profit_rate12_down'] = False
                                    symbol_list[sym]['profit_rate17_down'] = False
                                    
                                    time.sleep(3)
                                    stock_dict= get_stock_balance()

                        # 3차 매수
                        elif (last_target > current_price and
                            symbol_list[sym]['매수_1차'] == True and
                            symbol_list[sym]['매수_2차'] == True and
                            symbol_list[sym]['매수_3차'] == False):


                            qty = int((symbol_list[sym]['배분예산'] // current_price) * buy_rate) # 33% 분할 매수
                            send_message(f"[{symbol_list[sym]['종목명']}] 3차 매수 시도 ({qty}개)")
                            if qty > 0:
                                if buy(symbol_list[sym]['마켓_sb'], sym, qty, current_price):
                                    
                                    symbol_list[sym]['매수_3차'] = True
                                    symbol_list[sym]['최대보유'] += qty  # 익절매 분할 기준값
                                    symbol_list[sym]['실매수가'] = current_price
                                    symbol_list[sym]['보유'] = True

                                    send_message(f"[{symbol_list[sym]['종목명']}] 3차 매수 성공")
                                    formatted_amount = "{:,.4f}$".format(symbol_list[sym]['목표매수가'])
                                    send_message(f" - 목표매수가: {formatted_amount}")   
                                    formatted_amount = "{:,.4f}$".format(symbol_list[sym]['실매수가'])
                                    send_message(f" - **실매수가**: {formatted_amount}")
                                    formatted_amount = "{:,.4f}$".format(symbol_list[sym]['시가'])
                                    send_message(f" - 시가: {formatted_amount}")

                                    #분할매도 조건 초기화
                                    symbol_list[sym]['profit_rate07_up'] = True
                                    symbol_list[sym]['profit_rate12_up'] = True
                                    symbol_list[sym]['profit_rate17_up'] = True
                                    symbol_list[sym]['profit_rate22_up'] = True
                                    symbol_list[sym]['profit_rate07_down'] = False
                                    symbol_list[sym]['profit_rate12_down'] = False
                                    symbol_list[sym]['profit_rate17_down'] = False
                                    
                                    time.sleep(3)
                                    stock_dict= get_stock_balance()

#---------------------- 분할 매수 루프 -----------------------------------------------------------------------------
                                
                if t_now.minute == 30 and t_30: 
                    t_30 = False
                    t_0 = True
                    send_message("")
                    send_message("===30분===30분===30분===30분===")
                    send_message("")
                    get_stock_balance()
                if t_now.minute == 0 and t_0:
                    t_0 = False
                    t_30 = True
                    send_message("")
                    send_message("===0분===0분===0분===0분===")
                    send_message("")
                    get_stock_balance()
                
                # 서비스 정책상 (1초 20건 한계)
                if t_start <= t_now < t_10:
                    time.sleep(1)
                elif t_1550 <= t_now < t_exit:
                    time.sleep(1)
                else:
                    time.sleep(15)

            if t_exit < t_now and startoncebyday == True:  # PM 03:19 ~ : 데일리 프로그램 종료
                startoncebyday = False

                send_message(f"=데일리 일괄매도=")
                stock_dict = get_stock_balance()
                for sym, qty in stock_dict.items(): # 있으면 일괄 매도
                    current_price = get_current_price(symbol_list[sym]['마켓'],sym)
                    if sell(symbol_list[sym]['마켓_sb'], sym, int(qty), current_price):
                        send_message(f">>> [{symbol_list[sym]['종목명']}]: 현재가 {get_current_price(symbol_list[sym]['마켓'],sym)} / 매수가 {symbol_list[sym]['목표매수가']}")
                        send_message(f">>> [{symbol_list[sym]['종목명']}]: {round(get_current_price(symbol_list[sym]['마켓'],sym)/symbol_list[sym]['목표매수가'],4)}% 매도합니다")
                    else:   # 매도 실패하면 1번더 시도
                        current_price = get_current_price(symbol_list[sym]['마켓'],sym)
                        sell(symbol_list[sym]['마켓_sb'], sym, int(qty), current_price)
                        send_message(f">>> retry [{symbol_list[sym]['종목명']}]: 현재가 {get_current_price(symbol_list[sym]['마켓'],sym)} / 매수가 {symbol_list[sym]['목표매수가']}")
                        send_message(f">>> retry [{symbol_list[sym]['종목명']}]: {round(get_current_price(symbol_list[sym]['마켓'],sym)/symbol_list[sym]['목표매수가'],4)}% 매도합니다")
                send_message(f"---")

                
                # send_message("[매매 카운트]")
                # send_message(f" -buy: {buy_cnt}")
                # send_message(f" -good Sell: {good_sell_cnt}")
                # send_message(f" -bad Sell: {bad_sell_cnt}")
                # send_message(f" -end Sell: {end_sell_cnt}")

    
                a,b = get_real_total()
                send_message("")
                formatted_amount = "{:,.4f}$".format(a)
                send_message(f"총평가손익금액: {formatted_amount}")

                formatted_amount = "{:,.4f}%".format(b)
                send_message(f"총수익율: {formatted_amount}")
                send_message("")

                send_message("=== 뉴욕증시 자동매매를 종료합니다 ===")
                continue
except Exception as e:
    send_message(f"[오류 발생]{e}")
    time.sleep(1)


