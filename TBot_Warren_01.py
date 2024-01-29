import requests
import json
import datetime
import time
import yaml

# 분할매수 Warren


with open('config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL_KOREA']
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

def get_holiday(day="YYYYMMDD"):
    date = ["20240209",
    "20240212",
    "20240301",
    "20240410",
    "20240501", "20240506","20240515",
    "20240606",
    "20240815",
    "20240916","20240916","20240918",
    "20241003","20241009",
    "20241225","20241231"]

    i =""
    for i in date:
        if i == day:
            return True
    return False

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
    cnt = 0 # 음봉 카운트

    target_price = 0 # 초기화
    delta = 0 # 윗꼬리값

    for i in range(0,data_period):
        stck_hgpr = int(res.json()['output'][i]['stck_hgpr']) #고가
        # stck_lwpr = int(res.json()['output'][i]['stck_lwpr']) #저가
        stck_clpr = int(res.json()['output'][i]['stck_clpr']) #종가
        stck_oprc = int(res.json()['output'][i]['stck_oprc']) #시가

        if stck_oprc >= stck_clpr : #음봉
            delta += stck_hgpr - stck_oprc
            cnt += 1

    target_price = int(res.json()['output'][0]['stck_oprc']) #오늘 시가
    
    if cnt > 0:
        delta /= cnt # 평균

    target_price += delta

    return target_price

def get_real_total():
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance-rlz-pl"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8494R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "00",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "COST_ICLD_YN": "N",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    res = requests.get(URL, headers=headers, params=params)

    evaluation1 = float(res.json()['output2'][0]['asst_icdc_amt'])
    evaluation2 = float(res.json()['output2'][0]['asst_icdc_erng_rt'])

    
    return evaluation1, evaluation2

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
    
    send_message("")
    send_message("====주식 보유잔고====")
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = stock['hldg_qty']
            send_message(f"{stock['prdt_name']}({stock['pdno']}): {stock['hldg_qty']}주")
    
    formatted_amount = "{:,.0f}원".format(int(evaluation[0]['scts_evlu_amt']))
    send_message(f"주식 평가 금액: {formatted_amount}")

    formatted_amount = "{:,.0f}원".format(int(evaluation[0]['evlu_pfls_smtl_amt']))
    send_message(f"평가 손익 합계: {formatted_amount}")

    formatted_amount = "{:,.0f}원".format(int(evaluation[0]['tot_evlu_amt']))
    send_message(f"총 평가 금액: {formatted_amount}")
    send_message("=================")
    send_message("")
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
        send_message("-+-+-매수 성공-+-+-")
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
        send_message(f"-#-#-매도 성공-#-#-")
        return True
    else:
        send_message(f"[매도 실패]{str(res.json())}")
        return False
    

# 자동 매매 코드
try:        
    send_message("")
    send_message("=== 국내증시 초기화합니다 ===")
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
    sell_rate = 0.2

    symbol_list = {
    '069500':{'종목명':'코스피_200',
    '배분예산':0,
    '목표매수가':0,
    '실매수가':0,
    '시가':0,
    '보유':False,
    '예산_가중치':1.35,
    '익절_가중치':0.65,
    'profit_rate07_up':True,
    'profit_rate12_up':True,
    'profit_rate17_up':True,
    'profit_rate22_up':True,
    'profit_rate07_down':False,
    'profit_rate12_down':False,
    'profit_rate17_down':False},

    '114800':{'종목명':'코스피_인버스',
    '배분예산':0,
    '목표매수가':0,
    '실매수가':0,
    '시가':0,
    '보유':False,
    '예산_가중치':1.35,
    '익절_가중치':0.65,
    'profit_rate07_up':True,
    'profit_rate12_up':True,
    'profit_rate17_up':True,
    'profit_rate22_up':True,
    'profit_rate07_down':False,
    'profit_rate12_down':False,
    'profit_rate17_down':False},

    '122630':{'종목명':'KOSPI_레버리지',
    '배분예산':0,
    '목표매수가':0,
    '실매수가':0,
    '시가':0,
    '보유':False,
    '예산_가중치':1.0,
    '익절_가중치':1.3,
    'profit_rate07_up':True,
    'profit_rate12_up':True,
    'profit_rate17_up':True,
    'profit_rate22_up':True,
    'profit_rate07_down':False,
    'profit_rate12_down':False,
    'profit_rate17_down':False},

    '252670':{'종목명':'KOSPI_인버스X2',
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
    'profit_rate17_down':False},

    '229200':{'종목명':'KOSDAQ_150',
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
    'profit_rate17_down':False},

    '233740':{'종목명':'KOSDAQ_레버리지',
    '배분예산':0,
    '목표매수가':0,
    '실매수가':0,
    '시가':0,
    '보유':False,
    '예산_가중치':1.0,
    '익절_가중치':1.5,
    'profit_rate07_up':True,
    'profit_rate12_up':True,
    'profit_rate17_up':True,
    'profit_rate22_up':True,
    'profit_rate07_down':False,
    'profit_rate12_down':False,
    'profit_rate17_down':False},

    '251340':{'종목명':'KOSDAQ_인버스X2',
    '배분예산':0,
    '목표매수가':0,
    '실매수가':0,
    '시가':0,
    '보유':False,
    '예산_가중치':1.0,
    '익절_가중치':1.3,
    'profit_rate07_up':True,
    'profit_rate12_up':True,
    'profit_rate17_up':True,
    'profit_rate22_up':True,
    'profit_rate07_down':False,
    'profit_rate12_down':False,
    'profit_rate17_down':False},

    '371460':{'종목명':'TIGER_차이나',
    '배분예산':0,
    '목표매수가':0,
    '실매수가':0,
    '시가':0,
    '보유':False,
    '예산_가중치':1.0,
    '익절_가중치':1.5,
    'profit_rate07_up':True,
    'profit_rate12_up':True,
    'profit_rate17_up':True,
    'profit_rate22_up':True,
    'profit_rate07_down':False,
    'profit_rate12_down':False,
    'profit_rate17_down':False},            
    }

    while True:
        today = datetime.datetime.today().weekday()
        today_date = datetime.datetime.today().strftime("%Y%m%d")
        
        if today == 5 or today == 6 or get_holiday(today_date):  # 토,일 자동종료, 2024 공휴일 포함
            if holiday == False:
                send_message("KOSPI 휴장일 입니다~")
                holiday = True
            continue
        else:
            t_now = datetime.datetime.now()
            
            t_start = t_now.replace(hour=9, minute=0, second=15, microsecond=0)
            t_930 = t_now.replace(hour=9, minute=30, second=0, microsecond=0)
            t_1510 = t_now.replace(hour=15, minute=10, second=40,microsecond=0)
            t_exit = t_now.replace(hour=15, minute=19, second=40,microsecond=0)
            
            if t_start < t_now < t_exit and startoncebyday == False: # 매매 준비
            
                send_message("")
                send_message("=== 국내증시 자동매매를 준비합니다 ===")
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

                # 일단 200만원으로 테스팅 ===============================================================================
                # total_cash /= 5 

                stock_dict = get_stock_balance() # 보유 주식 조회
                target_buy_count = int(len(symbol_list)) # 매수종목 수량

                for sym, qty in stock_dict.items(): # 있으면 일괄 매도
                    sell(sym, int(qty))
                    send_message(f">>> [{symbol_list[sym]['종목명']}] 시가({get_stck_oprc(sym)})원에 매도했습니다~")


                for sym in symbol_list: # 초기화

                    send_message(f"[{symbol_list[sym]['종목명']}]")
                    symbol_list[sym]['배분예산'] = total_cash * (1/target_buy_count) * symbol_list[sym]['예산_가중치']
                    formatted_amount = "{:,.0f}원".format(symbol_list[sym]['배분예산'])
                    send_message(f" - 배분예산: {formatted_amount}")

                    symbol_list[sym]['시가'] = get_stck_oprc(sym)
                    formatted_amount = "{:,.0f}원".format(symbol_list[sym]['시가'])
                    send_message(f" - 시가: {formatted_amount}")   

                    symbol_list[sym]['목표매수가'] = get_target_price_new(sym)
                    formatted_amount = "{:,.0f}원".format(symbol_list[sym]['목표매수가'])
                    send_message(f" - 목표매수가: {formatted_amount}")   

                    send_message(f" - 타겟%: {round((symbol_list[sym]['목표매수가'])/symbol_list[sym]['시가'],4)}")

                    symbol_list[sym]['보유'] = False
                    send_message("---------------------------------")
                    
                
                send_message("")
                send_message("국내증시 매매를 시작합니다~")
                send_message("")

            if t_start < t_now < t_exit and startoncebyday == True:  # AM 09:00 ~ PM 03:20 : 매수

                for sym in symbol_list:
                    current_price = get_current_price(sym)

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


                        #익절
                        if sell_fix:
                            stock_dict = get_stock_balance() # 보유주식 최신화
                            for symtemp, qty in stock_dict.items():
                                if sym == symtemp:
                                    qty = int(qty)                                    
                                    sell_qty = int(symbol_list[sym]['배분예산'] // current_price) * sell_rate

                                    if qty > sell_qty: # sell_rate 분할매도
                                        qty = sell_qty

                                    if sell(sym, qty):
                                        good_sell_cnt += 1
                                        send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/symbol_list[sym]['실매수가'],4)}% 익절매합니다 ^^")
                                    
                                        continue
                            

                        #시가 손절 : 99.5% 보정
                        elif(symbol_list[sym]['시가']*0.995 > current_price): # 오늘 시가 보다 떨어지면 
                            symbol_list[sym]['보유'] = False                   
                            stock_dict = get_stock_balance() # 보유주식 정보 최신화
                            for symtemp, qty in stock_dict.items():
                                if sym == symtemp:
                                    if sell(sym, int(qty)):
                                        bad_sell_cnt += 1
                                        send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/symbol_list[sym]['실매수가'],4)}% 시가 손절매합니다 ㅠ")
                                        
                                        continue
                        
                        continue # 보유 주식 있으면 매수하지 않는다.

                    # 목표가 매수
                    elif symbol_list[sym]['목표매수가'] <= current_price and symbol_list[sym]['보유'] == False:
                        qty = int(symbol_list[sym]['배분예산'] // current_price)
                        if qty > 0:
                            if buy(sym, qty):
                                buy_cnt += 1
                                symbol_list[sym]['실매수가'] = current_price
                                symbol_list[sym]['보유'] = True

                                send_message(f"[{symbol_list[sym]['종목명']}] 매수가")
                                
                                formatted_amount = "{:,.0f}원".format(symbol_list[sym]['목표매수가'])
                                send_message(f" - 목표매수가: {formatted_amount}")   

                                formatted_amount = "{:,.0f}원".format(symbol_list[sym]['실매수가'])
                                send_message(f" - 실매수가: {formatted_amount}")

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
                if t_start <= t_now < t_930:
                    time.sleep(1)
                elif t_1510 <= t_now < t_exit:
                    time.sleep(1)
                else:
                    time.sleep(15)

            if t_exit < t_now and startoncebyday == True:  # PM 03:19 ~ : 데일리 프로그램 종료
                startoncebyday = False

                send_message(f"=데일리 일괄매도=")
                stock_dict = get_stock_balance()
                for sym, qty in stock_dict.items(): # 있으면 일괄 매도
                    end_sell_cnt += 1
                    sell(sym, int(qty))
                    send_message(f">>> [{symbol_list[sym]['종목명']}]: 현재가 {get_current_price(sym)} / 매수가 {symbol_list[sym]['목표매수가']}")
                    send_message(f">>> [{symbol_list[sym]['종목명']}]: {round(get_current_price(sym)/symbol_list[sym]['목표매수가'],4)}% 매도합니다")
                send_message(f"---")

                
                send_message("[매매 카운트]")
                send_message(f" -buy: {buy_cnt}")
                send_message(f" -good Sell: {good_sell_cnt}")
                send_message(f" -bad Sell: {bad_sell_cnt}")
                send_message(f" -end Sell: {end_sell_cnt}")

                a,b = get_real_total()
                send_message("")
                formatted_amount = "{:,.0f}원".format(a)
                send_message(f"오늘의 차익: {formatted_amount}")

                formatted_amount = "{:,.3f}%".format(b)
                send_message(f"수익율: {formatted_amount}")
                send_message("")

                send_message("=== 국내증시 자동매매를 종료합니다 ===")
                continue
except Exception as e:
    send_message(f"[오류 발생]{e}")
    time.sleep(1)


