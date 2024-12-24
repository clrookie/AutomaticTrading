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
    message_list += "\n====주식 보유잔고====\n"
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
def get_avg_price_15day(code="005930"): # 음봉 윗꼬리 평균 + 보정
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey": APP_KEY,
        "appSecret": APP_SECRET,
        "tr_id": "FHKST01010400"
    }
    params = {
        "fid_cond_mrkt_div_code": "J",  # 코스피: "J", 코스닥: "Q"
        "fid_input_iscd": code,         # 종목 코드 (삼성전자: "005930")
        "fid_org_adj_prc": "1",         # 조정 가격 옵션
        "fid_period_div_code": "D"      # 일봉
    }

    res = requests.get(URL, headers=headers, params=params)

    # 응답을 확인하여 'output'이 존재하는지 확인
    if res.status_code != 200:
        print(f"API 요청 실패: {res.status_code}, Response: {res.text}")
    
    data = res.json()

    # 'output'이 데이터에 포함되지 않으면 오류 처리
    if "output" not in data:
        print("응답 데이터에서 'output' 필드를 찾을 수 없습니다.")
        return None

    data_period = 15  # 최근 추출 기간
    Avg_price = 0  # 초기화

    for i in range(0, data_period):
        stck_clpr = int(data['output'][i]['stck_clpr'])  # 종가
        Avg_price += stck_clpr

    Avg_price /= 15  # 목표가 계산

    return Avg_price


# 자동 매매 코드
try:        
    send_message(f"=== Warren 초기화 ===\n")
    
    bAccess_token = False
    bStart_buy = False
    bEnd_sell = False
    holiday = False
    t_0 = True
    t_30 = True

    buy_rate = 200000.0 # 20만원
        
    # 공용 데이터
    common_data ={
    '보유': False,
    }

    #개별 종목 데이터
    symbol_list = {
    '122630':{'종목명':'KODEX 레버리지',
    **common_data},
    '252670':{'종목명':'KODEX 인버스',
    **common_data},

    '233740':{'종목명':'KOSDAQ 레버리지',
    **common_data},
    '251340':{'종목명':'KOSDAQ 인버스',
    **common_data},                  
    }


    while True:
        today = datetime.datetime.today().weekday()
        today_date = datetime.datetime.today().strftime("%Y%m%d")

        if today == 5 or today == 6 or get_holiday(today_date):  # 토,일 자동종료, 2024 공휴일 포함
            if holiday == False:
                send_message("KOSPI 휴장일")
                holiday = True
            continue
        else:
            t_now = datetime.datetime.now()
            # t_ready = t_now.replace(hour=8, minute=50, second=0, microsecond=0)
            t_start = t_now.replace(hour=9, minute=0, second=0, microsecond=5)
            t_end = t_now.replace(hour=14, minute=40, second=0,microsecond=0)
  
            # 매매 준비
            if t_start < t_now < t_end and bAccess_token == False: 
            
                bAccess_token = True

                bStart_buy = False
                bEnd_sell = False
                holiday = False

                # 토큰 세팅
                ACCESS_TOKEN = get_access_token()
                send_message(f"=== Warren 토큰 구동 ({today_date})===\n\n")
                
                stock_dict = get_stock_balance() # 보유 주식 조회        

            #######################           
            # 시가 조건 매수
            #######################
            elif t_start < t_now and bStart_buy == False:
                bStart_buy = True

                # 있으면 일괄 매도
                stock_dict = get_stock_balance() # 보유 주식 조회
                for sym, qty in stock_dict.items():

                    current_price = get_current_price(sym)
                    current_price = float(current_price)
                    avg_price = get_avg_balance(sym)
                    avg_price = float(avg_price)
                    
                    formatted_amount1 = "{:,.2f}%".format((current_price/avg_price)*100-100)
                    if avg_price == 9:
                        send_message(f"[{symbol_list[sym]['종목명']}] : !!!! 평단가 리턴 실패 !!!!")

                    if sell(sym, int(qty)):
                        send_message(f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 일괄 매도 !!")
                    else:
                        sell(sym, int(qty))
                        send_message(f">>> retry [{symbol_list[sym]['종목명']}]: {formatted_amount1} 일괄 매도 !!")

                # 15일 평균선 < 시가 높은 경우 체크
                for sym in symbol_list: 
                    symbol_list[sym]['보유'] = False
                    current_price = get_current_price(sym)
                    avg_15day = get_avg_price_15day(sym)

                    current_price = float(current_price)
                    avg_15day = float(avg_15day)

                    formatted_amount = "{:,.0f}원".format(current_price)
                    formatted_amount1 = "{:,.0f}원".format(avg_15day)
                    if current_price >= avg_15day: 
                        
                        qty = int(buy_rate/current_price) # 분할 매수
                        send_message(f"[{symbol_list[sym]['종목명']}] 조건 만족!! {formatted_amount} (15선:{formatted_amount1})")
                        if buy(sym, qty):
                            symbol_list[sym]['보유'] = True

                    else:
                        send_message(f"[{symbol_list[sym]['종목명']}] 조건 실패~ {formatted_amount} (15선:{formatted_amount1})")
                
            
            ####################### 
            # 있으면, 조건 매도 (2% 익절, -2% 손절)
            ####################### 
            elif t_start < t_now < t_end:  
                for sym in symbol_list:

                    if symbol_list[sym]['보유'] == False:
                        continue

                    current_price = get_current_price(sym)
                    current_price = float(current_price)
                    avg_price = get_avg_balance(sym)
                    avg_price = float(avg_price)
                    
                    formatted_amount1 = "{:,.2f}%".format((current_price/avg_price)*100-100)

                    result = current_price / avg_price # 나누기 연산 시, float형
                    if result >= 1.02: #익절
                        stock_dict = get_stock_balance()
                        for symtemp, qty in stock_dict.items(): # 있으면 일괄 매도
                            if sym == symtemp:
                                avg_price = get_avg_balance(sym)
                                avg_price = float(avg_price)
                                formatted_amount = "{:,.0f}원".format(avg_price)
                                if avg_price == 9:
                                    send_message(f"[{symbol_list[sym]['종목명']}] : !!!! 평단가 리턴 실패 !!!!")

                                if sell(sym, int(qty)):
                                    send_message(f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 익절매^^")
                                else:
                                    sell(sym, int(qty))
                                    send_message(f">>> retry [{symbol_list[sym]['종목명']}]: {formatted_amount1} 익절매^^")
                                
                                symbol_list[sym]['보유'] = False

                    elif result <= 0.98: #손절
                        stock_dict = get_stock_balance()
                        for symtemp, qty in stock_dict.items(): # 있으면 일괄 매도
                            if sym == symtemp:
                                avg_price = get_avg_balance(sym)
                                avg_price = float(avg_price)
                                if avg_price == 9:
                                    send_message(f"[{symbol_list[sym]['종목명']}] : !!!! 평단가 리턴 실패 !!!!")

                                if sell(sym, int(qty)):
                                    send_message(f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 손절매ㅠ")
                                else:
                                    sell(sym, int(qty))
                                    send_message(f">>> retry [{symbol_list[sym]['종목명']}]: {formatted_amount1} 손절매ㅠ")

                                symbol_list[sym]['보유'] = False

                time.sleep(1) # 유량 에러 대응

                # 구동중 체크
                if t_now.minute == 30 and t_30: 
                    t_30 = False
                    t_0 = True
                    message_list =""
                    message_list += "===30분===30분 (WarrenOn) 30분===30분===\n"
                    message_list += "\n"
                    send_message(message_list)
                    stock_dict = get_stock_balance() # 보유 주식 조회  
                if t_now.minute == 0 and t_0:
                    t_0 = False
                    t_30 = True
                    message_list =""
                    message_list += "===0분===0분 (WarrenOn) 0분===0분===\n"
                    message_list += "\n"
                    send_message(message_list)
                    stock_dict = get_stock_balance() # 보유 주식 조회  

            ####################### 
            # 있으면, 종가 매도
            ####################### 
            elif t_end < t_now and bEnd_sell == False:
                bEnd_sell = True
                bAccess_token = False

                send_message(f"**** 데일리 일괄매도 ****")
                stock_dict = get_stock_balance()
                for sym, qty in stock_dict.items(): # 있으면 일괄 매도
                    current_price = get_current_price(sym)
                    current_price = float(current_price)
                    avg_price = get_avg_balance(sym)
                    avg_price = float(avg_price)
                    
                    formatted_amount1 = "{:,.2f}%".format((current_price/avg_price)*100-100)
                    if avg_price == 9:
                        message_list += f"[{symbol_list[sym]['종목명']}] : !!!! 평단가 리턴 실패 !!!!\n"

                    if sell(sym, int(qty)):
                        send_message(f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 일괄 매도")
                    else:
                        sell(sym, int(qty))
                        send_message(f">>> retry [{symbol_list[sym]['종목명']}]: {formatted_amount1} 일괄 매도")
                
                a,b = get_real_total()
                
                message_list += "\n\n[일간 손익]\n"
                formatted_amount = "{:,.0f}원".format(a)
                message_list += f"자산증감액: {formatted_amount}\n"
                formatted_amount = "{:,.3f}%".format(b)
                message_list += f"총수익율: {formatted_amount}\n"
                message_list += "\n"
                message_list += "=== 자동매매를 종료합니다 ===\n"
                send_message(message_list)

            

except Exception as e:
    send_message(f"[오류 발생]{e}")
    time.sleep(1)


