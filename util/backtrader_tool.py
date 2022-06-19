import backtrader as bt
from pykrx import stock
import pandas as pd

class SmaCross(bt.Strategy):
    #볼린저 밴드에 사용할 이동평균 일수와 표준편차에 곱할 상수를 정의
    params = (
        ("period", 20),
        ("devfactor", 2),
        ("ma20", 20),
        ("ma60", 60),
        ("debug", False)
    )

    def log(self, txt, dt=None):
        #프롬프트에 매수 or 매도, 매수매도 가격, 개수를 출력
        dt = dt or self.data.datetime[0]
        if isinstance(dt, float):
            dt = bt.num2date(dt)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        self.boll = bt.indicators.BollingerBands(period=self.p.period, devfactor=self.p.devfactor, plot=True)
        # 볼린저밴드 indicators를 가져옴
        self.sma20 = bt.ind.SMA(period=self.p.ma20)
        self.sma60 = bt.ind.SMA(period=self.p.ma60)
        self.rsi2 = bt.indicators.RSI(self.data.close, period=2)
        self.rsi14 = bt.indicators.RSI(self.data.close, period=14)


    def next(self):
        global buy_price
        if not self.position:   #매수한 종목이 없고
            if (self.sma20[0] > self.sma60[0] and
                self.rsi2 < 5 and
                (data.close[0] - data.close[2]) / data.close[0] * 100 > -2 and
                data.close[0] < self.sma20[0] and
                30 < self.rsi14 < 40 and
                data.close[0] > data.open[0]) :
                buy_price = data.close[0]
                self.buy()   #매수, size = 구매 개수 설정


        else:
            if self.rsi2 > 80 and data.close[0] > buy_price or data.close[0] > self.boll.lines.top[0] :
                self.sell() #20일 이평선=볼린저밴드 중심에서 매도

data=pd.read_excel('C:\Users\ljj94\PycharmProjects\SystemTrading')

size = 0
stock_name = "KODEX 코스피100"
stock_from = "20200101"
stock_to = "20220506"

# if stock_name == "KODEX 코스피100":
#     stock_list = pd.DataFrame({'종목코드': stock.get_etf_ticker_list(stock_to)})
#     stock_list['종목명'] = stock_list['종목코드'].map(lambda x: stock.get_etf_ticker_name(x))
#     stock_list.head()
#
#     ticker = stock_list.loc[stock_list['종목명'] == stock_name, '종목코드']
#     df = stock.get_market_ohlcv_by_date(fromdate=stock_from, todate=stock_to, ticker=ticker)
#     # df = df.drop(['NAV', '거래대금', '기초지수'], axis=1)
#     df = df.rename(columns={'시가': 'open', '고가': 'high', '저가': 'low', '종가': 'close', '거래량': 'volume'})
#
#     df["open"] = df["open"].apply(pd.to_numeric, errors="coerce")
#     df["high"] = df["high"].apply(pd.to_numeric, errors="coerce")
#     df["low"] = df["low"].apply(pd.to_numeric, errors="coerce")
#     df["close"] = df["close"].apply(pd.to_numeric, errors="coerce")
#     df["volume"] = df["volume"].apply(pd.to_numeric, errors="coerce")
#
#     data = bt.feeds.PandasData(dataname=df)
#
#
#
# else:
stock_list = pd.DataFrame({'종목코드': stock.get_market_ticker_list(stock_to)})
stock_list['종목명'] = stock_list['종목코드'].map(lambda x: stock.get_market_ticker_name(x))
stock_list.head()

# ticker = stock_list.loc[stock_list['종목명'] == stock_name, '종목코드']
df = stock.get_market_ohlcv_by_date(fromdate=stock_from, todate=stock_to, ticker=stock_name)
# df = df.drop(['NAV', '거래대금', '기초지수'], axis=1)
df = df.rename(columns={'시가': 'open', '고가': 'high', '저가': 'low', '종가': 'close', '거래량': 'volume'})

df["open"] = df["open"].apply(pd.to_numeric, errors="coerce")
df["high"] = df["high"].apply(pd.to_numeric, errors="coerce")
df["low"] = df["low"].apply(pd.to_numeric, errors="coerce")
df["close"] = df["close"].apply(pd.to_numeric, errors="coerce")
df["volume"] = df["volume"].apply(pd.to_numeric, errors="coerce")

data = bt.feeds.PandasData(dataname=df)

cerebro = bt.Cerebro()  # create a "Cerebro" engine instance
cerebro.broker.setcash(1000000)
cerebro.broker.setcommission(0.00015)  # 0.015% 수수료

cerebro.adddata(data)  # Add the data feed
cerebro.addstrategy(SmaCross)  # Add the trading strategy
cerebro.run()  # run it all
cerebro.plot(style='candlestick', barup='red', bardown='blue', xtight=True, ytight=True, grid=True)  # and plot it with a single command