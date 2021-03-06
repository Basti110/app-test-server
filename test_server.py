import time
from twisted.internet import reactor
from server import ServerController, ServerSocket, ResponseAnswer

class TestServer:
    def __init__(self):
        self._exercise_count = {}
        self._client_callbacks = {}

        server_controller = ServerController("ws://127.0.0.1:3030", self.client_callback)
        server_controller.register_callback(1, self.login_station)
        server_controller.register_callback(2, self.logout_station)
        server_controller.register_callback(3, self.start_exercise)
        server_controller.register_callback(4, self.stop_exercise)
        server_controller.register_callback(7, self.weight_detection)
        server_controller.protocol = ServerSocket
        reactor.listenTCP(3030, server_controller)
        reactor.run()

    def client_callback(self, client_id, callback):
        print("Register Calback")
        self._client_callbacks[client_id] = callback

    def login_station(self, user_id, payload):
        print("[LOGIN STATION] Payload: ", payload)
        return ResponseAnswer(501, 1)

    def logout_station(self, user_id, payload):
        print("[LOGOUT STATION] Payload:", payload)
        return ResponseAnswer(502, 1)

    def start_exercise(self, user_id, payload):
        print("[START EXERCISE] Payload:", payload)
        self._client_callbacks[user_id](response_code=503, satus_code=1)

        for i in range(8): 
            time.sleep(2)
            self.send_repitition(user_id, i, payload["exercise"], payload["set_id"])

        return ResponseAnswer(request_requiered=False)

    def stop_exercise(self, user_id, payload):
        print("[STOP EXERCISE] Payload:", payload)
        return ResponseAnswer(504, 1)

    def weight_detection(self, user_id, payload):
        print("[WEIGHT DETECTION] Payload:", payload)
        return ResponseAnswer(507, 1, {"weight" : 500.0, "probability" : 0.5})

    def send_repitition(self, user_id : str, repetition : int, exercise, set_id : int):
        payload = {
            "repetitions": repetition,
            "exercise": exercise,
            "set_id": set_id
        }
        self._client_callbacks[user_id](response_code=509, satus_code=1, payload=payload)

if __name__ == '__main__':
    test_server = TestServer()