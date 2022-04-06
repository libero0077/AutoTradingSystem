import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from datetime import datetime

BASE_URL = 'https://finance.naver.com/sise/sise_market_sum.nhn?sosok='  #네이버금융 기본 URL
CODES = [0, 1] #KOSPI=0, KOSDAQ=1
START_PAGE = 1
fields = []

now = datetime.now()
formattedDate = now.strftime("%Y%m%d")

def execute_crawler():
    df_total = []

    for code in CODES:
        res = requests.get(BASE_URL + str(CODES[0])) #total page를 가져오는 request
        page_soup = BeautifulSoup(res.text, 'lxml')

        total_page_num = page_soup.select_one('td.pgRR > a')  #맨뒤에 해당하는 태그를 기준으로 전체 페이지수 추출, page_soup에서 클래스가 pgRR인 <td>태그 하단 <a> 태그를 하나만 선택(select_one)
        total_page_num = int(total_page_num.get('href').split('=')[-1]) #herf값을 =을 기준으로 split하여 마지막 값을 가져옴

        ipt_html = page_soup.select_one('div.subcnt_sise_item_top')  # 조회가능한 항목 추출

        global fields
        fields = [item.get('value') for item in ipt_html.select('input')]

        result = [crawler(code, str(page)) for page in range(1, total_page_num + 1)]    #각 페이지에 존재하는 모든 항목 정보를 result에 저장

        df = pd.concat(result, axis=0, ignore_index=True) #전체 페이지를 저장한 result를 하나의 데이터프레임으로 치환

        df_total.append(df) #df를 합치기 위해 df_total에 저장

    df_total = pd.concat(df_total)  #df_total을 하나의 데이터프레임으로 만듦
    df_total.reset_index(inplace=True, drop=True)   #합친 데이터프레임을 새로 indexing
    df_total.to_excel('NaverFinance.xlsx')  #엑셀로 출력

    return df_total

def crawler(code, page):

    global fields

    data = {'menu': 'market_sum',   #NaverFinace에는 menu, fieldIds, returnUrl을 전달해야 함
            'fieldIds': fields,
            'returnUrl': BASE_URL + str(code) + "&page=" + str(page)}

    res = requests.post('https://finance.naver.com/sise/field_submit.nhn', data=data)

    page_soup = BeautifulSoup(res.text, 'lxml')

    table_html = page_soup.select_one('div.box_type_l')  #크롤링할 table의 html을 가져오는 코드(크롤링 대상 요소의 클래스는 각 웹 브라우저에서 확인 필요

    header_data = [item.get_text().strip() for item in table_html.select('thead th')][1:-1] #column 이름을 가공

    inner_data = [item.get_text().strip() for item in table_html.find_all(lambda x:
                                                                          (x.name == 'a' and
                                                                           'tltle' in x.get('class', [])) or
                                                                          (x.name == 'td' and
                                                                           'number' in x.get('class', []))
                                                                          )]

    no_data = [item.get_text().strip() for item in table_html.select('td.no')]  #페이지마다 있는 종목의 순번 get
    number_data = np.array(inner_data)

    number_data.resize(len(no_data), len(header_data))

    df = pd.DataFrame(data=number_data, columns=header_data)
    return df

def get_universe():
    df = execute_crawler()  #크롤링 결과를 받아옴

    mapping = {',': '', 'N/A': '0'}
    df.replace(mapping, regex=True, inplace=True)

    cols = ['거래량', '매출액', '매출액증가율', 'ROE', 'PER']   #사용할 column을 설정

    df[cols] = df[cols].astype(float)   #column들을 숫자 타입으로 변환(NaverFinance를 크롤링해 온 데이터는 str로 되어있음)

    df = df[(df['거래량'] > 0) & (df['매출액'] > 0) & (df['매출액증가율'] > 0) & (df['ROE'] > 0) & (df['PER'] > 0) & (~df.종목명.str.contains("지주")) & (~df.종목명.str.contains("홀딩스"))]

    df['1/PER'] = 1/df['PER']   #PER 역수

    df['RANK_ROE'] = df['ROE'].rank(method='max', ascending=False) #ROE 순위계산

    df['RANK_1/PER'] = df['1/PER'].rank(method='max', ascending=False)  #1/PER의 순위계산

    df['RANK_VALUE'] = (df['RANK_ROE'] + df['RANK_1/PER']) / 2  #ROE순위, 1/PER 순위를 합산한 랭킹

    df = df.sort_values(by=['RANK_VALUE'])  #RANK_VALUE를 기준으로 정렬

    df.reset_index(inplace=True, drop=True) #필터링한 데이터프레임의 index 번호를 새로 매김

    df = df.loc[:199]   #상위 200개만 추출

    df.to_excel('universe.xlsx')
    return df['종목명'].tolist()

if __name__ == "__main__":  #이 모듈을 import할 때 이 코드들은 실행되지 않게 함함
    print('Start')
    # execute_crawler()
    # get_universe()
    get_universe()
    print('End')