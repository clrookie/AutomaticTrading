import schedule
import time

principal = 1000

rate = 1.015
period = 100

print("원금: ", principal)
print("수익률: ", rate)
print("=====")
print("  ")

result = 0
for i in range(period):
    result += (principal * rate) - principal

formatted_amount1 = "{:,.0f}원".format(principal+result)
print("수익: ", formatted_amount1)


for i in range(period):
    principal *= rate   

formatted_amount1 = "{:,.0f}원".format(principal) 
print("복리수익: ", formatted_amount1)


aaa = 1.16645
print("소수점: ", round(aaa,2))

""" 자동매매 스케쥴 시작
schedule.every().day.at("09:31").do() 

while True:
    print("1111")
    while True:
        if schedule.run_pending():
            print("333333")
            continue
        print("1111")
        time.sleep(1)
    
    print("22222")
    time.sleep(1)
    """