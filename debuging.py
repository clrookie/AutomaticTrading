import requests
import json
import datetime
import time
import yaml
import schedule



print("===국내주식 자동매매를 시작합니다===")

def sell(code="005930", qty="1"):
    """주식 시장가 매도"""
    data = {
        "CANO": "01",
        "ACNT_PRDT_CD": "01",
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": qty,
        "ORD_UNPR": "0",
    }

    return data

def AAA():
    # symbol_list = ["122630","252670"] # 매수종목 (KODEX 레버리지, KODEX 200선물인버스2X)
    symbol_list = ["003490","034220"] # 매수종목 (대한항공, LG디스플레이)
    bought_list = [] # 매수 리스트

    selldone_list = [] # 중간매매 완료 리스트

    # 1% 매매 (박리다익으로 확률을 높인다)
    profit_rate = 1.011

    total_cash = 60000 # 보유 현금 조회

    target_buy_count = 2 # 매수할 종목 수
    buy_percent = 0.5 # 종목당 매수 금액 비율
    buy_amount = total_cash * buy_percent  # 종목별 주문 금액 계산
    soldout = False
    stock_dict = {"1"}

    while True:
        t_now = datetime.datetime.now()
        t_9 = t_now.replace(hour=0, minute=0, second=0, microsecond=0)
        t_start = t_now.replace(hour=0, minute=0, second=0, microsecond=0)
        t_sell = t_now.replace(hour=23, minute=58, second=0, microsecond=0)
        t_exit = t_now.replace(hour=23, minute=59, second=0,microsecond=0)
        if t_9 < t_now < t_start and soldout == False: # 잔여 수량 매도
            for sym in symbol_list:
                print(f"{sym} 전량 매도")
            soldout = True
            bought_list = []
        if t_start < t_now < t_sell :  # AM 09:05 ~ PM 03:15 : 매수
            for sym in symbol_list:
            #  if len(bought_list) < target_buy_count:
                target_price = 1800
                current_price = 2000

                if sym in bought_list: #종목 이미 샀거나, 이후 익/손절매 했으면 패스

                    #익절매 or 손절매 했으면 패스
                    if (sym in selldone_list):
                        print(f"{sym} 중간매매 완료 패스 !! ")
                        time.sleep(2)
                        continue
                    
                    #익절매
                    if ((target_price*profit_rate) < current_price):
                        sell("00",stock_dict)
                        print(f"{sym} 익절매 실현 ^^ ")
                        selldone_list.append(sym)
                        continue
                        
                    #손절매
                    if(1800 > current_price): #오늘 시가 보다 떨어지면
                        print(f"{sym} 시가 손절매 ㅠ ")
                        selldone_list.append(sym)
                        continue
                    continue #종목 이미 샀거나, 이후 익/손절매 했으면 패스
                
                if target_price < current_price:
                    buy_qty = 0  # 매수할 수량 초기화
                    buy_qty = int(buy_amount // current_price)
                    if buy_qty > 0:
                        print(f"{sym} {buy_qty}개 매수합니다.")
                        soldout = False
                        bought_list.append(sym)
                time.sleep(1)

            if len(selldone_list) == target_buy_count:
                print(f"{selldone_list} 다팔았기에 while문을 빠져나옵니다.")
                break

        if t_sell < t_now < t_exit:  # PM 03:15 ~ PM 03:20 : 일괄 매도
            if soldout == False:
                for sym in symbol_list:
                    print(f"{sym}일괄 매도합니다.")
                soldout = True
                bought_list = []
                time.sleep(1)
        if t_exit < t_now:  # PM 03:20 ~ :프로그램 종료
            print("장시간 마감으로 자동매매를 종료합니다.")
            break


schedule.every(1).seconds.do(AAA) 
# schedule.every(10).seconds.do(AutomaticTrading) # 테스트용 코드

# 자동매매 스케쥴 시작
while True:
    schedule.run_pending()
    time.sleep(1)
    print("===10초 마다 실행===")
