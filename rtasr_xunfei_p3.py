# -*- encoding:utf-8 -*-

import base64
import hashlib
import hmac
import json
import logging
import threading
import time
from hashlib import sha1
from socket import *
from urllib.parse import quote

import websocket
from websocket import create_connection

logging.basicConfig(level=logging.DEBUG)

base_url = ""
app_id = ""
api_key = ""

end_tag = "{\"end\": true}"


class Client():
    def __init__(self):
        # 生成鉴权参数
        ts = str(int(time.time()))
        tmp = app_id + ts
        hl = hashlib.md5()
        hl.update(tmp.encode(encoding='utf-8'))
        my_sign = hmac.new(api_key.encode(), hl.hexdigest().encode(), sha1).digest()
        signa = base64.b64encode(my_sign)

        self.ws = create_connection(base_url + "?appid=" + app_id + "&ts=" + ts + "&signa=" + quote(signa))
        self.trecv = threading.Thread(target=self.recv)
        self.trecv.start()

    def send(self, file_path):
        file_object = open(file_path, 'rb')
        try:
            index = 1
            while True:
                chunk = file_object.read(1280)
                if not chunk:
                    break
                self.ws.send(chunk)

                index += 1
                time.sleep(0.04)
        finally:
            # print str(index) + ", read len:" + str(len(chunk)) + ", file tell:" + str(file_object.tell())
            file_object.close()

        self.ws.send(end_tag.encode())
        print("send end tag success")

    def recv(self):
        try:
            while self.ws.connected:
                result = str(self.ws.recv())
                if len(result) == 0:
                    print("receive result end")
                    break
                result_dict = json.loads(result)

                # 解析结果
                if result_dict["action"] == "started":
                    print("handshake success, result: " + result)

                if result_dict["action"] == "result":
                    # 过滤中间结果
                    result_json = json.loads(result)
                    data_str = result_json['data']
                    data_json = json.loads(data_str)
                    if data_json['cn']['st']['type'] == '0':
                        # print("rtasr result:\n" + json.dumps(data_json, ensure_ascii=False))
                        print(parse_rtasr_sentence(data_str))
                    else:
                        # print('中间结果 {}')
                        pass

                if result_dict["action"] == "error":
                    print("rtasr error: " + result)
                    self.ws.close()
                    return
        except websocket.WebSocketConnectionClosedException:
            print("receive result end")

    def close(self):
        self.ws.close()
        print("connection closed")


def parse_rtasr_sentence(data):
    data_json = json.loads(data)
    ws = data_json['cn']['st']['rt'][0]['ws']
    sentence = ''.join(w['cw'][0]['w'] for w in ws)
    return sentence


if __name__ == '__main__':
    file_path = "./test_1.pcm"
    client = Client()
    client.send(file_path)
