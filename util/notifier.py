import requests

TARGET_URL = 'https://notify-api.line.me/api/notify'

def send_message(message, token=None):  #메세지 내용, LINE토큰을 받아 전송
    try:
        response = requests.post(
            TARGET_URL,
            headers={
                'Authorization': 'Bearer ' + token
            },
            data={
                'message': message
            }
        )
        status = response.json()['status']

        if status != 200:   #전송 실패 체크
            raise Exception('Fail need to check. Status is %s' % status)    #에러가 발생할 때만 로깅

    except Exception as e:
        raise Exception(e)