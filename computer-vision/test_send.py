import websocket
import base64
import json
import cv2

from process_image import full_processing_pipeline, get_current_frame, extract_paper

def bridge_loop():
    token = int.to_bytes(0, 8)
    # token = int.to_bytes(1 << 56, 8)

    # cap = cv2.VideoCapture(0) # for pi
    cap = cv2.VideoCapture(1) # for testing
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)


    ws = websocket.WebSocket()
    try:
        ws.connect("ws://10.124.51.109:3000/ws", header = {
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
        print("got to here")
        assert msg["session_id"] == session_id
        if msg["type"] == "TURN":
            print("OUR TURN")
            image = cv2.imread("/home/main/Pictures/temp/picture_2026-03-25_10-28-19.jpg")
            paper = extract_paper(image)
            # paper = get_current_frame(cap)
            lines = full_processing_pipeline(paper)

            submit_msg = {
                "type": "SUBMIT",
                "session_id": session_id,
                "svg": lines
            }
            ws.send(json.dumps(submit_msg))
        if msg["type"] == "DRAW":
            print("OUR DRAW")
            print(msg["svg"])

bridge_loop()
