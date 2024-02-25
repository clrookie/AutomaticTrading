import schedule
import time
import datetime

principal = 20000

rate = 1.05
period = 150

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
print("복리: ", formatted_amount1)



now = datetime.datetime.now()
message = {"content": f"[{now.strftime('%m-%d %H:%M:%S')}] {str("msg")}"}
print(message)


aa = (round(100/99.5,4))
print(aa)

aa = round(((100/99-1)*100),4)
print(aa)


print("")
print("===30분========30분========30분========30분========30분========30분========30분===")





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