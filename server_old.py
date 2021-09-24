from time import sleep
import time
import sys
import copy
from typing import Callable, Dict
import json
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from twisted.python import log
from twisted.internet import reactor

class ResponseAnswer:
    def __init__(self, response_code = 500, status_code = 8, payload = dict(), request_requiered = True):
        self.response_code = response_code
        self.status_code = status_code
        self.payload = payload
        self.request_requiered = request_requiered

def login_station(payload):
    print("login into station. Payload: ", payload)
    return ResponseAnswer(501, 1)

def logout_station():
    print("logout from station")

def start_exercise():
    print("start exercise")

def stop_exercise():
    print("stop exercise")

RESPONSE_DICT = {
    "id" : "",
    "type" : 1,
    "response": 508,
    "status_code": 0,
    "payload": {}
}

class ServerSocket(WebSocketServerProtocol):

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))
        self._id = "ID"

    def onOpen(self):
        print("WebSocket connection open.")

    def callback_wrapper(self, function : Callable, pyaload : Dict):
        result : ResponseAnswer = function(pyaload)
        if not result.request_requiered:
            return
        response = copy.deepcopy(RESPONSE_DICT)
        response["id"] = self._id
        response["response"] = result.response_code
        response["status_code"] = result.status_code
        response["payload"] = result.payload

        response = str(json.dumps(response))
        response = response.encode('utf8')
        print(response)
        reactor.callFromThread(self.sendMessage, response, False)

    def onMessage(self, payload, isBinary):
        if isBinary:
            self.send_error("Binary Messages currently not supported", 2)
            return

        data_str = str(payload.decode('utf8'))
        try:
            data = json.loads(data_str)
        except json.decoder.JSONDecodeError:
                self.send_error("Wrong JSON Format", 8)
                return

        print("Received Data ", data)
        user_id = data.get("id")
        if user_id is None:
            self.send_error("There is no 'id' field in the request", 8)
            return
        if user_id != self._id:
            self.send_error("Wrong ID", 8)
            return

        message_type = data.get("type")
        if message_type is None:
            self.send_error("There is no 'type' field in the request", 8)
            return
        if message_type != 0:
            self.send_error("Message is no Request Type", 8)
            return

        request = data.get("request")
        if request is None:
            self.send_error("There is no 'request' field in the request", 8)
            return
        if request < 1 or request > 499:
            self.send_error("reqeuest code range must be in the range from 1 to 499", 8)
            return

        payload = data.get("payload")
        if payload is None:
            self.send_error("There is no 'payload' field in the request", 8)
            return

        request_func = self.factory._callbacks.get(request)
        if request_func is None:
            self.send_error("Request currently not implemented", 2)
            return

        reactor.callInThread(self.callback_wrapper, request_func, payload)
        return

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

    def send_error_ts(self, error="Error", satus_code=2, response_code=508):
        reactor.callFromThread(self.send_error, error, satus_code, response_code)

    def send_error(self, error="Error", satus_code=2, response_code=508):
        response = copy.deepcopy(RESPONSE_DICT)
        response["id"] = self._id
        response["response"] = response_code
        response["status_code"] = satus_code
        response["payload"] = {"error" : error}
        response = str(json.dumps(response))
        print(response)
        self.sendMessage(response.encode('utf8'), isBinary=False)

class ServerController(WebSocketServerFactory):

    def __init__(self, uri):
        WebSocketServerFactory.__init__(self, uri)
        self._callbacks : Dict[int, Callable] = {}

    def register_callback(self, message_code : int, callback : Callable):
        self._callbacks[message_code] = callback

if __name__ == '__main__':
    server_controller = ServerController("ws://127.0.0.1:9000")
    server_controller.register_callback(1, login_station)
    server_controller.protocol = ServerSocket
    reactor.listenTCP(9000, server_controller)
    reactor.run()
