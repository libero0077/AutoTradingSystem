import pandas as pd
import gdown

def download_sentiment_data():
    url = 'https://drive.google.com/uc?id=1yP8CGhLg5asTgI-ROQryiV0fvh1dj1PG'
    output = 'sentiment.xlsx'
    gdown.download(url, output, quiet=False)

def get_sentiment_data(code_dict):
    df = pd.read_excel('C:/Users/ljj94/PycharmProjects/SystemTrading/util/sentiment.xlsx')
    st = df.set_index('종목명').T.to_dict('index')
    st = st['감성수치']
    sentiment = {}
    for i in code_dict:
        sentiment[code_dict[i]] = st[i]
    return sentiment