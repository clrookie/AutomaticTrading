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

def get_target_price(code="005930"): #변동성 돌파 (안씀)
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

def get_target_price_new(code="005930"): # 음봉 윗꼬리 평균 + 보정
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

    data_period = 30 # 최근 추출 기간
    rate = 1.15 # 상향 보정 비율
    cnt = 0 # 음봉 카운트

    target_price = 0 # 초기화

    for i in range(0,data_period):
        stck_hgpr = int(res.json()['output'][i]['stck_hgpr']) #전일 고가
        # stck_lwpr = int(res.json()['output'][i]['stck_lwpr']) #전일 저가
        stck_clpr = int(res.json()['output'][i]['stck_clpr']) #전일 종가
        stck_oprc = int(res.json()['output'][i]['stck_oprc']) #오늘 시가

        if stck_oprc >= stck_clpr : #음봉
            target_price += stck_hgpr - stck_oprc

    target_price /= cnt # 평균
    target_price *= rate

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
    send_message(f"주식 평가 금액: {evaluation[0]['scts_evlu_amt']}원")
    send_message(f"평가 손익 합계: {evaluation[0]['evlu_pfls_smtl_amt']}원")
    send_message(f"총 평가 금액: {evaluation[0]['tot_evlu_amt']}원")
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
        "ORD_QTY": str(int(qty)),
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
    send_message("=== 자동매매를 초기화합니다 ===")
    
    holiday = False
    startoncebyday = False

    # 분할매도 기준선
    profit_rate07 = 1.007
    profit_rate12 = 1.012
    profit_rate17 = 1.017
    profit_rate34 = 1.034
    sell_rate = 0.2

    # 매수종목 (KODEX 레버리지, KODEX 200선물인버스2X, 코스닥150레버리지, 코스닥150선물인버스)
    # symbol_list = ["122630","252670","233740","251340"] 

    symbol_list = { # 테스트 매수종목 : 대한항공,LG디스플레이,태웅로직스,이월드
    '003490':{'종목명':'대한항공',
    '배분예산':'0',
    '목표매수가':'0',
    '실매수가':'0',
    '시가':'0',
    '보유':'False',
    '재매수':'True',
    'profit_rate07_up':'True',
    'profit_rate12_up':'True',
    'profit_rate17_up':'True',
    'profit_rate34_up':'True',
    'profit_rate07_down':'False',
    'profit_rate12_down':'False',
    'profit_rate17_down':'False',
    'profit_rate34_down':'False'},

    '034220':{'종목명':'LG디스플레이어',
    '배분예산':'0',
    '목표매수가':'0',
    '실매수가':'0',
    '시가':'0',
    '보유':'False',
    '재매수':'True',
    'profit_rate07_up':'True',
    'profit_rate12_up':'True',
    'profit_rate17_up':'True',
    'profit_rate34_up':'True',
    'profit_rate07_down':'False',
    'profit_rate12_down':'False',
    'profit_rate17_down':'False',
    'profit_rate34_down':'False'},

    '124560':{'종목명':'태웅로직스',
    '배분예산':'0',
    '목표매수가':'0',
    '실매수가':'0',
    '시가':'0',
    '보유':'False',
    '재매수':'True',
    'profit_rate07_up':'True',
    'profit_rate12_up':'True',
    'profit_rate17_up':'True',
    'profit_rate34_up':'True',
    'profit_rate07_down':'False',
    'profit_rate12_down':'False',
    'profit_rate17_down':'False',
    'profit_rate34_down':'False'},

    '084680':{'종목명':'이월드',
    '배분예산':'0',
    '목표매수가':'0',
    '실매수가':'0',
    '시가':'0',
    '보유':'False',
    '재매수':'True',
    'profit_rate07_up':'True',
    'profit_rate12_up':'True',
    'profit_rate17_up':'True',
    'profit_rate34_up':'True',
    'profit_rate07_down':'False',
    'profit_rate12_down':'False',
    'profit_rate17_down':'False',
    'profit_rate34_down':'False'}               
    }

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
            t_930 = t_now.replace(hour=9, minute=30, second=0, microsecond=0)
            t_exit = t_now.replace(hour=15, minute=19, second=50,microsecond=0)
            
            if t_9 < t_now < t_start and startoncebyday == False: # 매매 준비
                send_message("=== 데일리 자동매매를 준비합니다 ===")
                
                startoncebyday = True
                holiday = False

                # 토큰 세팅
                ACCESS_TOKEN = get_access_token()

                total_cash = get_balance() # 보유 현금 조회
                stock_dict = get_stock_balance() # 보유 주식 조회
                target_buy_count = int(len(symbol_list)) # 매수종목 수량

                for sym, qty in stock_dict.items(): # 있으면 일괄 매도
                    sell(sym, int(qty))
                    send_message(f">>> [{symbol_list[sym]['종목명']}] 시가에 매도했습니다~")


                for sym in symbol_list: # 초기화
                    send_message(f"[{symbol_list[sym]['종목명']}]")
                    symbol_list[sym]['배분예산'] = total_cash * (1/target_buy_count)
                    send_message(f" -[{symbol_list[sym]['배분예산']}]")
                    symbol_list[sym]['시가'] = get_stck_oprc(sym)
                    send_message(f" -[{symbol_list[sym]['시가']}]")   
                    symbol_list[sym]['목표매수가'] = get_target_price_new(sym)
                    symbol_list[sym]['재매수'] = True
                    send_message(f" -[{symbol_list[sym]['목표매수가']}]")  
                    send_message("---------")
                    


                time.sleep(0.1)
                stock_dict = get_stock_balance() # 보유 주식 조회

            if t_start < t_now < t_exit and startoncebyday == True:  # AM 09:00 ~ PM 03:20 : 매수

                for sym in symbol_list:
                    current_price = get_current_price(sym)

                    if symbol_list[sym]['보유']: # 보유중이면
                        sell_fix = False
                        
                        #상향 익절
                        if current_price > symbol_list[sym]['목표매수가']*profit_rate34 and symbol_list[sym]['profit_rate34_up']:
                            symbol_list[sym]['profit_rate34_up'] = False

                            symbol_list[sym]['profit_rate17_up'] = False
                            symbol_list[sym]['profit_rate12_up'] = False
                            symbol_list[sym]['profit_rate07_up'] = False
                            symbol_list[sym]['profit_rate17_down'] = True
                            symbol_list[sym]['profit_rate12_down'] = True
                            symbol_list[sym]['profit_rate07_down'] = True

                            sell_fix = True

                        if current_price > symbol_list[sym]['목표매수가']*profit_rate17 and symbol_list[sym]['profit_rate17_up']:
                            symbol_list[sym]['profit_rate17_up'] = False

                            symbol_list[sym]['profit_rate12_up'] = False
                            symbol_list[sym]['profit_rate07_up'] = False
                            symbol_list[sym]['profit_rate12_down'] = True
                            symbol_list[sym]['profit_rate07_down'] = True

                            sell_fix = True

                        if current_price > symbol_list[sym]['목표매수가']*profit_rate12 and symbol_list[sym]['profit_rate12_up']:
                            symbol_list[sym]['profit_rate12_up'] = False

                            symbol_list[sym]['profit_rate07_up'] = False
                            symbol_list[sym]['profit_rate07_down'] = True

                            sell_fix = True

                        if current_price > symbol_list[sym]['목표매수가']*profit_rate07 and symbol_list[sym]['profit_rate07_up']:
                            symbol_list[sym]['profit_rate07_up'] = False

                            sell_fix = True

                        # 하향 익절
                        if current_price <= symbol_list[sym]['목표매수가']*profit_rate17 and symbol_list[sym]['profit_rate17_down']:
                            symbol_list[sym]['profit_rate17_down'] = False

                            symbol_list[sym]['profit_rate34_up'] = True

                            sell_fix = True

                        if current_price <= symbol_list[sym]['목표매수가']*profit_rate12 and symbol_list[sym]['profit_rate12_down']:
                            symbol_list[sym]['profit_rate12_down'] = False

                            symbol_list[sym]['profit_rate34_up'] = True
                            symbol_list[sym]['profit_rate17_up'] = True

                            sell_fix = True


                        if current_price <= symbol_list[sym]['목표매수가']*profit_rate07 and symbol_list[sym]['profit_rate07_down']:
                            symbol_list[sym]['profit_rate07_down'] = False

                            symbol_list[sym]['profit_rate34_up'] = True
                            symbol_list[sym]['profit_rate17_up'] = True
                            symbol_list[sym]['profit_rate12_up'] = True

                            sell_fix = True


                        #익절
                        if sell_fix:
                            stock_dict = get_stock_balance() # 보유주식 최신화
                            for symtemp, qty in stock_dict.items():
                                if sym == symtemp:
                                    qty = int(qty)                                    
                                    sell_qty = int(symbol_list[sym]['배분예산'] // current_price) * sell_rate

                                    if qty > sell_qty: # sell_rate 매도
                                        qty = sell_qty
                                    else:
                                        symbol_list[sym]['보유'] = False # 청산

                                    if sell(sym, qty):
                                        send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/symbol_list[sym]['실매수가'],1)}%로 익절매합니다 ^^")
                                        time.sleep(0.1)
                                        stock_dict= get_stock_balance()
                                        continue
                            

                        #시가 손절
                        if(symbol_list[sym]['시가'] > current_price): # 오늘 시가 보다 떨어지면                    
                            stock_dict = get_stock_balance() # 보유주식 정보 최신화
                            for symtemp, qty in stock_dict.items():
                                if sym == symtemp:
                                    if sell(sym, int(qty)):
                                        send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/symbol_list[sym]['실매수가'],1)}%로 시가 손절매합니다 ㅠ")
                                        symbol_list[sym]['보유'] = False
                                        symbol_list[sym]['재매수'] = True
                                        time.sleep(0.1)
                                        stock_dict= get_stock_balance()
                                        continue
                        
                        continue # 보유 주식 있으면 매수하지 않는다.

                    # 목표가 매수
                    if symbol_list[sym]['목표매수가'] <= current_price and symbol_list[sym]['재매수']:
                        qty = int(symbol_list[sym]['배분예산'] // current_price)
                        if qty > 0:
                            if buy(sym, qty):
                                symbol_list[sym]['실매수가'] = current_price
                                symbol_list[sym]['보유'] = True
                                symbol_list[sym]['재매수'] = False # 손절까지 재매수 안함

                                send_message(f"[{symbol_list[sym]['종목명']}]")
                                send_message(f" -목표매수가: [{symbol_list[sym]['목표매수가']}")
                                send_message(f" -실매수가: [{symbol_list[sym]['실매수가']}")

                                #분할매수 조건 초기화
                                symbol_list[sym]['profit_rate07_up'] = True
                                symbol_list[sym]['profit_rate12_up'] = True
                                symbol_list[sym]['profit_rate17_up'] = True
                                symbol_list[sym]['profit_rate34_up'] = True
                                symbol_list[sym]['profit_rate07_down'] = False
                                symbol_list[sym]['profit_rate12_down'] = False
                                symbol_list[sym]['profit_rate17_down'] = False
                                symbol_list[sym]['profit_rate34_down'] = False
                                
                                time.sleep(0.1)
                                stock_dict= get_stock_balance()

                if t_now.minute == 30 and t_now.second <= 5: 
                    get_stock_balance()
                    time.sleep(5)
                
                # 서비스 정책상 (1초 20건 한계)
                if t_9 <= t_now < t_930:
                    time.sleep(1)
                else:
                    time.sleep(15)

            if t_exit < t_now and startoncebyday == True:  # PM 03:19 ~ : 데일리 프로그램 종료
                startoncebyday = False

                send_message(f"데일리 일괄매도")
                for sym, qty in stock_dict.items(): # 있으면 일괄 매도
                    sell(sym, int(qty))

                    send_message(f">>> [{symbol_list[sym]['종목명']}]: {round(get_current_price(sym)/symbol_list[sym]['목표매수가'],1)}%로 매도합니다")
                send_message(f"---")

                time.sleep(0.1)
                stock_dict = get_stock_balance()
                
                send_message("=== 데일리 자동매매를 종료합니다 ===")
                continue
except Exception as e:
    send_message(f"[오류 발생]{e}")
    time.sleep(1)


