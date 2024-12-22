import requests
import pandas as pd
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
    
def hashkey(datas): # 사고팔때 필요함
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
    date = [
    "20241225","20241231",
    "20250101",
    "20250128",
    "20250129",
    "20250130",
    "20250303",
    "20250501","20250505","20250506",
    "20250606",
    "20250815",
    "20251003","20251006","20251007","20251008","20251009",
    "20251225","20251231"]

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


#############
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

def main():
    # 1. Access Token 발급
    ACCESS_TOKEN = get_access_token()
    if not ACCESS_TOKEN:
        return

    # 2. 일일 시세 데이터 조회
    ticker = "005930"  # 삼성전자 종목 코드
    raw_data = get_target_price_new(ticker)
    if not raw_data:
        return

# 자동 매매 코드
try:        
    send_message(f"=== Warren 초기화 ===\n")

    ticker = "005930.KQ"  # 삼성전자 종목 (Yahoo Finance 티커)
    period = "7d"         # 최대 7일 데이터 (10분봉 기준)
    interval = "90m"      # 10분봉 데이터
    
    holiday = False
    t_0 = True
    t_30 = True

    budget = 10000000 # 1000만원
    buy_rate = 500000 # 50만원
        

    # 공용 데이터
    common_data ={
    '잔여예산':0,
    '공포적립':0,
    }

    #개별 종목 데이터
    symbol_list = {
    '122630':{'종목명':'KODEX 레버리지 #1',
    **common_data},
    '252670':{'종목명':'KODEX 인버스X2 #2',
    **common_data},

    '233740':{'종목명':'KOSDAQ 레버리지 #3',
    **common_data},
    '251340':{'종목명':'KOSDAQ 인버스X2 #4',
    **common_data},                  
    }


    while True:
        today = datetime.datetime.today().weekday()
        today_date = datetime.datetime.today().strftime("%Y%m%d")

        if today == 5 or today == 6 or get_holiday(today_date):  # 토,일 자동종료, 2024 공휴일 포함

            main()

            if holiday == False:
                send_message("KOSPI 휴장일 입니다~")
                holiday = True
            continue

        else:
            t_now = datetime.datetime.now()
            
            t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
            t_buy = t_now.replace(hour=9, minute=10, second=0, microsecond=0)
            t_sell = t_now.replace(hour=15, minute=10, second=0,microsecond=0)
            
            # 매매 준비
            if t_start == t_now: 
            
                # 토큰 세팅
                ACCESS_TOKEN = get_access_token()
                send_message(f"=== Warren 토큰 구동 ({today_date})===\n\n")
                
                holiday = False
                
                # total_cash = get_balance() # 보유 현금 조회
                # stock_dict = get_stock_balance() # 보유 주식 조회                    

            # 탐욕 지급
            if t_buy == t_now:  

                for sym in symbol_list:
                    
                    time.sleep(0.2) # 유량 에러 대응
                    current_price = get_current_price(sym)
                    
                    # 매도

                    send_message(message_list)


            # 공포 예탁
            if t_sell == t_now:  

                for sym in symbol_list:
                    
                    time.sleep(0.2) # 유량 에러 대응
                    current_price = get_current_price(sym)
                    
                    # 매수

                    send_message(message_list)


                a,b = get_real_total()
                
                message_list = "[일간 손익]"
                formatted_amount = "{:,.0f}원".format(a)
                message_list += f"자산증감액: {formatted_amount}\n"
                formatted_amount = "{:,.3f}%".format(b)
                message_list += f"총수익율: {formatted_amount}\n"
                message_list += "\n"
                message_list += "=== 자동매매를 종료합니다 ==="
                send_message(message_list)

            if t_now.minute == 30 and t_30: 
                t_30 = False
                t_0 = True

                message_list =""
                message_list += "===30분===30분=(WarrenOn)=30분===30분===\n"
                message_list += "\n"
                send_message(message_list)

            if t_now.minute == 0 and t_0:
                t_0 = False
                t_30 = True
                
                message_list =""
                message_list += "===0분===0분=(WarrenOn)=0분===0분===\n"
                message_list += "\n"
                send_message(message_list)

except Exception as e:
    send_message(f"[오류 발생]{e}")
    time.sleep(1)


