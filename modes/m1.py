import mss
import cv2
import numpy as np
import pydirectinput
import time

#FiveM-Checkpoint-Hunter1(Faster-but-Messy)
#don't steal this stupid code and post it... just make it better if you do.
#https://github.com/p0rtwalker/Auto-Checkpoint-FiveM

pydirectinput.FAILSAFE = False
pydirectinput.PAUSE = 0

DISPLAY = {"top": 0, "left": 0, "width": 1920, "height": 1080}
STRIP_HEIGHT = 650
crop = {
    "top": DISPLAY["height"]//2 - STRIP_HEIGHT//2,
    "left": 0,
    "width": DISPLAY["width"],
    "height": STRIP_HEIGHT
}

lower_red = np.array([0, 90, 90])
upper_red = np.array([10, 255, 255])
MIN_AREA = 100
CENTER_TOL = 120

last_red_time = time.time()
last_lost_time = 0
tease_chase_end = 0
burst_end_time = 0
lost_red_sprint_end = 0
last_360_spin = time.time()

def status(text):
    print(f"\r{' ' * 80}", end="\r")  
    print(f"\r[CPTerminator-status:] {text}", end="", flush=True)

print("Starting in 5 sec...", flush=True)
time.sleep(5)
print("""
Started 
you need to be in the game for it to work
-> CTRL + C to stop in the terminal.      
""")

sct = mss.mss()

def release_all():
    for k in 'wad':
        pydirectinput.keyUp(k)

with sct:
    while True:
        img = np.array(sct.grab(crop))
        hsv = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower_red, upper_red)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((10,10), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((10,10), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        current_time = time.time()
        time_without_red = current_time - last_red_time
        release_all()

        red_seen = False

        if contours:
            c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
            if area > MIN_AREA:
                red_seen = True
                last_red_time = current_time
                lost_red_sprint_end = 0
                tease_chase_end = 0

                M = cv2.moments(c)
                cx = int(M['m10']/M['m00'])
                dx = cx - DISPLAY["width"]//2

                if burst_end_time == 0:
                    pydirectinput.keyDown('w')
                    burst_end_time = current_time + 4.0
                    status("RED SPOTTED → 5 SEC FULL BURST!")

                elif current_time < burst_end_time: 
                    burst_end_time = 0

                pydirectinput.keyDown('w')
                if current_time - last_360_spin >= 15:
                    pydirectinput.keyDown('d')
                    time.sleep(1.05)
                    last_360_spin = current_time
                    status("360 SPIN")
                elif abs(dx) > CENTER_TOL:
                    turn_time = min(0.12, abs(dx) * 0.0004)
                    direction = "RIGHT" if dx > 0 else "LEFT"
                    if dx > 0:
                        pydirectinput.keyDown('d'); time.sleep(turn_time)
                    else:
                        pydirectinput.keyDown('a'); time.sleep(turn_time)
                    status(f"STEERING {direction} → DX: {dx:+}")
                else:
                    status("TARGET LOCKED → HOLDING W")
                last_lost_time = 0
                time.sleep(0.01)
                continue

        if not red_seen and last_red_time > last_lost_time and current_time - last_red_time < 1.5:
            last_lost_time = current_time
            if tease_chase_end == 0:
                tease_chase_end = current_time + 6.0
                status("RED TEASED → 6 SEC W LOOKING FORWARD")

        if tease_chase_end > current_time:
            pydirectinput.keyDown('w')
            remaining = int(tease_chase_end - current_time)
            status(f"CHASING TEASE → {remaining}s LEFT!")
            if current_time >= tease_chase_end:
                tease_chase_end = 0
            time.sleep(0.01)
            continue

        if time_without_red >= 55:
            if lost_red_sprint_end == 0:
                lost_red_sprint_end = current_time + 400.0
                status("NO RED FOR 55s → 400+ SEC SEARCH SPRINT!")
            if current_time < lost_red_sprint_end:
                pydirectinput.keyDown('w')
                if int(current_time * 1000) % 3000 < 50:
                    pydirectinput.keyDown('d')
                    time.sleep(0.9)
                remaining = int(lost_red_sprint_end - current_time)
                status(f"SEARCH SPRINT → {remaining}s + SCANNING")
                if current_time >= lost_red_sprint_end:
                    lost_red_sprint_end = 0
                time.sleep(0.01)
                continue

        burst_end_time = 0
        pydirectinput.keyDown('d')
        time.sleep(0.05)
        status(f"SCANNING → {int(time_without_red)}s no red")

        time.sleep(0.01)
