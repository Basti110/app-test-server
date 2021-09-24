import copy
import traceback
from typing import Callable, Dict
import json
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from twisted.internet import reactor

class ResponseAnswer:
    def __init__(self, response_code = 500, status_code = 8, payload = dict(), request_requiered = True):
        self.response_code = response_code
        self.status_code = status_code
        self.payload = payload
        self.request_requiered = request_requiered


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
        self._id = "id123"
        if self.factory._register_client_callback is not None:
            self.factory._register_client_callback(self._id, self.send_msg_ts)

    def onOpen(self):
        print("### New Connection ###")
        response = copy.deepcopy(RESPONSE_DICT)
        response["id"] = self._id
        response["response"] = 500
        response["status_code"] = 1
        response = json.dumps(response).encode('utf8')
        self.sendMessage(response, False)

    def callback_wrapper(self, function : Callable, pyaload : Dict):
        #pylint: disable=broad-except
        try :
            result : ResponseAnswer = function(self._id, pyaload)
        except Exception as exception:
            self.send_error_ts(str(exception))
            traceback.print_exc()       
            return

        #traceback.print_exc()
        if not result.request_requiered:
            return
            
        self.send_msg_ts(result.response_code, result.status_code, result.payload)

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

        print() #New line 
        
        #print("Received Data ", data)
        #print("Test:", type(data))
        #user_id = data.get("id")
        # if user_id is None:
        #     self.send_error("There is no 'id' field in the request", 8)
        #     return
        # if user_id != self._id:
        #     self.send_error("Wrong ID", 8)
        #     return

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
        print("[ERROR]", response)
        self.sendMessage(response.encode('utf8'), isBinary=False)

    def send_msg_ts(self, response_code=508, satus_code=2, payload=dict({})):
        response = copy.deepcopy(RESPONSE_DICT)
        response["id"] = self._id
        response["response"] = response_code
        response["status_code"] = satus_code
        response["payload"] = payload
        response = str(json.dumps(response))
        response = response.encode('utf8')
        print("[RESPONSE]", response)
        reactor.callFromThread(self.sendMessage, response, False)

class ServerController(WebSocketServerFactory):

    def __init__(self, uri, register_client_callback = None):
        print("init")
        WebSocketServerFactory.__init__(self, uri)
        self._callbacks : Dict[int, Callable] = {}
        self._register_client_callback = register_client_callback

    def register_callback(self, message_code : int, callback : Callable):
        self._callbacks[message_code] = callback