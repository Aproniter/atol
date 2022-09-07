import os
import json
import time
import requests
import redis

from datetime import datetime
from dotenv import load_dotenv

from logger import Logger


load_dotenv()
logger = Logger('kkt-hendler', 'kkt-hendler').get_logger()


class KktHendler:
    """Класс для работы с API АТОЛ-Онлайн с
    использованием протокола v4"""

    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.headers = {
            'Content-type': 'application/json; charset=utf-8',
        }
        self.redis = self._redis_connection()
        self.token = self._authorized()
        self.template_item = {
            "name": os.getenv('PAYMENT_SERVICE_NAME'),
            "price": 0.00,
            "quantity": 1,
            "sum": 0.00,
            "payment_method": "full_prepayment",
            "payment_object": "service",
            "vat":{
                "type":"none"
            }
        }
        self.template_request = {
            "external_id": str(time.time()).replace('.',''),
            "receipt":{
                "client":{
                    "email": ""
                },
                "company":{
                    "email": os.getenv('EMAIL'),
                    "inn": os.getenv('INN'),
                    "payment_address": os.getenv('SHOP_NAME')
                    },
                "items":[],
                "payments":[
                    {
                        "type": 1,
                        "sum": 0.00
                    }
                ],
                "total": 0.00
                },
                "service":{
                    "callback_url": os.getenv('CALLBACK_URL', '')
                },
            "timestamp": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        }


    def _redis_connection(self):
        """Подключение к Redis"""

        r = redis.StrictRedis(
            host='0.0.0.0',
            port=6379,
            charset="utf-8",
            decode_responses=True
        )
        return r

    def _authorized(self):
        """Получение токена авторизации"""

        data =  json.dumps({
            'login': self.login,
            'pass': self.password
        })
        r_headers = self.headers
        url = f'{os.getenv("URL")}getToken'
        if not self.redis.exists('token'):
            try:
                response = requests.post(
                    url,
                    data=data,
                    headers=r_headers
                ).json()
            except requests.exceptions.RequestException as e:
                logger.error('Ошибка запроса', exc_info=True)
            if response['error']:
                logger.error(f'Авторизация не удалась: {response["error"]}')
                return None
            if not response['error']:
                token_timeout = 60 * 60 * 24
                self.redis.set('token', response['token'], token_timeout)
                logger.info('Получен новый токен')
                return response['token']
        logger.debug(
            f'Используется токен из памяти. До истечения {self.redis.ttl("token")} секунд.'
        )
        return self.redis.get('token')

    def sell(self, data):
        r_headers = self.headers
        r_headers['Token'] = self.redis.get('token')
        url = f'{os.getenv("URL")}{os.getenv("GROUP_CODE")}/sell'
        response = requests.post(
            url,
            data=json.dumps(data),
            headers=r_headers
        ).json()
        if not response['error']:
            logger.debug(response)
        else:
            logger.error(response['error'])

    def check_status(self, uuid):
        url = f'{os.getenv("URL")}{os.getenv("GROUP_CODE")}/report/{uuid}'
        r_headers = self.headers
        r_headers['Token'] = self.redis.get('token')
        logger.debug(r_headers)
        response = requests.get(
            url,
            headers=r_headers
        ).json()
        if not response['error']:
            logger.debug(response)
        else:
            logger.error(response['error'])


if __name__ == '__main__':
    kkt = KktHendler(
        os.getenv('LOGIN'),
        os.getenv('PASS')
    )