
symbol_list = { # 대한항공, LG디스플레이,태웅로직스,이월드
                '003490':{'종목명':'대한항공',
                '보유':'False',
                '재매수':'False',
                'profit_rate07_up':'True',
                'profit_rate12_up':'True',
                'profit_rate17_up':'True',
                'profit_rate34_up':'True',
                'profit_rate07_down':'False',
                'profit_rate12_down':'False',
                'profit_rate17_down':'False',
                'profit_rate34_down':'False'},

                '034220':{'종목명':'LG디스플레이어',
                '보유':'False',
                '재매수':'False',
                'profit_rate07_up':'True',
                'profit_rate12_up':'True',
                'profit_rate17_up':'True',
                'profit_rate34_up':'True',
                'profit_rate07_down':'False',
                'profit_rate12_down':'False',
                'profit_rate17_down':'False',
                'profit_rate34_down':'False'},

                '124560':{'종목명':'태웅로직스',
                '보유':'False',
                '재매수':'False',
                'profit_rate07_up':'True',
                'profit_rate12_up':'True',
                'profit_rate17_up':'True',
                'profit_rate34_up':'True',
                'profit_rate07_down':'False',
                'profit_rate12_down':'False',
                'profit_rate17_down':'False',
                'profit_rate34_down':'False'},

                '084680':{'종목명':'이월드',
                '보유':'False',
                '재매수':'False',
                'profit_rate07_up':'True',
                'profit_rate12_up':'True',
                'profit_rate17_up':'True',
                'profit_rate34_up':'True',
                'profit_rate07_down':'False',
                'profit_rate12_down':'False',
                'profit_rate17_down':'False',
                'profit_rate34_down':'False'}               
                }
target_buy_count = int(len(symbol_list)) # 매수할 종목 수
print(target_buy_count)
print("==========")

for sym in symbol_list:
    print(symbol_list[sym]['종목명'])

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
    