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

def check_Opening(day: str) -> bool:
    """
    특정 날짜가 휴장일인지 확인합니다.
    :param date: YYYYMMDD 형식의 날짜 문자열
    :return: True(휴장일) 또는 False(영업일)
    """
    PATH = "uapi/domestic-stock/v1/quotations/chk-holiday"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "CTCA0903R",  # 휴장일 확인 API 호출 ID
        "custtype":"P",
    }
    params = {
        "BASS_DT": day,
        "CTX_AREA_NK":"",
        "CTX_AREA_FK":""
        }
    
    res = requests.get(URL, headers=headers, params=params)
    if res.status_code == 200:
        data = res.json()
        # 응답 데이터의 구조가 리스트라면 첫 번째 항목 참조
        if isinstance(data["output"], list):
            return data["output"][0]["opnd_yn"] == "Y"
        # 딕셔너리라면 바로 참조
        if isinstance(data["output"], dict):
            return data["output"]["opnd_yn"] == "Y"
        else:
            raise ValueError("Unexpected output format in response")
    else:
        raise Exception(f"Failed to check holiday status: {res.json()}")

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
            message_list += f"{stock['prdt_name']}: {stock['evlu_pfls_rt']}%\n"
    
    formatted_amount = "{:,.0f}원".format(int(evaluation[0]['scts_evlu_amt']))
    message_list += f"주식 평가 금액: {formatted_amount}\n"

    formatted_amount = "{:,.0f}원".format(int(evaluation[0]['evlu_pfls_smtl_amt']))
    message_list += f"평가 손익 합계: {formatted_amount}\n"

    formatted_amount = "{:,.0f}원".format(int(evaluation[0]['tot_evlu_amt']))
    message_list += f"총 평가 금액: {formatted_amount}\n"
    message_list += "==================================\n"
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
        return True
    else:
        send_message(f"[매수 실패]{str(res.json())}\n")
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
        return True
    else:
        send_message(f"[매도 실패]{str(res.json())}")
        return False


#############
def get_avg_price_15day(code="005930"):
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
    send_message("=== Warren 초기화 ===")
    
    last_date = 0
    last_hour = 0

    bStart_buy = False
    bEnd_sell = False
    holiday = False
    t_0 = True
    t_30 = True

    buy_rate = 1500000.0 # 150만원
    profit_cut = 1.021
    lost_cut = 0.985
        
    # 공용 데이터
    common_data ={
    '보유': False,
    '물량': 0.0,
    '익절': False,
    }

    #개별 종목 데이터
    symbol_list = {
    '122630':{'종목명':'KODEX 레버리지 #1',     **common_data},
    '233740':{'종목명':'KOSDAQ 레버리지 #2',    **common_data},
    
    '371460':{'종목명':'TIGER 차이나전기차 #3',   **common_data},
    '192090':{'종목명':'TIGER 차이나CSI #4',    **common_data},

    '462330':{'종목명':'KODEX 2차전지 #5',      **common_data},
    '471990':{'종목명':'KODEX AI반도체 #6',     **common_data},

    '252670':{'종목명':'KODEX 인버스 #7',       **common_data},
    '251340':{'종목명':'KOSDAQ 인버스 #8',      **common_data},
    '465350':{'종목명':'RISE 2차전 인버스 #9', **common_data},                       
    }


    while True:
        today_date = datetime.datetime.today().strftime("%Y%m%d")
        t_now = datetime.datetime.now()

        if last_hour != t_now.hour:
            last_hour = t_now.hour
            send_message(f"WarrenOn...({last_hour}시)")

        if last_date != today_date:
            last_date = today_date

            ACCESS_TOKEN = get_access_token()
            send_message(f"=== Warren 토큰 발급 ({today_date})===") 

            time.sleep(1) # 유량 에러 대응

            # 개장일
            if check_Opening(today_date):
                holiday = False
                bStart_buy = False
                bEnd_sell = False
                send_message("오늘은 KOSPI 영업일^^")
            # 휴장일
            else:
                holiday = True
                send_message("오늘은 KOSPI 휴장일ㅠ")

            stock_dict = get_stock_balance() # 보유 주식 조회
            for sym, qty in stock_dict.items():
                symbol_list[sym]['보유'] = True
                symbol_list[sym]['물량'] = float(qty)

        elif holiday == False: # 개장일
            t_start = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
            t_0240 = t_now.replace(hour=14, minute=40, second=0,microsecond=0)
            t_end = t_now.replace(hour=15, minute=10, second=0,microsecond=0)
  
            #######################           
            # 시가 조건 매수
            #######################
            if t_start < t_now < t_0240 and bStart_buy == False:
                bStart_buy = True

                message_list =" #시가 매수\n"

                # 있으면 일괄 매도
                for sym in symbol_list:

                    if symbol_list[sym]['보유'] == True:
                        current_price = get_current_price(sym)
                        current_price = float(current_price)
                        avg_price = get_avg_balance(sym)
                        if avg_price == 9:
                            message_list += f"[{symbol_list[sym]['종목명']}] : !!!! 평단가 리턴 실패 !!!!\n"
                        avg_price = float(avg_price)
                        
                        formatted_amount1 = "{:,.2f}%".format((current_price/avg_price)*100-100)

                        if sell(sym, int(symbol_list[sym]['물량'])):
                            message_list += f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 일괄 매도 !!\n"
                        else:
                            sell(sym, int(symbol_list[sym]['물량']))
                            message_list += f">>> retry [{symbol_list[sym]['종목명']}]: {formatted_amount1} 일괄 매도 !!\n"

                message_list += "-------------------------------------\n"

                # 15일 평균선 < 시가 높은 경우 체크
                for sym in symbol_list: 
                    
                    # 초기화
                    symbol_list[sym]['보유'] = False
                    symbol_list[sym]['물량'] = 0.0
                    symbol_list[sym]['익절'] = False

                    current_price = get_current_price(sym)
                    avg_15day = get_avg_price_15day(sym)

                    current_price = float(current_price)
                    avg_15day = float(avg_15day)

                    formatted_amount = "{:,.0f}원".format(current_price)
                    formatted_amount1 = "{:,.0f}원".format(avg_15day)
                    if current_price >= avg_15day: 
                        
                        qty = int(buy_rate/current_price) # 분할 매수
                        message_list += f"[{symbol_list[sym]['종목명']}] 매수성공 O {formatted_amount} (15선:{formatted_amount1})\n"
                        if buy(sym, qty):
                            symbol_list[sym]['보유'] = True
                            symbol_list[sym]['물량'] = float(qty)
                            message_list +="+++ 시가 매수 +++\n\n"

                    else:
                        message_list += f"[{symbol_list[sym]['종목명']}] 매수실패 X {formatted_amount} (15선:{formatted_amount1})\n"
                
                send_message(message_list)
                stock_dict = get_stock_balance() # 보유 주식 조회
            

            
            ####################### 
            # 장중간 조건 매도
            ####################### 
            elif t_start < t_now < t_0240:  
                
                for sym in symbol_list:

                    if symbol_list[sym]['보유'] == False:
                        continue

                    current_price = get_current_price(sym)
                    current_price = float(current_price)
                    avg_price = get_avg_balance(sym)
                    if avg_price == 9:
                        send_message(f"[{symbol_list[sym]['종목명']}] : !!!! 평단가 리턴 실패 !!!!")
                    avg_price = float(avg_price)
                    
                    formatted_amount1 = "{:,.2f}%".format((current_price/avg_price)*100-100)

                    result = current_price / avg_price # 나누기 연산 시, float형
                    if result >= profit_cut and symbol_list[sym]['익절'] == False:

                        symbol_list[sym]['물량'] = symbol_list[sym]['물량'] / 2 # 절반만 익절

                        if sell(sym, int(symbol_list[sym]['물량'])):
                            send_message(f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 1/2익절^^")
                        else:
                            sell(sym, int(symbol_list[sym]['물량']))
                            send_message(f">>> retry [{symbol_list[sym]['종목명']}]: {formatted_amount1} 1/2익절^^")
                        
                        symbol_list[sym]['익절'] = True


                    elif result <= lost_cut: #손절
                        
                        if sell(sym, int(symbol_list[sym]['물량'])):
                            send_message(f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 손절ㅠ")
                        else:
                            sell(sym, int(symbol_list[sym]['물량']))
                            send_message(f">>> retry [{symbol_list[sym]['종목명']}]: {formatted_amount1} 손절ㅠ")

                        symbol_list[sym]['보유'] = False
                        symbol_list[sym]['물량'] = 0.0

                time.sleep(1) # 유량 에러 대응

                # 구동중 체크
                if t_now.minute == 30 and t_30: 
                    t_30 = False
                    t_0 = True                    
                    send_message("===30분===30분 (WarrenOn) 30분===30분===")
                    stock_dict = get_stock_balance() # 보유 주식 조회  
                if t_now.minute == 0 and t_0:
                    t_0 = False
                    t_30 = True
                    send_message("===0분===0분 (WarrenOn) 0분===0분===")
                    stock_dict = get_stock_balance() # 보유 주식 조회  

            ####################### 
            # 종가 일괄 매도
            ####################### 
            elif t_0240 < t_now < t_end and bEnd_sell == False:
                bEnd_sell = True

                stock_dict = get_stock_balance()
                
                message_list = " **** 데일리 마감 ****\n"

                for sym, qty in stock_dict.items(): # 있으면 일괄 매도
                    current_price = get_current_price(sym)
                    current_price = float(current_price)
                    avg_price = get_avg_balance(sym)
                    if avg_price == 9:
                        message_list += f"[{symbol_list[sym]['종목명']}] : !!!! 평단가 리턴 실패 !!!!\n"
                    avg_price = float(avg_price)
                    
                    formatted_amount1 = "{:,.2f}%".format((current_price/avg_price)*100-100)

                    if sell(sym, int(qty)):
                        message_list += f"[{symbol_list[sym]['종목명']}]: {formatted_amount1} 일괄 매도\n"
                    else:
                        sell(sym, int(qty))
                        message_list += f">>> retry [{symbol_list[sym]['종목명']}]: {formatted_amount1} 일괄 매도\n"
                
                a,b = get_real_total()
                
                message_list += "\n[일간 손익]\n"
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


