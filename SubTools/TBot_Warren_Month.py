import requests
import json
from datetime import datetime, timedelta
import datetime
import time
import yaml

# KOSPI


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
    "20240916","20240917","20240918",
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


def get_target_price(code,profit_max): # 음봉 윗꼬리 평균 + 보정
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
        stck_clpr = int(res.json()['output'][i]['stck_clpr']) #종가
        stck_oprc = int(res.json()['output'][i]['stck_oprc']) #시가

        if stck_oprc >= stck_clpr : #음봉
            delta += stck_hgpr - stck_oprc
            cnt += 1

    target_price = int(res.json()['output'][0]['stck_oprc']) #오늘 시가
    
    if cnt > 0:
        delta /= cnt # 평균

    target_price += delta

    # 5일 이평선 ----------------------------------------------------------------

    stck_clpr_5 = 0
    for i in range(0,5):
        stck_clpr_5 += int(res.json()['output'][i]['stck_clpr']) #종가

    stck_clpr_5 /= 5
    stck_oprc_day = int(res.json()['output'][0]['stck_oprc']) #오늘 시가

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
                target_price = stck_clpr_5 + delta
                return target_price,profit_rate

    # 이평선 위에 시가 시작이면 평소처럼
    return target_price, profit_rate




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

def get_avg_balance(code="005930"):
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

    for stock in stock_list:
        if int(stock['hldg_qty']) > 0 and stock['pdno'] == code:
            return stock['pchs_avg_pric']
    
    return 9

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
    
    message_list = ""
    message_list += "====주식 보유잔고====\n"
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = stock['hldg_qty']
            message_list += f"{stock['prdt_name']}({stock['pdno']}): {stock['hldg_qty']}주\n"
    
    formatted_amount = "{:,.0f}원".format(int(evaluation[0]['scts_evlu_amt']))
    message_list += f"주식 평가 금액: {formatted_amount}\n"

    formatted_amount = "{:,.0f}원".format(int(evaluation[0]['evlu_pfls_smtl_amt']))
    message_list += f"평가 손익 합계: {formatted_amount}\n"

    formatted_amount = "{:,.0f}원".format(int(evaluation[0]['tot_evlu_amt']))
    message_list += f"총 평가 금액: {formatted_amount}\n"
    message_list += "=================\n"
    message_list += "\n"
    send_message(message_list)

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
    
    message_list = ""
    message_list += "===============================\n"
    formatted_amount = "{:,.0f}원".format(int(cash))
    message_list += f"현금 잔고: {formatted_amount}\n"
    send_message(message_list)

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
    message_list = ""
    message_list += "=== 국내증시 초기화합니다 ===\n"
    message_list += "\n"
    send_message(message_list)
    message_list = ""
    
    holiday = False
    startoncebyday = False
    t_0 = True
    t_30 = True

    # 익절 기준선
    profit_rate07 = 1.051
    profit_rate12 = 1.076
    profit_rate17 = 1.101
    profit_rate22 = 1.126
    
    # 손절 기준선
    loss_cut1 = 0.990
    loss_cut2 = 0.9875
    loss_cut3 = 0.985

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
    '보유':False,
    '매수최대량':0,
        
    '매매유무': False,
    '매수카운트':0,
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
    # '069500':{'종목명':'코스피 200 #1', #1
    # '예산_가중치':1,
    # '익절_가중치':0.65,
    # **common_data},
    # '114800':{'종목명':'코스피 인버스 #2', #2
    # '예산_가중치':1,
    # '익절_가중치':0.65,
    # **common_data},
    '122630':{'종목명':'코스피 레버리지 #3', #3
    '예산_가중치':1,
    '익절_가중치':1,
    **common_data},
    '252670':{'종목명':'코스피 인버스X2 #4', #4
    '예산_가중치':1,
    '익절_가중치':0.65,
    **common_data},

    # '229200':{'종목명':'KOSDAQ 150 #5', #5
    # '예산_가중치':1,
    # '익절_가중치':0.65,
    # **common_data},
    '233740':{'종목명':'KOSDAQ 레버리지 #6', #6
    '예산_가중치':1,
    '익절_가중치':1,
    **common_data},
    '251340':{'종목명':'KOSDAQ 인버스X2 #7', #7
    '예산_가중치':1,
    '익절_가중치':0.65,
    **common_data},

    # '102110':{'종목명':'TIGER 200 #8', #8
    # '예산_가중치':1,
    # '익절_가중치':0.65,
    # **common_data},
    '396500':{'종목명':'TIGER 반도체TOP10 #9', #9
    '예산_가중치':1,
    '익절_가중치':1,
    **common_data},
    '371460':{'종목명':'TIGER 차이나 #10', #10
    '예산_가중치':1,
    '익절_가중치':1,
    **common_data},
    '192090':{'종목명':'TIGER CSI300 #11', #11
    '예산_가중치':1,
    '익절_가중치':0.65,
    **common_data},  

    '462330':{'종목명':'코스피 2차전지레버 #12', #12
    '예산_가중치':1,
    '익절_가중치':1,
    **common_data},    
    '465350':{'종목명':'KB 2차전지인버스 #13', #13
    '예산_가중치':1,
    '익절_가중치':1,
    **common_data},

    # '471760':{'종목명':'TIGER AI반도체공정 #14', #14
    # '예산_가중치':1,
    # '익절_가중치':1,
    # **common_data},       
    '471990':{'종목명':'코스피 AI반도체장비 #15', #15
    '예산_가중치':1,
    '익절_가중치':1,
    **common_data},                        
    }

    # ============================================================================================
    # 초반 테스트용 코드 초반 테스트용 코드 초반 테스트용 코드 초반 테스트용 코드 초반 테스트용 코드
    # ============================================================================================

    # # 토큰 세팅
    # ACCESS_TOKEN = get_access_token()
    
    # startoncebyday = True
    # holiday = False
    
    # t_0 = True
    # t_30 = True              
    
    # total_cash = get_balance() # 보유 현금 조회

    # # total_cash /= 5 

    # stock_dict = get_stock_balance() # 보유 주식 조회
    # target_buy_count = int(len(symbol_list)) # 매수종목 수량

    
    # for sym, qty in stock_dict.items(): # 있으면 일괄 매도
        
    #     current_price = get_current_price(sym)
    #     send_message(f">>> [{symbol_list[sym]['종목명']}] {current_price}원에 매도 시도 ({sym}개)")

    #     if sell(sym, int(qty)):
    #         send_message(f">>> [{symbol_list[sym]['종목명']}] 일괄 매도 성공 !!")

    # message_list = "" # 초기화
    # for sym in symbol_list: # 초기화

    #     message_list += f"[{symbol_list[sym]['종목명']}]\n"
    #     symbol_list[sym]['배분예산'] = int(total_cash * (1/target_buy_count) * symbol_list[sym]['예산_가중치'])
    #     formatted_amount = "{:,.0f}원".format(symbol_list[sym]['배분예산'])
    #     message_list += f"- 배분예산: {formatted_amount}\n"

    #     symbol_list[sym]['시가'] = int(get_stck_oprc(sym))
    #     formatted_amount = "{:,.0f}원".format(symbol_list[sym]['시가'])
    #     message_list += f"- 시가: {formatted_amount}\n"   

    #     target_price,profit_rate = get_target_price(sym,(((profit_rate22-1)*symbol_list[sym]['익절_가중치'])+1))
    #     symbol_list[sym]['익절_가중치'] *= profit_rate

    #     symbol_list[sym]['목표매수가'] = int(target_price)
    #     formatted_amount = "{:,.0f}원".format(symbol_list[sym]['목표매수가'])
    #     message_list += f"- 목표매수가: {formatted_amount}\n"   

    #     message_list += f"- 타겟%: {round((symbol_list[sym]['목표매수가'])/symbol_list[sym]['시가'],4)}\n"

    # ============================================================================================
    # 초반 테스트용 코드 초반 테스트용 코드 초반 테스트용 코드 초반 테스트용 코드 초반 테스트용 코드
    # ============================================================================================

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
            
            t_start = t_now.replace(hour=9, minute=4, second=0, microsecond=0)
            t_930 = t_now.replace(hour=9, minute=30, second=0, microsecond=0)
            t_1510 = t_now.replace(hour=15, minute=10, second=0,microsecond=0)
            t_exit = t_now.replace(hour=15, minute=17, second=0,microsecond=0)
            
            if t_start < t_now < t_exit and startoncebyday == False: # 매매 준비
            
                message_list = ""
                message_list += "=== 자동매매를 준비합니다 ===\n"
                message_list += "\n"
                send_message(message_list)
                message_list = ""

                
                # 토큰 세팅
                ACCESS_TOKEN = get_access_token()
                
                startoncebyday = True
                holiday = False
                
                t_0 = True
                t_30 = True              
                
                total_cash = get_balance() # 보유 현금 조회

                # 고정 시드머니 설정 (1000만원)
                if total_cash > 10000000: total_cash = 10000000

                stock_dict = get_stock_balance() # 보유 주식 조회
                target_buy_count = int(len(symbol_list)) # 매수종목 수량

                
                for sym, qty in stock_dict.items(): # 있으면 일괄 매도
                    
                    current_price = get_current_price(sym)
                    send_message(f">>> [{symbol_list[sym]['종목명']}] {current_price}원에 매도 시도 ({sym}개)")

                    if sell(sym, int(qty)):
                        send_message(f">>> [{symbol_list[sym]['종목명']}] 일괄 매도 성공 !!")

                message_list = "" # 초기화
                for sym in symbol_list: # 초기화

                    message_list += f"[{symbol_list[sym]['종목명']}]\n"
                    symbol_list[sym]['배분예산'] = int(total_cash * (1/target_buy_count) * symbol_list[sym]['예산_가중치'])
                    formatted_amount = "{:,.0f}원".format(symbol_list[sym]['배분예산'])
                    message_list += f"- 배분예산: {formatted_amount}\n"

                    symbol_list[sym]['시가'] = int(get_stck_oprc(sym))
                    formatted_amount = "{:,.0f}원".format(symbol_list[sym]['시가'])
                    message_list += f"- 시가: {formatted_amount}\n"   

                    target_price,profit_rate = get_target_price(sym,(((profit_rate22-1)*symbol_list[sym]['익절_가중치'])+1))
                    symbol_list[sym]['익절_가중치'] *= profit_rate

                    symbol_list[sym]['목표매수가'] = int(target_price)
                    formatted_amount = "{:,.0f}원".format(symbol_list[sym]['목표매수가'])
                    message_list += f"- 목표매수가: {formatted_amount}\n"   

                    message_list += f"- 타겟%: {round((symbol_list[sym]['목표매수가'])/symbol_list[sym]['시가'],4)}\n"

                    symbol_list[sym]['보유'] = False
                    symbol_list[sym]['손절_1차'] = False
                    symbol_list[sym]['손절_2차'] = False
                    symbol_list[sym]['손절_3차'] = False
                    symbol_list[sym]['매매유무'] = False
                    symbol_list[sym]['매수카운트'] = 0
                    symbol_list[sym]['매수최대량'] = 0

                    message_list += "---------------------------------\n"
                    
                
                previous_time = datetime.datetime.now()
                
                message_list +="\n"
                message_list +="매매를 시작합니다~~\n"
                message_list +="\n"

                send_message(message_list)
                message_list =""

            if t_start < t_now < t_exit and startoncebyday == True:  # AM 09:00 ~ PM 03:19 : 매수

                # 시간 간격 분할 매수
                time_difference = t_now - previous_time
                # n시간이 지났는지 확인
                if time_difference >= timedelta(seconds=buy_interval):                    
                    # 현재 시간을 이전 시간으로 업데이트
                    previous_time = t_now

                    for sym in symbol_list:
                        
                        time.sleep(0.2) # 유량 에러 대응
                        current_price = get_current_price(sym)
                        
                        if symbol_list[sym]['목표매수가'] < current_price and symbol_list[sym]['매수카운트'] < buy_max_cnt: # 목표매수가와 횟수 체크
                                
                                message_list =""

                                qty = int((symbol_list[sym]['배분예산'] // current_price) * buy_rate) # 분할 매수
                                message_list += f"[{symbol_list[sym]['종목명']}] 매수 시도 ({qty}개)\n"
                                if qty > 0:
                                    if buy(sym, qty):
                                        
                                        symbol_list[sym]['매수카운트'] += 1
                                        symbol_list[sym]['실매수가'] = current_price
                                        symbol_list[sym]['보유'] = True
                                        symbol_list[sym]['매매유무'] = True
                                        
                                        symbol_list[sym]['매수최대량'] += qty

                                        # 손절 1차 unlock... ;;
                                        symbol_list[sym]['손절_1차'] = False
                                        symbol_list[sym]['손절_2차'] = False
                                        symbol_list[sym]['손절_3차'] = False     

                                        message_list += f"[{symbol_list[sym]['종목명']}] {symbol_list[sym]['매수카운트']}차 매수 성공\n"
                                        
                                        formatted_amount = "{:,.0f}원".format(symbol_list[sym]['시가'])
                                        message_list += f"- 시가: {formatted_amount}\n"
                                        formatted_amount = "{:,.0f}원".format(symbol_list[sym]['목표매수가'])
                                        message_list += f"- 목표매수가: {formatted_amount}\n"   
                                        formatted_amount = "{:,.0f}원".format(symbol_list[sym]['실매수가'])
                                        message_list += f"- 실매수가: {formatted_amount}\n"
                                        
                                        
                                        avg_price = get_avg_balance(sym)
                                        avg_price = float(avg_price)
                                        
                                        if avg_price == 9:
                                            message_list += f"[{symbol_list[sym]['종목명']}] : !!!! 평단가 리턴 실패 !!!!\n"
                                        
                                        formatted_amount = "{:,.0f}원".format(avg_price)
                                        
                                        message_list += f"- *평단가*: {formatted_amount}\n"

                                        #분할매도 조건 초기화
                                        symbol_list[sym]['profit_rate07_up'] = True
                                        symbol_list[sym]['profit_rate12_up'] = True
                                        symbol_list[sym]['profit_rate17_up'] = True
                                        symbol_list[sym]['profit_rate22_up'] = True
                                        symbol_list[sym]['profit_rate07_down'] = False
                                        symbol_list[sym]['profit_rate12_down'] = False
                                        symbol_list[sym]['profit_rate17_down'] = False
                                        
                                send_message(message_list)
# -------------- 분할 매수 -------------------------------------------------------


# -------------- 보유중 -------------------------------------------------------
                for sym in symbol_list:

                    if symbol_list[sym]['보유']: # 보유중이면

                        sell_fix = False
                        avg_price = get_avg_balance(sym)
                        avg_price = float(avg_price)
                        if avg_price == 9:
                            send_message(f"[{symbol_list[sym]['종목명']}] : !!!! 평단가 리턴 실패 !!!!")
                            continue
                        
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
                            stock_dict = get_stock_balance() # 보유주식 최신화
                            for symtemp, qty in stock_dict.items():
                                if sym == symtemp:
                                    qty = float(qty)
                                    sell_qty = float(symbol_list[sym]['매수최대량'] * sell_rate)
                                    
                                    if sell_qty < 1: sell_qty = 1

                                    if qty > sell_qty: # 분할 익절
                                        send_message(f"[{symbol_list[sym]['종목명']}]: 분할 익절 시도 ({sell_qty}/{qty}개)")
                                        qty = sell_qty
                                    else:
                                        symbol_list[sym]['보유'] = False # 전량 익절 -> 일간 매매 종료
                                        send_message(f"[{symbol_list[sym]['종목명']}]: 전량 익절 시도 ({qty}개)")

                                    if sell(sym, qty):
                                        send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/avg_price,4)}% 익절매합니다 ^^ ({qty}개)")
                                        send_message(f"[{symbol_list[sym]['종목명']}]: 익절가({current_price}) 평단가({avg_price})")     
                           
                        # 1차 손절하거나
                        elif(avg_price*loss_cut1 > current_price and symbol_list[sym]['손절_1차'] == False):
                            stock_dict = get_stock_balance() # 보유주식 정보 최신화
                            for symtemp, qty in stock_dict.items():
                                if sym == symtemp:
                                    total_qty = qty
                                    qty = float(qty) * 0.33 # 분할 손절
                                    if qty < 1:
                                        qty = 1
                                    else:
                                        qty = int(qty)

                                    send_message(f"[{symbol_list[sym]['종목명']}]: 1차 손절매 시도 ({qty}/{total_qty}개)")
                                    if sell(sym, int(qty)):
                                        symbol_list[sym]['손절_1차'] = True
                                        symbol_list[sym]['매수최대량'] -= qty     
                                        send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/avg_price,4)}% 1차 손절매")
                                        send_message(f"[{symbol_list[sym]['종목명']}]: 손절가({current_price}) 평단가({avg_price})")     
                                        
                        # 2차 손절
                        elif(avg_price*loss_cut2 > current_price and symbol_list[sym]['손절_2차'] == False):
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
                                    if sell(sym, qty):
                                        symbol_list[sym]['손절_2차'] = True   
                                        symbol_list[sym]['매수최대량'] -= qty     
                                        send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/avg_price,4)}% 2차 손절매")
                                        send_message(f"[{symbol_list[sym]['종목명']}]: 손절가({current_price}) 평단가({avg_price})")
                                        
                        # 3차 손절
                        elif(avg_price*loss_cut3 > current_price and symbol_list[sym]['손절_3차'] == False):

                            stock_dict = get_stock_balance() # 보유주식 정보 최신화
                            for symtemp, qty in stock_dict.items():
                                if sym == symtemp:
                                    qty = int(qty)
                                    send_message(f"[{symbol_list[sym]['종목명']}]: 3차 전량 손절매 시도 ({qty}개)")
                                    if sell(sym, qty):
                                        symbol_list[sym]['손절_3차'] = True
                                        send_message(f"[{symbol_list[sym]['종목명']}]: {round(current_price/avg_price,4)}% 3차 손절매")
                                        send_message(f"[{symbol_list[sym]['종목명']}]: 손절가({current_price}) 평단가({avg_price})")     

                                        # 매수 unlock... ;;
                                        symbol_list[sym]['보유'] = False
                                        symbol_list[sym]['매수카운트'] = 0
                                        symbol_list[sym]['매수최대량'] = 0   

#---------------------- 여기까지 보유중 루프 -----------------------------------------------------------------------------


                if t_now.minute == 30 and t_30: 
                    t_30 = False
                    t_0 = True

                    message_list =""
                    message_list += "===30분===30분===30분===30분===\n"
                    message_list += "\n"
                    send_message(message_list)
                    get_stock_balance()
                if t_now.minute == 0 and t_0:
                    t_0 = False
                    t_30 = True
                    
                    message_list =""
                    message_list += "===0분===0분===0분===0분===\n"
                    message_list += "\n"
                    send_message(message_list)
                    get_stock_balance()
                
                # 서비스 정책상 (1초 20건 한계)
                if t_start <= t_now < t_930:
                    time.sleep(1)
                elif t_1510 <= t_now < t_exit:
                    time.sleep(1)
                else:
                    time.sleep(10)

            if t_exit < t_now and startoncebyday == True:  # PM 03:19 ~ : 데일리 프로그램 종료
                startoncebyday = False

                send_message(f"**** 데일리 일괄매도 ****")
                stock_dict = get_stock_balance()
                for sym, qty in stock_dict.items(): # 있으면 일괄 매도
                    
                    avg_price = get_avg_balance(sym)
                    avg_price = float(avg_price)
                    if avg_price == 9:
                        send_message(f"[{symbol_list[sym]['종목명']}] : !!!! 평단가 리턴 실패 !!!!")

                    if (symbol_list[sym]['profit_rate17_down'] == True): # 시세좋은 종목은 다음날 시가 매도
                        send_message(f"[{symbol_list[sym]['종목명']}]: 일괄 매도 롤오버~")
                        send_message(f"[{symbol_list[sym]['종목명']}]: 현재가 {get_current_price(sym)} / 평단가 {avg_price}")
                        continue

                    if sell(sym, int(qty)):
                        send_message(f"[{symbol_list[sym]['종목명']}]: 현재가 {get_current_price(sym)} / 평단가 {avg_price}")
                        send_message(f"[{symbol_list[sym]['종목명']}]: {round(get_current_price(sym)/avg_price,4)}% 매도합니다")
                    else:
                        sell(sym, int(qty))
                        send_message(f">>> retry [{symbol_list[sym]['종목명']}]: 현재가 {get_current_price(sym)} / 평단가 {avg_price}")
                        send_message(f">>> retry [{symbol_list[sym]['종목명']}]: {round(get_current_price(sym)/avg_price,4)}% 매도합니다")
                    
                send_message(f"---")

                
                #매매한 종목수 카운트
                Total_sym = 0
                trade_cnt = 0
                for sym in symbol_list: # 초기화
                    Total_sym += 1
                    if symbol_list[sym]['매매유무'] == True:
                        trade_cnt += 1

                time.sleep(15)

                get_stock_balance()

                a,b = get_real_total()
                
                message_list = "[일간 손익]"

                message_list += "\n"
                message_list += f"매매종목수: {trade_cnt}/{Total_sym}\n"
                formatted_amount = "{:,.0f}원".format(a)
                message_list += f"자산증감액: {formatted_amount}\n"
                formatted_amount = "{:,.3f}%".format(b)
                message_list += f"총수익율: {formatted_amount}\n"
                message_list += "\n"
                message_list += "=== 자동매매를 종료합니다 ==="
                send_message(message_list)

    

                continue
except Exception as e:
    send_message(f"[오류 발생]{e}")
    stock_dict = get_stock_balance() # 보유 주식 조회                
    for sym, qty in stock_dict.items(): # 오류 있으면 일괄 매도
        
        current_price = get_current_price(sym)
        send_message(f">>> [{symbol_list[sym]['종목명']}] {current_price}원에 오류 매도 시도 ({sym}개)")

        if sell(sym, int(qty)):
            send_message(f">>> [{symbol_list[sym]['종목명']}] 오류 일괄 매도 성공 !!")
    time.sleep(1)


