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
print("기대수익: ", int(principal+result))

for i in range(period):
    principal *= rate    
print("복리수익: ", int(principal))




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