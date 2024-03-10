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

    # 익절비율
    sell_rate = 0.2
    
    # 매수
    buy_rate = 0.2
    buy_max_cnt = 5
    buy_interval = 30

    previous_time = datetime.datetime.now()
    

    # 공용 데이터
    common_data ={
    '잔여예산':0,
    '공포적립':0,
    }

    #개별 종목 데이터
    symbol_list = {
    '122630':{'종목명':'코스피 레버리지 #1',
    **common_data},
    '252670':{'종목명':'코스피 인버스X2 #2',
    **common_data},

    '233740':{'종목명':'KOSDAQ 레버리지 #3',
    **common_data},
    '251340':{'종목명':'KOSDAQ 인버스X2 #4',
    **common_data},

    '396500':{'종목명':'TIGER 반도체TOP10 #5',
    **common_data},
    '371460':{'종목명':'TIGER 차이나 #6',
    **common_data},
    '192090':{'종목명':'TIGER CSI300 #7',
    **common_data},  

    '462330':{'종목명':'코스피 2차전지레버 #8',
    **common_data},    
    '465350':{'종목명':'KB 2차전지인버스 #9',
    **common_data},
 
    '471990':{'종목명':'코스피 AI반도체장비 #10',
    **common_data},                        
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
            
            t_start = t_now.replace(hour=9, minute=10, second=0, microsecond=0)
            t_exit = t_now.replace(hour=15, minute=17, second=0,microsecond=0)
            
            # 매매 준비
            if t_start < t_now < t_exit and startoncebyday == False: 
            
                message_list = ""
                message_list += "=== 자동매매를 준비합니다 ===\n"
                message_list += "\n"
                send_message(message_list)
                message_list = ""

                
                # 토큰 세팅
                ACCESS_TOKEN = get_access_token()
                
                startoncebyday = True
                holiday = False
                
                
                total_cash = get_balance() # 보유 현금 조회

                stock_dict = get_stock_balance() # 보유 주식 조회
                target_buy_count = int(len(symbol_list)) # 매수종목 수량

                message_list = "" 
                for sym in symbol_list: # 초기화


                    message_list += "---------------------------------\n"
                    
                
                message_list +="\n"
                message_list +="매매를 시작합니다~~\n"
                message_list +="\n"

                send_message(message_list)
                message_list =""

            # AM 09:00 ~ PM 03:19 : 매수
            if t_start < t_now < t_exit and startoncebyday == True:  

                for sym in symbol_list:
                    
                    time.sleep(0.2) # 유량 에러 대응
                    current_price = get_current_price(sym)
                    
                    send_message(message_list)
# -------------- 분할 매수 -------------------------------------------------------



            # PM 03:19 ~ : 데일리 프로그램 종료
            if t_exit < t_now and startoncebyday == True:  

                startoncebyday = False

                a,b = get_real_total()
                
                message_list = "[일간 손익]"
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
    time.sleep(1)


