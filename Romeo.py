import requests
import json
import datetime
import time
import yaml

#git git git


with open('config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL']
URL_BASE = _cfg['URL_BASE']

def send_message(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[[KOSPI]{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
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

def get_current_price(code="005930"):
    """현재가 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey":APP_KEY,
            "appSecret":APP_SECRET,
            "tr_id":"FHKST01010100"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    }
    res = requests.get(URL, headers=headers, params=params)
    return int(res.json()['output']['stck_prpr'])

def get_stck_oprc(code="005930"):
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"FHKST01010400"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    "fid_org_adj_prc":"1",
    "fid_period_div_code":"D"
    }
    res = requests.get(URL, headers=headers, params=params)

    stck_oprc = int(res.json()['output'][0]['stck_oprc']) #오늘 시가
    
    return stck_oprc


def get_hotstart(code="005930"):
    """ 오늘 시가 갭상 여부 체크"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"FHKST01010400"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    "fid_org_adj_prc":"1",
    "fid_period_div_code":"D"
    }
    res = requests.get(URL, headers=headers, params=params)

    stck_clpr = int(res.json()['output'][1]['stck_clpr']) #전일 종가
    stck_oprc = int(res.json()['output'][0]['stck_oprc']) #오늘 시가
    
    if (stck_clpr*1.005 < stck_oprc): #갭상으로 시작?
        return stck_clpr
    return False

def get_target_price(code="005930"):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"FHKST01010400"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    "fid_org_adj_prc":"1",
    "fid_period_div_code":"D"
    }
    res = requests.get(URL, headers=headers, params=params)
    stck_hgpr = int(res.json()['output'][1]['stck_hgpr']) #전일 고가
    stck_lwpr = int(res.json()['output'][1]['stck_lwpr']) #전일 저가
    stck_clpr = int(res.json()['output'][1]['stck_clpr']) #전일 종가
    stck_oprc = int(res.json()['output'][0]['stck_oprc']) #오늘 시가

    ## 심리를 이용한 1% 먹기 알고리즘 ##
    # 매수가 = 시가 + (전일고가-전일저가) *0.5) + ((전일종가-시가)*0.5)
    # 손절) 시가 이하
    # 익절) 1.0% or 15:15 일괄매도
    
    target_price = 0
    rate = 0.5
    gab_rate = 0.25
    stck_oprc_temp = ((stck_hgpr - stck_lwpr) * rate) + ((stck_clpr-stck_oprc) * gab_rate)

    # 최소 타겟값 보정
    if (stck_oprc * 0.01) > stck_oprc_temp :
        target_price = stck_oprc * 1.01
    else :    
        target_price = stck_oprc + stck_oprc_temp

    return target_price

def get_stock_balance():
    """주식 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8434R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    send_message(f"====주식 보유잔고====")
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = stock['hldg_qty']
            send_message(f"{stock['prdt_name']}({stock['pdno']}): {stock['hldg_qty']}주")
            time.sleep(0.01)
    send_message(f"주식 평가 금액: {evaluation[0]['scts_evlu_amt']}원")
    time.sleep(0.01)
    send_message(f"평가 손익 합계: {evaluation[0]['evlu_pfls_smtl_amt']}원")
    time.sleep(0.01)
    send_message(f"총 평가 금액: {evaluation[0]['tot_evlu_amt']}원")
    time.sleep(0.01)
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
    send_message(f"주문 가능 현금 잔고: {cash}원")
    return int(cash)

def buy(code="005930", qty="1"):
    """주식 시장가 매수"""  
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": str(int(qty)),
        "ORD_UNPR": "0",
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC0802U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(f"[매수 성공]{str(res.json())}")
        return True
    else:
        send_message(f"[매수 실패]{str(res.json())}")
        return False

def sell(code="005930", qty="1"):
    """주식 시장가 매도"""
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": qty,
        "ORD_UNPR": "0",
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC0801U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(f"[매도 성공]{str(res.json())}")
        return True
    else:
        send_message(f"[매도 실패]{str(res.json())}")
        return False
    

# 자동 매매 코드
try:        
    holiday = False
    startoncebyday = False
    
    send_message("=== 자동매매를 구동합니다 ===")

    while True:
        today = datetime.datetime.today().weekday()
        
        if today == 5 or today == 6:  # 토,일 자동종료
            if holiday == False:
                send_message("주말이라 쉽니다~")
                holiday = True
            continue
        else:
            t_now = datetime.datetime.now()
            
            t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
            t_start = t_now.replace(hour=9, minute=0, second=1, microsecond=0)
            t_exit = t_now.replace(hour=15, minute=19, second=50,microsecond=0)
            
            if t_9 < t_now < t_start and startoncebyday == False: # 매매 준비
                send_message("=== 데일리 매매를 준비합니다 ===")
                
                startoncebyday = True
                holiday = False

                # 토큰 세팅
                ACCESS_TOKEN = get_access_token()

                # 매수종목 (KODEX 레버리지, KODEX 200선물인버스2X, 코스닥150레버리지, 코스닥150선물인버스)
                # symbol_list = ["122630","252670"] 
                symbol_list = ["003490","034220","124560","084680"] # 매수종목(대한항공, LG디스플레이,태웅로직스,이월드)
                bought_list = [] # 매수 리스트
                selldone_list = [] # 중간매매 완료 리스트
                
                # 1.2% 매매 (박리다익으로 확률을 높인다)
                profit_rate = 1.012

                total_cash = get_balance() # 보유 현금 조회
                stock_dict = get_stock_balance() # 보유 주식 조회
                for sym in stock_dict.keys():
                    bought_list.append(sym)

                target_buy_count = int(len(symbol_list)) # 매수할 종목 수
                buy_percent = 1 / target_buy_count # 종목당 매수 금액 비율
                buy_amount = total_cash * buy_percent  # 종목별 주문 금액 계산

                for sym, qty in stock_dict.items(): 
                    sell(sym, qty)
                    
                bought_list = []

                time.sleep(1)
                get_stock_balance() # 보유 주식 조회

            if t_start < t_now < t_exit and startoncebyday == True:  # AM 09:00 ~ PM 03:18 : 매수
                
                if len(selldone_list) == target_buy_count:
                    startoncebyday = False

                    bought_list = []
                    get_stock_balance()
                    
                    send_message("=== 익/손절매 전량매도로 매매를 종료합니다 ===")
                    continue

                for sym in symbol_list:
                    target_price = get_target_price(sym)
                    current_price = get_current_price(sym)

                    if sym in bought_list: #매수한 종목 -> 익절 or 손절 처리만
                        
                        #이미 익절 or 손절 했으면 패스
                        if (sym in selldone_list):
                            continue
                        
                        #익절
                        if ((target_price*profit_rate) < current_price):
                            stock_dict = get_stock_balance() # 보유주식 정보 최신화
                            for symtemp, qty in stock_dict.items():
                                if sym == symtemp:
                                    if sell(sym, qty):
                                        send_message(f"{sym} ({target_price*profit_rate} < {current_price}) {profit_rate}% 익절합니다 ^^ ")
                                        selldone_list.append(sym)
                                        get_stock_balance()
                                        continue
                            
                        #손절
                        stck_oprc = get_stck_oprc(sym)
                        if(stck_oprc > current_price): #오늘 시가 보다 떨어지면                    
                            stock_dict = get_stock_balance() # 보유주식 정보 최신화
                            for symtemp, qty in stock_dict.items():
                                if sym == symtemp:
                                    if sell(sym, qty):
                                        send_message(f"{sym} ({get_stck_oprc(sym)} > {current_price}) 시가에서 손절합니다 ㅠ ")
                                        selldone_list.append(sym)
                                        get_stock_balance()
                                        continue
                        
                        continue # 종목 이미 샀거나, 이후 익/손절매 했으면 패스
                    
                    # 목표가에 달성했다면
                    if target_price < current_price:
                        buy_qty = 0  # 매수할 수량 초기화
                        buy_qty = int(buy_amount // current_price)
                        if buy_qty > 0:
                            send_message(f"{sym} 목표가 달성({target_price} < {current_price})으로 매수합니다~")
                            if buy(sym, buy_qty):
                                bought_list.append(sym)
                                get_stock_balance()

                if t_now.minute == 30 and t_now.second <= 5: 
                    get_stock_balance()
                    time.sleep(5)
                
                time.sleep(60) # 1분 주기 모니터링

            if t_exit < t_now and startoncebyday == True:  # PM 03:19 ~ : 데일리 프로그램 종료
                startoncebyday = False

                stock_dict = get_stock_balance()
                for sym, qty in stock_dict.items():
                    sell(sym, qty)
                bought_list = []
                stock_dict = get_stock_balance()
                
                send_message("=== 데일리 매매를 종료합니다 ===")
                continue
except Exception as e:
    send_message(f"[오류 발생]{e}")
    time.sleep(1)


