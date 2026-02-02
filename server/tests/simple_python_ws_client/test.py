import websocket
import base64
import json

ws = websocket.WebSocket()
ws.connect("ws://localhost:3000/ws", header = {
    "Authorization": base64.urlsafe_b64encode(int.to_bytes(0, 8)).decode("ascii")
})

token = 0 | 1 << 56
ws2 = websocket.WebSocket()
ws2.connect("ws://localhost:3000/ws", header = {
    "Authorization": base64.urlsafe_b64encode(token.to_bytes(8)).decode("ascii")
})

print(ws.recv())
print(ws2.recv())
print(ws.recv())

submit_msg = {
    "type": "SUBMIT",
    "session_id": 0,
    "svg": "hello"
}

ws.send(json.dumps(submit_msg))
print(ws2.recv())
print(ws2.recv())

