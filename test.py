
import pandas as pd
import FinanceDataReader as fdr


print(int(1-2))
# 오늘 날짜 가져오기


# # 코스피 개장일 목록에서 오늘 날짜가 있는지 확인
# is_market_open_today = today_date in kospi_market_dates['ListingDate'].dt.date.values

# # 결과 출력
# if is_market_open_today:
#     print("오늘은 코스피의 개장일입니다.")
# else:
#     print("오늘은 코스피의 휴장일이거나 개장되지 않은 날입니다.")


# import pandas as pd
# import yfinance as yf
# import matplotlib.pyplot as plt
# from matplotlib import font_manager, rc


# # 주식 데이터 가져오기 (예: 삼성전자, 2022년 1월 1일부터 현재까지)
# stock_data = yf.download('122630.KS', start='2023-07-01')

# # 주식 종가 기준으로 5일 평균 계산
# stock_data['5일평균'] = stock_data['Close'].rolling(window=5).mean()

# # 한글 폰트 설정
# font_path = "C:/Windows/Fonts/malgun.ttf"  # 사용하는 운영체제의 한글 폰트 경로로 변경
# font_name = font_manager.FontProperties(fname=font_path).get_name()
# rc('font', family=font_name)

# # 그래프 그리기
# plt.figure(figsize=(10, 6))
# plt.plot(stock_data['Close'], label='종가')
# plt.plot(stock_data['5일평균'], label='5일 평균선', color='orange')
# plt.title('주식 가격 및 5일 평균선')
# plt.xlabel('날짜')
# plt.ylabel('가격')
# plt.legend()
# plt.show()

# symbol_list = { # 대한항공, LG디스플레이,태웅로직스,이월드
#                 '003490':{'종목명':'대한항공',
#                 '보유':'False',
#                 '재매수':'False',
#                 'profit_rate07_up':'True',
#                 'profit_rate12_up':'True',
#                 'profit_rate17_up':'True',
#                 'profit_rate34_up':'True',
#                 'profit_rate07_down':'False',
#                 'profit_rate12_down':'False',
#                 'profit_rate17_down':'False',
#                 'profit_rate34_down':'False'},

#                 '034220':{'종목명':'LG디스플레이어',
#                 '보유':'False',
#                 '재매수':'False',
#                 'profit_rate07_up':'True',
#                 'profit_rate12_up':'True',
#                 'profit_rate17_up':'True',
#                 'profit_rate34_up':'True',
#                 'profit_rate07_down':'False',
#                 'profit_rate12_down':'False',
#                 'profit_rate17_down':'False',
#                 'profit_rate34_down':'False'},

#                 '124560':{'종목명':'태웅로직스',
#                 '보유':'False',
#                 '재매수':'False',
#                 'profit_rate07_up':'True',
#                 'profit_rate12_up':'True',
#                 'profit_rate17_up':'True',
#                 'profit_rate34_up':'True',
#                 'profit_rate07_down':'False',
#                 'profit_rate12_down':'False',
#                 'profit_rate17_down':'False',
#                 'profit_rate34_down':'False'},

#                 '084680':{'종목명':'이월드',
#                 '보유':'False',
#                 '재매수':'False',
#                 'profit_rate07_up':'True',
#                 'profit_rate12_up':'True',
#                 'profit_rate17_up':'True',
#                 'profit_rate34_up':'True',
#                 'profit_rate07_down':'False',
#                 'profit_rate12_down':'False',
#                 'profit_rate17_down':'False',
#                 'profit_rate34_down':'False'}               
#                 }
# target_buy_count = int(len(symbol_list)) # 매수할 종목 수
# print(target_buy_count)
# print("==========")

# for sym in symbol_list:
#     print(symbol_list[sym]['종목명'])

# symbol_list = {
# '003490':{'종목명':'대한항공','보유':'0','재매수':'0'},
# '034220':{'종목명':'LG디스플레이어','보유':'0','재매수':'0'} # 매수종목(대한항공, LG디스플레이,태웅로직스,이월드)
# }


# symbol_list['003490']['재매수'] = True

# chulsoo_neighborhood = symbol_list['003490']['종목명']
# print(chulsoo_neighborhood)

# chulsoo_neighborhood = symbol_list['034220']['종목명']
# print(chulsoo_neighborhood)

# chulsoo_neighborhood = symbol_list['003490']['보유']
# print(chulsoo_neighborhood)

# chulsoo_neighborhood = symbol_list['003490']['재매수']
# print(chulsoo_neighborhood)

# input1 = 0.1
# profit_rate07 = 1.007
# profit_rate12 = 1.012
# profit_rate17 = 1.017
# profit_rate34 = 1.034

# profit_rate07_up = True
# profit_rate12_up = True
# profit_rate17_up = True
# profit_rate34_up = True

# profit_rate07_down = False
# profit_rate12_down = False
# profit_rate17_down = False
# profit_rate34_down = False

#  # 거미줄 익절매
# while 1:
   
#     input1 = input("가격 입력: ")
#     input1 = float(input1)

#     #상향 익절
#     if input1 > profit_rate34 and profit_rate34_up:
#         profit_rate34 = 1.034
#         print(f"==상향 익절 {profit_rate34}")
#         profit_rate34_up = False

#         profit_rate17_up = False
#         profit_rate12_up = False
#         profit_rate07_up = False
#         profit_rate17_down = True
#         profit_rate12_down = True
#         profit_rate07_down = True
#         continue

#     if input1 > profit_rate17 and profit_rate17_up:
#         profit_rate17 = 1.017
#         print(f"==상향 익절 {profit_rate17}")
#         profit_rate17_up = False

#         profit_rate12_up = False
#         profit_rate07_up = False
#         profit_rate12_down = True
#         profit_rate07_down = True
#         continue

#     if input1 > profit_rate12 and profit_rate12_up:
#         profit_rate12 = 1.012
#         print(f"==상향 익절 {profit_rate12}")
#         profit_rate12_up = False

#         profit_rate07_up = False
#         profit_rate07_down = True
#         continue

#     if input1 > profit_rate07 and profit_rate07_up:
#         profit_rate07 = 1.007
#         print(f"==상향 익절 {profit_rate07}")
#         profit_rate07_up = False
#         continue

#     # 하향 익절
#     if input1 <= profit_rate17 and profit_rate17_down:
#         profit_rate17 = 1.017
#         print(f"하하하하향 익절 {profit_rate17}")
#         profit_rate17_down = False

#         profit_rate34_up = True
#         continue

#     if input1 <= profit_rate12 and profit_rate12_down:
#         profit_rate12 = 1.012
#         print(f"하하하하향 익절 {profit_rate12}")
#         profit_rate12_down = False

#         profit_rate34_up = True
#         profit_rate17_up = True
#         continue

#     if input1 <= profit_rate07 and profit_rate07_down:
#         profit_rate07 = 1.007
#         print(f"하하하하향 익절 {profit_rate07}")
#         profit_rate07_down = False

#         profit_rate34_up = True
#         profit_rate17_up = True
#         profit_rate12_up = True
#         continue
    