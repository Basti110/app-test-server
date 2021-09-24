from twisted.internet import reactor
from server import ServerController, ServerSocket, ResponseAnswer

class TestServer:
    def __init__(self):
        self._exercise_count = {}
        self._client_callbacks = {}


    def client_callback(self, client_id, callback):
        self._client_callbacks[client_id] = callback

    def login_station(self, user_id, payload):
        print("login into station. Payload: ", payload)
        return ResponseAnswer(501, 1)

    def logout_station(self, user_id, payload):
        print("logout from station. Payload:", payload)
        return ResponseAnswer(502, 1)

    def start_exercise(self, user_id, payload):
        print("start exercise. Payload:", payload)
        self._client_callbacks[user_id](response_code=503, satus_code=1)

        for i in range(8): 
            time.sleep(2)
            self.send_repitition(user_id, i, payload["exercise"], payload["set_id"])

        return ResponseAnswer(request_requiered=False)

    def stop_exercise(self, user_id, payload):
        print("stop exercise. Payload:", payload)
        return ResponseAnswer(504, 1)

    def weight_detection(self, user_id, payload):
        print("Start Weight Detection. Payload:", payload)
        return ResponseAnswer(507, 1, {"weight" : 500.0, "probability" : 0.5})

    def send_repitition(self, user_id : str, repetition : int, exercise : str, set_id : int):
        payload = {
            "repetitions": repetition,
            "exercise": exercise,
            "set_id": set_id
        }
        self._client_callbacks[user_id](response_code=509, satus_code=1, payload=payload)

if __name__ == '__main__':
    server_controller = ServerController("ws://127.0.0.1:3030")
    server_controller.register_callback(1, login_station)
    server_controller.register_callback(2, logout_station)
    server_controller.register_callback(3, start_exercise)
    server_controller.register_callback(4, stop_exercise)
    server_controller.register_callback(7, weight_detection)
    server_controller.protocol = ServerSocket
    reactor.listenTCP(3030, server_controller)
    reactor.run()