from api.Kiwoom import *
from util.make_up_universe import *
from util.db_helper import *
from util.time_helper import *
import math
import traceback

class RSIStrategy(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.strategy_name = "RSIStrategy"
        self.kiwoom = Kiwoom()

        self.universe = {} #유니버스 정보를 담는 딕셔너리
        self.deposit = 0  # 계좌 예수금
        self.is_init_success = False  # 초기화 함수 성공 여부 확인 변수

        self.init_strategy()

    def init_strategy(self):    #전략 초기화 함수
        try:
            self.check_and_get_universe()       #유니버스 생성함수 작동
            self.check_and_get_price_data()     #가격정보 조회, 필요시 생성
            self.kiwoom.get_order()             #주문정보확인
            self.kiwoom.get_balance()           #잔고확인
            self.deposit = self.kiwoom.get_deposit()    #예수금확인
            self.set_universe_real_time()       #유니버스 실시간 체결 정보 등록
            self.is_init_success = True         #여기까지 도달할때에만 True로 바꿈

        except Exception as e:
            print(traceback.format_exc())

    def check_and_get_universe(self):   #유니버스 존재 유무 확인, 없으면 생성
        if not check_table_exist(self.strategy_name, 'universe'):
            universe_list = get_universe()
            print(universe_list)
            universe = {}
            now = datetime.now().strftime("%Y%m%d")

            kospi_code_list = self.kiwoom.get_code_list_by_market("0") #KOSPI(0)에 상당된 모든 종목 코드를 가져와 kospi_code_list에 저장
            kosdaq_code_list = self.kiwoom.get_code_list_by_market("10") #KOSDAQ(10)에 상당된 모든 종목 코드를 가져와 kospi_code_list에 저장

            for code in kospi_code_list + kosdaq_code_list:
                code_name = self.kiwoom.get_master_code_name(code)

                if code_name in universe_list:
                    universe[code] = code_name

            universe_df = pd.DataFrame({    #코드, 종목명, 생성일자를 열로 가지는 DataFrame 생성
                'code': universe.keys(),
                'code_name': universe.values(),
                'created_at': [now] * len(universe.keys())
            })

            insert_df_to_db(self.strategy_name, 'universe', universe_df)    #universe라는 이름으로 DB에 저장

        sql = "select * from universe"
        cur = execute_sql(self.strategy_name, sql)
        universe_list = cur.fetchall()
        for item in universe_list:
            idx, code, code_name, created_at = item
            self.universe[code] = {
                'code_name': code_name
            }
        print(self.universe)

    def check_and_get_price_data(self):     #일봉 데이터가 있는지 확인하고 없으면 생성 *주의 : 일봉데이터는 전일(금일제외)까지의 데이터임
        for idx, code in enumerate(self.universe.keys()):
            print("({}/{}) {}".format(idx + 1, len(self.universe), code))

            if check_transaction_closed() and not check_table_exist(self.strategy_name, code):  #일봉 데이터가 아예 없는지 확인(장 종료 이후)
                price_df = self.kiwoom.get_price_data_daily(code)   #API를 이용해 조회한 가격 데이터를 price_df에 저장
                insert_df_to_db(self.strategy_name, code, price_df)    #코드를 테이블 이름으로 해서 데이터베이스에 저장
            else:   #일봉데이터가 있으면
                if check_transaction_closed():  #장이 종료되면 api를 이용해 얻어온 데이터 저장
                    sql = "select max('{}') from '{}'".format('index', code)    #저장된 데이터의 가장 최근 일자 조회
                    cur = execute_sql(self.strategy_name, sql)

                    last_date = cur.fetchall()  #일봉 데이터를 저장한 가장 최근일자 조회

                    now = datetime.now().strftime("%Y%m%d") #오늘 날짜를 yyyymmdd형태로 지정

                    if last_date[0] != now:     #최근 저장 일자가 오늘이 아닌지 확인
                        price_df = self.kiwoon.get_price_date(code)

                        insert_df_to_db(self.strategy_name, code, price_df) #코드를 테이블 이름으로 해서 데이터베이스에 저장

                else:   #장 시작 전이거나 장 중인 경우 데이터베이스에 저장된 데이터 조회
                    sql = "select * from '{}'".format(code)
                    cur = execute_sql(self.strategy_name, sql)
                    cols = [column[0] for column in cur.description]

                    price_df = pd.DataFrame.from_records(data=cur.fetchall(), columns=cols) #데이터베이스에서 조회한 데이터를 DataFrame 형태로 변환해 저장
                    price_df = price_df.set_index('index')
                    self.universe[code]['price_df'] = price_df  #가격데이터를 self.universe에서 접근할 수 있도록 저장

    def set_universe_real_time(self):   #유니버스의 실시간 체결 정보 수신을 등록하는 함수
        fids = get_fid("체결시간") #임의의 fid를 하나 전달, 아무 fid 하나라도 일단 전달해야 정보를 얻어올 수 있기 때문
        # self.kiwoom.set_real_reg("1000", "", get_fid("장운영구분"), "0")

        codes = self.universe.keys()        #universe 딕셔너리의 키 값들은 종목 코드를 의미
        codes = ";".join(map(str, codes))   #종목 코드들을 ; 기준으로 연결

        self.kiwoom.set_real_reg("9999", codes, fids, "0")  #화면번호 9999에 종목코드들의 실시간 체결 정보 수신 요청

    def check_sell_signal(self, code):
        universe_item = self.universe[code]

        if code not in self.kiwoom.universe_realtime_transaction_info.keys():   #체결 정보가 존재하는지 확인
            print("매도대상 확인 과정에서 아직 체결정보가 없습니다.")    #체결 정보가 없으면 함수 종료
            return

        open = self.kiwoom.universe_realtime_transaction_info[code]['시가']   #체결 정보가 존재하면 각 항목 저장
        high = self.kiwoom.universe_realtime_transaction_info[code]['고가']
        low = self.kiwoom.universe_realtime_transaction_info[code]['저가']
        close = self.kiwoom.universe_realtime_transaction_info[code]['현재가']
        volume = self.kiwoom.universe_realtime_transaction_info[code]['누적거래량']

        today_price_data = [open, high, low, close, volume]

        df = universe_item['price_df'].copy()   #원본데이터에 영향을 주지 않기 위해 copy()를 사용

        df.loc[datetime.now().strftime('%Y%m%d')] = today_price_data    #과거 가격 데이터에 금일 날짜 데이터 추가

        # RSI(N) 계산
        period = 2 #기준일 N 설정
        date_index = df.index.astype('str')
        U = np.where(df['close'].diff(1) > 0, df['close'].diff(1), 0)   #df, diff로 '기준일 종가 - 기준일 전일 종가'를 계산하여 0보다 크면 증가분을 넣고, 감소했으면 0을 넣음 *np.where(조건, 참일경우, 거짓일경우)
        D = np.where(df['close'].diff(1) < 0, df['close'].diff(1) * -1, 0)  #df, diff로 '기준일 종가 - 기준일 전일 종가'를 계산하여 0보다 작으면 감소분을 넣고, 증가했으면 0을 넣음

        AU = pd.DataFrame(U, index=date_index).rolling(window=period).mean()    #period일간 U의 평균(AU(period))
        AD = pd.DataFrame(D, index=data_index).rolling(window=period).mean()    #period일간 D의 평균(AD(period))
        RSI = AU / (AD + AU) * 100  #0과 1 사이의 값을 갖는 RSI에 100을 곱함
        df['RSI({})'.format(period)] = RSI

        # 보유 종목의 매입가 조회
        purchase_price = self.kiwoom.balance[code]['매입가']
        rsi = df[-1:]['RSI({})'.format(period)].values[0]   #오늘 RSI(N) 구하기

        if rsi > 80 and close > purchase_price: #조건에 맞을 경우 매도 시그널을 return
            return True
        else:
            return False

    def order_sell(self, code): #매도 주문 접수 함수
        quantity = self.kiwoom.balance[code]['보유수량']    #보유수량 확인
        ask = self.kiwoom.universe_realtime_transaction_info[code]['(최우선)매도호가'] #최우선매도호가확인
        order_result = self.kiwoom.send_order('send_sell_order', '1001', 2, code, quantity, ask, '00')

    def run(self):  #실질적 수행함수
        while self.is_init_success:
            try:
                if not check_transaction_open():
                    print("장시간이 아니므로 5분간 대기합니다.")
                    time.sleep(5 * 60)
                    continue

                for idx, code in enumerate(self.universe.keys()):
                    print('[{}/{}_{}]'.format(idx+1, len(self.universe), self.universe[code]['code_name']))
                    time.sleep(0.25)

                    if code in self.kiwoom.order.keys():    #접수한 주문이 있는지 먼저 확인
                        print('접수 주문', self.kiwoom.order[code])

                        if self.kiwoom.order[code]['미체결수량'] > 0:    #미체결수량을 확인해서 주문상태를 확인, *딕셔너리의 '주문상태'를 확인하면, 일부라도 체결된 경우 '체결'로 변경되기 때문에 미체결수량을 확인하는 것이 좋음
                            pass

                    elif code in self.kiwoom.balance.keys():
                        print('보유 종목', self.kiwoom.balance[code])
                        if self.check_and_sell_signal(code):    #매도 대상인지 확인
                            self.order_sell(code)

                    else:
                        self.check_buy_signal_and_order(code)   #접수 종목, 보유 종목이 아니라면 매수 대상인지 확인 후 주문 접수

            except Exception as e:
                print(traceback.format_exc())

        while True:
            for idx, code in enumerate(self.universe.keys()):
                print('{}/{}_{}'.format(idx+1, len(self.universe), self.universe[code]['code_name']))
                time.sleep(0.25)

                if code in self.kiwoom.universe_realtime_transaction_info.keys():   #현재의 종목 코드가 실시간 체결 정보를 담은 딕셔너리에 있는지 확인해서 출력
                    print(self.kiwoom.universe_realtime_transaction_info[code])