"""Air Canvas: draw in the air with your index finger.

Gestures
  - Index finger up                -> draw
  - Index + middle finger up       -> select mode (hover a button in the top bar to pick it)
  - Any other hand shape           -> pause (no drawing)

Keys: c = clear, s = save, q or Esc = quit
"""
import time
from datetime import datetime

import cv2
import mediapipe as mp
import numpy as np

W, H = 1280, 720
HEADER = 100
BRUSH = 8
ERASER = 50
SMOOTH = 0.5          # 0 = no smoothing, closer to 1 = smoother but laggier
COOLDOWN = 1.0        # seconds between Clear / Save triggers

# (label, BGR colour or None for actions)
BUTTONS = [
    ("Red", (60, 60, 240)),
    ("Blue", (240, 150, 40)),
    ("Green", (90, 200, 90)),
    ("Yellow", (40, 220, 240)),
    ("Eraser", (0, 0, 0)),
    ("Clear", None),
    ("Save", None),
]

TIPS = [8, 12, 16, 20]   # index, middle, ring, pinky tips
PIPS = [6, 10, 14, 18]   # the joints below each tip


def button_rects():
    n = len(BUTTONS)
    width = W // n
    return [(i * width, 0, (i + 1) * width, HEADER) for i in range(n)]


def draw_header(frame, selected):
    for i, ((label, colour), (x1, y1, x2, y2)) in enumerate(zip(BUTTONS, button_rects())):
        fill = colour if colour is not None else (70, 70, 70)
        if label == "Eraser":
            fill = (110, 110, 110)
        cv2.rectangle(frame, (x1 + 6, y1 + 6), (x2 - 6, y2 - 6), fill, -1)
        if i == selected:
            cv2.rectangle(frame, (x1 + 6, y1 + 6), (x2 - 6, y2 - 6), (255, 255, 255), 4)
        text_colour = (0, 0, 0) if label == "Yellow" else (255, 255, 255)
        size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        cv2.putText(frame, label, (x1 + (x2 - x1 - size[0]) // 2, y1 + 58),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_colour, 2)


def save_drawing(canvas):
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    out = np.full_like(canvas, 255)
    out[gray > 10] = canvas[gray > 10]
    name = datetime.now().strftime("drawing_%Y%m%d_%H%M%S.png")
    cv2.imwrite(name, out)
    print(f"Saved {name}")
    return name


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("Could not open the webcam. Check camera permission for your terminal or VS Code.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    rects = button_rects()

    canvas = np.zeros((H, W, 3), np.uint8)
    colour = BUTTONS[0][1]
    selected = 0
    prev = None
    smooth_pt = None
    last_action = 0.0
    message, message_until = "", 0.0

    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7,
                        min_tracking_confidence=0.6) as hands:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (W, H))
            result = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            mode = "No hand"
            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
                lm = hand.landmark

                raw = np.array([lm[8].x * W, lm[8].y * H])
                smooth_pt = raw if smooth_pt is None else SMOOTH * smooth_pt + (1 - SMOOTH) * raw
                x, y = int(smooth_pt[0]), int(smooth_pt[1])

                up = [lm[t].y < lm[p].y for t, p in zip(TIPS, PIPS)]
                index_up, middle_up = up[0], up[1]
                others_up = up[2] or up[3]

                if (index_up and middle_up and not others_up) or(index_up and y < HEADER):
                    mode = "Select"
                    prev = None
                    cv2.circle(frame, (x, y), 18, colour if colour != (0, 0, 0) else (200, 200, 200), 3)
                    if y < HEADER:
                        for i, (x1, y1, x2, y2) in enumerate(rects):
                            if x1 <= x < x2:
                                label, col = BUTTONS[i]
                                now = time.time()
                                if label == "Clear" and now - last_action > COOLDOWN:
                                    canvas[:] = 0
                                    last_action = now
                                    message, message_until = "Canvas cleared", now + 1.5
                                elif label == "Save" and now - last_action > COOLDOWN:
                                    message = f"Saved {save_drawing(canvas)}"
                                    last_action = now
                                    message_until = now + 2.5
                                elif col is not None:
                                    colour, selected = col, i
                elif index_up and not others_up and not middle_up:
                    mode = "Draw"
                    if y > HEADER:
                        size = ERASER if colour == (0, 0, 0) else BRUSH
                        if prev is not None:
                            cv2.line(canvas, prev, (x, y), colour, size)
                        prev = (x, y)
                        cv2.circle(frame, (x, y), size // 2 + 2,
                                   (200, 200, 200) if colour == (0, 0, 0) else colour, -1)
                    else:
                        prev = None
                else:
                    mode = "Paused"
                    prev = None
            else:
                prev = None
                smooth_pt = None

            # blend the canvas onto the camera frame
            gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
            _, inv = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)
            frame = cv2.bitwise_and(frame, cv2.cvtColor(inv, cv2.COLOR_GRAY2BGR))
            frame = cv2.bitwise_or(frame, canvas)

            draw_header(frame, selected)
            cv2.putText(frame, f"Mode: {mode}", (20, H - 20), cv2.FONT_HERSHEY_SIMPLEX,
                        0.9, (255, 255, 255), 2)
            if time.time() < message_until:
                cv2.putText(frame, message, (20, H - 60), cv2.FONT_HERSHEY_SIMPLEX,
                            0.9, (0, 255, 255), 2)

            cv2.imshow("Air Canvas", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("c"):
                canvas[:] = 0
            if key == ord("s"):
                message, message_until = f"Saved {save_drawing(canvas)}", time.time() + 2.5

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
