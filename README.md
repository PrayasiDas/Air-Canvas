# ✋ Air Canvas

Draw in the air with your index finger. Air Canvas tracks your hand through the webcam in real time and turns finger movements into drawings on the screen.

**Demo:** (add your demo GIF or video link here)

## Features
- Real-time hand tracking with MediaPipe
- Gesture controls: index finger to draw, two fingers to select
- Colour palette, eraser, clear, and save-as-image, all controlled by fingertip
- Smoothed line drawing for cleaner strokes

## Gestures
| Gesture | Action |
|---|---|
| Index finger up | Draw |
| Index + middle finger up | Select a button in the top bar |
| Any other hand shape | Pause |

Keyboard shortcuts: `c` clear, `s` save, `q` quit.

## Built With
- Python
- OpenCV
- MediaPipe
- NumPy

## How to Run
1. Clone the repo:
   `git clone https://github.com/PrayasiDas/air-canvas.git`
2. Install requirements:
   `pip install -r requirements.txt`
3. Run:
   `python air_canvas.py`

On a Mac, allow camera access for your terminal or VS Code when asked.

## Author
**Prayasi Das** - [GitHub](https://github.com/PrayasiDas)
