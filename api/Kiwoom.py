from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import time
import pandas as pd
from util.const import *

class Kiwoom(QAxWidget):
    def __init__(self):  #Kiwoom 클래스의 초기화함수
        super().__init__()  #super는 Kiwoom 클래스가 상속받는 QAxWidget 클래스(부모클래스), 이를 초기화해 사용을 준비함.
        self._make_kiwoom_instance()
        self._set_signal_slots()
        self._comm_connect()

        self.account_number = self.get_account_number() #추후에 필요하지반 변경되는 값이 아니므로 최초에 호출

        self.tr_event_loop = QEventLoop()   #TR 요청에 대한 응답 대기 설정

        self.count = 0      #호출횟수 카운트를 위해 임의로 삽입함
        self.order = {}     #종목코드를 키, 주문정보를 값
        self.balance = {}   #종목코드를 키, 매수정보를 값
        self.universe_realtime_transaction_info = {}    #실시간 체결 정보를 저장할 딕셔너리

    def _make_kiwoom_instance(self):    #Open API를 PC에서 사용할 수 있도록 설정
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")    #API 식별자(KHOPEN~)을 setControl 함수로 전달해 API 호출
                                                        #이렇게 해야 로그인, 주식 주문, TR요청 등 Open API에서 제공하는 제어 함수들을 사용할 수 있음.

    def _set_signal_slots(self):    #사용할 API가 비동기 방식으로, 응답을 저장할 여러 slots 생성이 필요.
                                    #이 함수에서 API로 보내는 여러 요청에 대한 응답 처리를 담당하는 slot 함수 호출
        self.OnEventConnect.connect(self._login_slot)   #이벤트 함수로, 로그인 이벤트 발생시 자동으로 self._login_slot을 호출해 로그인 응답을 처리함.
        self.OnReceiveTrData.connect(self._on_receive_tr_data)  #마찬가지로 이벤트 함수, TR조회 이벤트 발생하여 성공했을 때 자동으로 _on_receive_tr_data로 호출
        self.OnReceiveMsg.connect(self._on_receive_msg) #TR/주문 메시지를 _on_receive_msg로
        self.OnReceiveChejanData.connect(self._on_chejan_slot)  #접수/체결 결과를 _on_chejan_slot으로
        self.OnReceiveRealData.connect(self._on_receive_real_data)  #실시간 체결 데이터를 _on_receive_data로

    def _login_slot(self, err_code):    #로그인 여부를 저장할 slot(err_code), 0일 경우 성공, 그 외 오류코드가 저장됨.
        if err_code == 0:
            print("connected")
        else:
            print("not connected")

        self.login_event_loop.exit()    #로그인 응답 대기를 종료하는 코드

    def _comm_connect(self):    #로그인을 요청할 함수
        self.dynamicCall(("CommConnect"))

        self.login_event_loop = QEventLoop()    #로그인이 되지 않으면 다른 코드 동작에 에러가 발생하므로, 로그인 응답 대기 설정
        self.login_event_loop.exec_()

    def get_account_number(self, tag="ACCNO"):  #ACCNO는 계좌번호 목록을 반환, 이를 변경한 다른 함수를 정의하면 다른 로그인 정보(ID,이름,보유계좌 갯수 등)를 얻어올 수도 있을 것.
        account_list = self.dynamicCall("GetLoginInfo(QString)", tag)  #로그인과 달리 요청과 동시에 응답을 받아옴. 따라서 별다른 응답 slot이 필요하지 않음.
        account_number = account_list.split(';')[0] #(보유했을 경우)여러개의 계좌 중 첫 번째 계좌번호에 접근
        print("ACCNO : {}".format(account_number))
        return account_number

    def get_account_info(self, tag="ACCNO"):  #ACCNO는 계좌번호 목록을 반환, 이를 변경한 다른 함수를 정의하면 다른 로그인 정보(ID,이름,보유계좌 갯수 등)를 얻어올 수도 있을 것.
        account_list = self.dynamicCall("GetLoginInfo(QString)", tag)  #로그인과 달리 요청과 동시에 응답을 받아옴. 따라서 별다른 응답 slot이 필요하지 않음.
        account_info = account_list.split(';')[0] #(보유했을 경우)여러개의 계좌 중 첫 번째 계좌번호에 접근
        print("ACCNO : {}".format(account_info))
        return account_info

    def get_code_list_by_market(self, market_type): #특정 주식 시장(코스피, 코스닥, ELW, ETF, 뮤추얼펀드...)의 종목코드 리스트를 불러오는 함수, market_type을 ""공백으로 하면 전체시장
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_type)
        code_list = code_list.split(';')[:-1] #';'가 각 종목코드의 마지막에 붙어 하나의 String으로 연결되어 있기 때문에, 이를 각각 분할함과 동시에 *마지막 ';'가 공백으로 삽입되는 것을 제거함*
        return code_list

    def get_master_code_name(self, code):  #종목코드에 해당하는 종목명을 전달하는 함수
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_price_data_daily(self, code):   #상장 이후 가장 최근 일자까지의 일봉 정보를 가져옴
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 0, "0001")   #같은 screen_no로 데이터 요청을 빠르게 반복하는 경우 데이터 유효성 보장이 안되니 나중에 확인

        self.tr_event_loop.exec_()  #요청이 끝날때까지 대기 진입

        ohlcv = self.tr_data

        while self.has_next_tr_data:    #1회당 최대 조회 가능 수 이상일 시 반복하여 ohlcv에 삽입
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 2, "0001")

            self.tr_event_loop.exec_()  #요청이 끝날때까지 대기 진입

            for key, val in self.tr_data.items():
                ohlcv[key][-1:] = val   #추가로 받은 데이터를 이어붙임.

        df = pd.DataFrame(ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=ohlcv['data'])

        return df[::-1]

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):    #TR별 데이터를 가져오는 코드 정의, 매개변수 중 사용되지 않는 것 있음.
        self.count += 1
        print("[Kiwoom] _on_receive_tr_data is called {} / {} / {} / {} times.".format(screen_no, rqname, trcode, self.count))    #TR 조회에 대한 응답을 얼마나 수신하였는지 알려주는 용도
        tr_data_cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)    #데이터 수신 시 멀티데이터의 갯수를 얻어오는 용도

        if next == '2':     #1회당 최대 조회 가능 수 이상의 데이터가 있을 경우, 이를 지속적으로 불러오기 위한 용도
            self.has_next_tr_data = True
        else:
            self.has_next_tr_data = False

        if rqname == "opt10081_req":    #opt10081은 '주식일봉차트조회요청'의 sRQName
            ohlcv = {'data': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}  #ohlcv = 각 변수의 첫 글자

            for i in range(tr_data_cnt):
                data = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "일자")  #해당 trcode와 rqname에 해당하는 호출 데이터들을 순서대로 집어넣음.
                open = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "시가")
                high = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "고가")
                low = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "저가")
                close = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                volume = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "거래량")

                ohlcv['data'].append(data.strip())  #자료형 변경
                ohlcv['open'].append(int(open))
                ohlcv['high'].append(int(high))
                ohlcv['low'].append(int(low))
                ohlcv['close'].append(int(close))
                ohlcv['volume'].append(int(volume))

            self.tr_data = ohlcv    #객체를 만든 영역에서 ohlcv에 접근할 수 있도록 해줌.

        elif rqname == "opw00001_req":  #opt10081은 '예수금상세현황요청'의 sRQName
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, 0, "주문가능금액")
            self.tr_data = int(deposit)
            print(self.tr_data)

        elif rqname == "opt10075_req":  #미체결 주문 정보(opt10075)를 얻어옴.
            for i in range(tr_data_cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목코드")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목명")
                order_number = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문상태")
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문가격")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                order_type = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문구분")
                left_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "미체결수량")
                executed_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "체결량")
                ordered_at = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "시간")
                fee = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "당일매매수수료")
                tax = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "당일매매세금")

                code = code.strip()
                code_name = code_name.strip()
                order_number = str(int(order_number.strip()))
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                current_price = int(current_price.strip().lstrip('+').lstrip('-'))
                order_type = order_type.strip().lstrip('+').lstrip('-')     # +매수, -매도처럼 +,-를 제거함
                left_quantity = int(left_quantity.strip())
                executed_quantity = int(executed_quantity.strip())
                ordered_at = ordered_at.strip()
                fee = int(fee)
                tax = int(tax)

                self.order[code] = {
                    '종목코드': code,
                    '종목명': code_name,
                    '주문번호': order_number,
                    '주문상태': order_status,
                    '주문수량': order_quantity,
                    '주문가격': order_price,
                    '현재가': current_price,
                    '주문구분': order_type,
                    '미체결수량': left_quantity,
                    '체결량': executed_quantity,
                    '주문시간': ordered_at,
                    '당일매매수수료': fee,
                    '당일매매세금': tax
                }

            self.tr_data = self.order

        elif rqname == "opw00018_req":  #opw00018 : 계좌 평가 잔고 내역 요청
            for i in range(tr_data_cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목번호")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목명")
                quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "보유수량")
                purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "매입가")
                return_rate = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                total_purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "매입금액")
                available_quatity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "매매가능수량")

                code = code.strip()[1:] #리스트로 변환 및 가공
                code_name = code_name.strip()
                quantity = int(quantity)
                purchase_price = int(purchase_price)
                return_rate = float(return_rate)
                current_price = int(current_price)
                total_purchase_price = int(total_purchase_price)
                available_quatity = int(available_quatity)

                self.balance[code] = {
                    '종목명': code_name,
                    '보유수량': quantity,
                    '매입가': purchase_price,
                    '수익률': return_rate,
                    '현재가': current_price,
                    '매입금액': total_purchase_price,
                    '매매가능수량': available_quatity
                }

            self.tr_data = self.balance

        self.tr_event_loop.exit()   #TR 요청 응답 대기를 종료하는 코드
        time.sleep(0.25)    #키움 API 정책 상 1초에 최대 5회의 요청만 허가됨. 0.2초당 1회씩 요청 가능하나 좀 더 여유있게 0.25초로 설정

    def send_order(self, rqname, screen_no, order_type, code, order_quantity, order_price,  #주문 발생, RQName, 주문유형(매수도, 취소 등), 종목코드, 수량, 가격 등을 매개변수로 받음.
                   order_classification, origin_order_number=""):
        order_result = self.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [rqname, screen_no, self.account_number, order_type, code, order_quantity,
             order_price, order_classification, origin_order_number])
        return order_result

    def set_real_reg(self, str_screen_no, str_code_list, str_fid_list, str_opt_type):   #실시간 체결 정보 수신을 희망하는 종목들을 등록
        self.dynamicCall("SetRealReg(QString, QString, QString, QString", str_screen_no, str_code_list, str_fid_list, str_opt_type)

        time.sleep(0.25)

    def _on_receive_real_data(self, s_code, real_type, real_data):   #실시간 데이터를 수신하는 함수
        if real_type == "장시작시간": #장 시작 시간이 늦어져도 큰큰 문제 없게함.
            pass

        elif real_type == "주식체결":    #체결 정보를 수신할 경우 작동됨.
            signed_at = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("체결시간"))
            close = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("현재가"))
            high = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("고가"))
            open = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("시가"))
            low = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("저가"))
            top_priority_ask = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("(최우선)매도호가"))
            top_priority_bid = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("(최우선)매수호가"))
            accum_volume = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("누적거래량"))

            close = abs(int(close))
            high = abs(int(high))
            open = abs(int(open))
            low = abs(int(low))
            top_priority_ask = abs(int(top_priority_ask))
            top_priority_bid = abs(int(top_priority_bid))
            accum_volume = abs(int(accum_volume))

            print(s_code, signed_at, close, high, open, low, top_priority_ask, top_priority_bid, accum_volume)

            if s_code not in self.universe_realtime_transaction_info:
                self.universe_realtime_transaction_info.update({s_code: {}}) #프로그램 실행 중 지속 갱신해야 하므로 .update를 사용

            self.universe_realtime_transaction_info[s_code].update({        #프로그램 실행 중 지속 갱신해야 하므로 .update를 사용
                "체결시간": signed_at,
                "시가": open,
                "고가": high,
                "저가": low,
                "현재가": close,
                "(최우선)매도호가": top_priority_ask,
                "(최우선)매수호가": top_priority_bid,
                "누적거래량": accum_volume
            })



    def _on_receive_msg(self, screen_no, rqname, trcode, msg):  #어떤 요청에서 온 메세지인지 구분
        print("[Kiwoom] _on_receive_msg is called {} / {} / {} / {}".format(screen_no, rqname, trcode, msg))

    def _on_chejan_slot(self, s_gubun, n_item_cnt, s_fid_list): #체결 정보를 확인
        print("[Kiwoom] _on_chejan_slot is called {} / {} / {}".format(s_gubun, n_item_cnt, s_fid_list))

        for fid in s_fid_list.split(";"):   #받은 긴 텍스트를 ;를 기준으로 구분
            if fid in FID_CODES:            #FID_CODES에 있을 경우
                code = self.dynamicCall("GetChejanData(int)", '9001')[1:]   #종목코드를 얻어와 앞자리에 오는 '문자'를 제거
                data = self.dynamicCall("GetChejanData(int)", fid)          #fid를 사용하여 데이터 얻어오기. ex)fid:9203을 전달하면 주문 번호를 data에 저장
                data = data.strip().lstrip('+').lstrip('-')     #'+'나 '-'가 붙어있으면 제거

                if data.isdigit():      #문자형 데이터 중 숫자인 항목(매수가 등)을 숫자로 바꿈.
                    data = int(data)

                item_name = FID_CODES[fid]  #fid 코드에 해당하는 항목을 FID 에서 찾음.
                print("{}: {}".format(item_name, data)) #가져온 항목 이름과 데이터 출력

                if int(s_gubun) == 0:   #접수/체결(==0)이면 self.order, 잔고이동이면 self.balance에 값 저장
                    if code not in self.order.keys():   #order에 종목코드가 없으면 새로 생성
                        self.order[code] = {}

                    self.order[code].update({item_name: data})  #order 딕셔너리에 저장

                elif int(s_gubun) == 1:
                    if code not in self.balance.keys():   #balance에 종목코드가 없으면 새로 생성
                        self.balance[code] = {}

                    self.balance[code].update({item_name: data})

        if int(s_gubun) == 0:
            print("* 주문 출력(self.order)")
            print(self.order)

        elif int(s_gubun) == 1:
            print("* 잔고 출력(self.balance)")
            print(self.balance)

    def get_order(self):    #미체결 주문 정보(opt10075)를 얻어옴.
        # *다만 주문 관련 정보에 대해 '종목코드'를 키 값으로 하여 딕셔너리에 저장하므로 동일 종목에 대해
        # 당일 두 번 이상의 주문을 하는 분할매매, 동일 종목을 매수 후 바로 매도하는 재주문 등의 경우 마지막 하나의 주문만 order에 저장됨.
        # 이를 해결하기 위해서는 주문 번호를 데이터베이스에 따로 저장하고, 이를 키 값으로 하여 order 딕셔너리에 사용해야함.*
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "전체종목구분", "0")  # 0-전체 1-미체결 2-체결
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10075_req", "opt10075", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    def get_balance(self): #opw00018 : 계좌 평가 잔고 내역 요청
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
        self.dynamicCall("CommRqData(Qstring,QString, int, QString)", "opw00018_req", "opw00018", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    def get_deposit(self):  #현 계좌의 예수금 정보를 가져오는 함수
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
        self.dynamicCall("CommRqData(Qstring,QString, int, QString)", "opw00001_req", "opw00001", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data
