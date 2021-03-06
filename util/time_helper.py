#장 종료인지 장 중인지 확인함, 동시 호가(15:20~15:30) 제외
from datetime import datetime

def check_transaction_open():
    now = datetime.now()
    start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=20, second=0, microsecond=0)
    return start_time <= now <= end_time

def check_transaction_closed():
    now = datetime.now()
    end_time = now.replace(hour=15, minute=20, second=0, microsecond=0)
    return end_time < now

def check_adjacent_transaction_closed_for_buying():
    now = datetime.now()
    base_time = now.replace(hour=15, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=20, second=0, microsecond=0)
    return base_time <= now < end_time

def check_new_sentiment():
    now = datetime.now()
    start_time = now.replace(hour=8, minute=50, second=0, microsecond=0)
    end_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    return start_time <= now <=end_time