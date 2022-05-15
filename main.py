from strategy.RSIStrategy import *
import sys

app = QApplication(sys.argv) #Kiwoom 클래스를 객체화하는 메인 루프

rsi_strategy = RSIStrategy()
rsi_strategy.start()

# kospi_code_list = kiwoom.get_code_list_by_market("0")   #코스피 종목코드 호출
# print(kospi_code_list)
# for code in kospi_code_list:
#     code_name = kiwoom.get_master_code_name(code)
#     print(code, code_name)

# kosdaq_code_list = kiwoom.get_code_list_by_market("10") #코스닥 종목코드 호출
# print(kosdaq_code_list)
# for code in kosdaq_code_list:
#     code_name = kiwoom.get_master_code_name(code)
#     print(code, code_name)

# df = kiwoom.get_price_data_daily("005930")    #삼성전자(005930)의 일봉차트 호출
# print(df)

# deposit = kiwoom.get_deposit()  #예수금 정보 호출

# order_result = kiwoom.send_order('send_buy_order', '1001', 1, '005930', 1, 69000, '00') #매수매도주문, 화면번호, 주문유형(매수=1, 매도=2...), 종목코드, 주문수량, 주문가격, 주문방식(지정가, 시장가 등)
# print(order_result)

# orders = kiwoom.get_order()    #미체결 주문 정보 호출
# print(orders)

# position = kiwoom.get_balance() #계좌 평가 잔액 요청
# print(position)

# kiwoom.set_real_reg("1000", "", get_fid("장운영구분"), "0")
# codes = '005930;007700;000660;'
# kiwoom.set_real_reg("1000", codes, get_fid("체결시간"), "0")    #화면번호, 종목, 장운영구분/체결시간, 최초등록여부(0맞음,1아님)

app.exec_() #Kiwoom 클래스를 객체화하는 메인 루프