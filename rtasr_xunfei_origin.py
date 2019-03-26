#-*- encoding:utf-8 -*-

import sys
import hashlib
from hashlib import sha1
import hmac
import base64
from socket import *
import json, time, threading
from websocket import create_connection
import websocket
from urllib import quote
import logging

sys.setdefaultencoding("utf8")
logging.basicConfig()

base_url = "ws://rtasr.xfyun.cn/v1/ws"
app_id = "5c889ac7"
api_key = "e2b2ab4f99ec49a755dc5b2fa81673fb"
file_path = "./test_1.pcm"

end_tag = "{\"end\": true}"

class Client():
    def __init__(self):
        # 生成鉴权参数
        ts = str(int (time.time()))
        tmp = app_id + ts
        hl = hashlib.md5()
        hl.update(tmp.encode(encoding='utf-8'))
        my_sign = hmac.new(api_key,  hl.hexdigest(), sha1).digest()
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

        self.ws.send(bytes(end_tag))
        print "send end tag success"

    def recv(self):
        try:
            while self.ws.connected:
                result = str(self.ws.recv())
                if len(result) == 0:
                    print "receive result end"
                    break
                result_dict = json.loads(result)

                # 解析结果
                if result_dict["action"] == "started":
                    print "handshake success, result: " + result

                if result_dict["action"] == "result":
                    print "rtasr result: " + result

                if result_dict["action"] == "error":
                    print "rtasr error: " + result
                    self.ws.close()
                    return
        except websocket.WebSocketConnectionClosedException:
            print "receive result end"

    def close(self):
        self.ws.close()
        print "connection closed"

if __name__ == '__main__':
    client = Client()
    client.send(file_path)