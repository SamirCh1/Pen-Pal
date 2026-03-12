import websocket
import base64
import json
import time
import sys

def dummy_do_turn(n):
    # this should block until the turn is finished, detected via button or CV etc
    # it should then return the lines/svg
    print("doing our turn")
    time.sleep(1)
    return f"<svg>{n}</svg>"

def dummy_block_on_draw_lines(lines):
    # this should block until the lines have been drawn
    print("started drawing")
    time.sleep(1)
    print(lines)

def main():
    # testing, set as either client 1 or 2
    if sys.argv[1] == "1":
        token = int.to_bytes(0, 8)
    elif sys.argv[1] == "2":
        token = int.to_bytes(1 << 56, 8)
    else:
        print("invalid client number")
        return

    ws = websocket.WebSocket()
    try:
        ws.connect("ws://localhost:3000/ws", header = {
            "Authorization": base64.urlsafe_b64encode(token).decode()
        })
    except Exception as e:
        print("Failed to connect to server", e)
        return

    print("Waiting for session to start...")
    msg = json.loads(ws.recv())
    if msg["type"] != "START_SESSION":
        print("Server error")
        return
    session_id = msg["session_id"]
    print("Session started")

    while True:
        msg = json.loads(ws.recv())
        assert msg["session_id"] == session_id
        match msg["type"]:
            case "TURN":
                lines = dummy_do_turn(sys.argv[1])
                submit_msg = {
                    "type": "SUBMIT",
                    "session_id": session_id,
                    "svg": lines 
                }
                ws.send(json.dumps(submit_msg))
            case "DRAW":
                dummy_block_on_draw_lines(msg["svg"])

if __name__ == "__main__":
    main()

