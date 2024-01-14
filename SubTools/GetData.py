import requests
import time
import json
import yaml

with open('config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
URL_BASE = _cfg['URL_BASE']
CODE = "003490" #대한항공


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
    

# 1회 토큰세팅
ACCESS_TOKEN = get_access_token()

time.sleep(1)


"""daily-price 조회"""
PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
URL = f"{URL_BASE}/{PATH}"
headers = {"Content-Type":"application/json", 
    "authorization": f"Bearer {ACCESS_TOKEN}",
    "appKey":APP_KEY,
    "appSecret":APP_SECRET,
    "tr_id":"FHKST01010400"}
params = {
"fid_cond_mrkt_div_code":"J",
"fid_input_iscd":CODE,
"fid_org_adj_prc":"1",
"fid_period_div_code":"D"
}
res = requests.get(URL, headers=headers, params=params)


TEMP = 0
for i in range(5) :
    temp = int(res.json()['output'][i]['stck_clpr'])
    TEMP += temp
print("5일 이평선: ",int(TEMP / 5))

TEMP = 0
for j in range(20) :
    temp = int(res.json()['output'][j]['stck_clpr'])
    TEMP += temp

print("20일 이평선: ",int(TEMP / 20))

"""""
TEMP = 0
for k in range(60) :
    temp = int(res.json()['output'][k]['stck_clpr'])
    TEMP += temp

print("60일 이평선: ",int(TEMP / 60))
"""

print("==========================")

print("전일 저가: ",int(res.json()['output'][1]['stck_lwpr']))
print("전일 고가: ",int(res.json()['output'][1]['stck_hgpr']))
print("전일 종가: ",int(res.json()['output'][1]['stck_clpr']))
print("오늘 시가: ",int(res.json()['output'][0]['stck_oprc']))
print("누적 거래량: ",int(res.json()['output'][0]['acml_vol']))
print("전일 대비 거래량 비율: ",float(res.json()['output'][0]['prdy_vrss_vol_rate']))
print("전일 대비: ",int(res.json()['output'][0]['prdy_vrss']))

print("==========================")
print("==========================")

"""price 조회"""
PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
URL = f"{URL_BASE}/{PATH}"
headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"FHKST01010100"}
params = {
"fid_cond_mrkt_div_code":"J",
"fid_input_iscd":CODE,
}
res = requests.get(URL, headers=headers, params=params)

print("현재가: ", int(res.json()['output']['stck_prpr']))
print("전일 대비: ", int(res.json()['output']['prdy_vrss']))

