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
        url = f'{os.getenv("TEST_URL")}getToken'
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

    def sell(self):
        data =  json.dumps({
            "external_id": str(time.time()).replace('.',''),
                "receipt":{
                    "client":{
                        "email":""
                    },
                    "company":{
                        "email":"chek@romashka.ru",
                        "inn": os.getenv('TEST_INN'),
                        "payment_address": os.getenv('TEST_SHOP_NAME')
                    },
                    "items":[
                        {
                            "name":"Монитор Samsung C27F390FHI",
                            "price":16459.00,
                            "quantity":1,
                            "sum":16459.00,
                            "measurement_unit":"Еденица",
                            "payment_method":"partial_payment",
                            "payment_object":"service",
                            "vat":{
                                "type":"none"
                            }
                        }
                    ],
                "payments":[
                    {
                        "type":1,
                        "sum":23584.0
                    }
                ],
                "total":43584.0
                },
                "service":{
                    "callback_url":"http://testtest"
                },
            "timestamp": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        })
        r_headers = self.headers
        r_headers['Token'] = self.redis.get('token')
        logger.debug(r_headers)
        url = f'{os.getenv("TEST_URL")}{os.getenv("TEST_GROUP_CODE")}/sell'
        response = requests.post(
            url,
            data=data,
            headers=r_headers
        ).json()
        if not response['error']:
            logger.debug(response)

    def check_status(self, uuid):
        url = f'{os.getenv("TEST_URL")}{os.getenv("TEST_GROUP_CODE")}/report/{uuid}'
        response = requests.post(
            url,
            headers=self.headers
        ).json()
        if not response['error']:
            logger.debug(response)


if __name__ == '__main__':
    kkt_test = KktHendler(
        os.getenv('TEST_LOGIN'),
        os.getenv('TEST_PASS')
    )
    kkt_test.sell()
