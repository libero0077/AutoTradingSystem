import sqlite3
conn = sqlite3.connect('universe_price.db', isolation_level=None) #universe_price라는 데이터베이스 파일에 연결하겠다는 의미. 있으면 연결, 없으면 생성.
                                                                  #isolation_level을 None으로 하면 일일이 커밋 안해도됨.

def check_table_exist(db_name, table_name):
    with sqlite3.connect('{}.db'.format(db_name)) as con:   #매개변수를 파일명으로 하는 db파일 생성
        cur = con.cursor()
        sql = "SELECT name FROM sqlite_master WHERE type='table' and name=:table_name"  #sqlite_master는 메타데이터
        cur.execute(sql, {"table_name": table_name})

        if len(cur.fetchall()) > 0: #조회한 데이터 개수가 0보다 큰지 확인, 0보다 크면 데이터베이스에 해당 데이터가 있다는 뜻.
            return True
        else:
            return False

def insert_df_to_db(db_name, table_name, df, option="replace"):
    with sqlite3.connect('{}.db'.format(db_name)) as con:
        df.to_sql(table_name, con, if_exists=option)    #to_sql은 DataFrame객체가 사용할 수 있는 함수, 테이블이름, 데이터베이스 연결 객체(con), option(replace(이미 데이터 있으면 이걸로 대체))전달

def execute_sql(db_name, sql, param={}):
    with sqlite3.connect('{}.db'.format(db_name)) as con:
        cur = con.cursor()
        cur.execute(sql, param)
        return cur

# cur = conn.cursor()
# cur.execute('''CREATE TABLE IF NOT EXISTS balance(
#                code varchar(6) PRIMARY KEY,
#                bid_price int(20) NOT NULL,
#                quantity int(20) NOT NULL,
#                created_at varchar(14) NOT NULL,
#                will_clear_at varchar(14)
#                )''')
#
# sql = "insert into balance(code, bid_price, quantity, created_at, will_clear_at) values (?, ?, ?, ?, ?)"
# cur.execute(sql, ('007700', 35000, 30, '20201222', 'today'))    #종목코드, 매수가, 수량, 생성일자(매수일자), 청산예정일자(매도예정일자)
# print(cur.rowcount)

# cur.execute('select * from balance')
# row = cur.fetchone()    #fetchone은 첫 번째 행 데이터만 튜플로 가져옴
# print(row)

# cur.execute('select * from balance')
# rows = cur.fetchall()    #fetchall은 모든 행 데이터를 튜플로 하여 리스트로 보여줌
# print(rows)
# for row in rows:    #튜플안쓰고 출력하고싶으면 이렇게해도됨.
#     code, bid_price, quantity, created_at, will_clear_at = row
#     print(code, bid_price, quantity, created_at, will_clear_at)

# sql = 'select * from balance where code = :code and created_at = :created_at' #특정 조건에 해당하는 값만 추출
# cur.execute(sql, {"code": '007700', 'created_at': '20201222'})
# row = cur.fetchone()
# print(row)

# sql = "update balance set will_clear_at=:will_clear_at where bid_price=:bid_price" #update+테이블이름+set+업데이트할 column+where+column
# cur.execute(sql, {"will_clear_at": "next", "bid_price": 70000}) #bid_price가 70000인 row만 will_clear_at을 next로 변경
# print(cur.rowcount)

# sql = "delete from balance where will_clear_at=:will_clear_at"
# cur.execute(sql, {"will_clear_at": "next"})

# conn.close()    #DB 사용 종료
# with splite3.connect('universe_price.db') as conn:  #연결 이후 conn.close 자동 수행, isolation level 세팅 안해도 자동 커밋
#     cur = conn.cursor()