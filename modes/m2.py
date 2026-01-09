import mss
import cv2
import numpy as np
import pydirectinput
import time
from dataclasses import dataclass
from typing import Optional

#FiveM-Checkpoint-Hunter2(Slower-but-Precise)
#don't steal this stupid code and post it... just make it better if you do.
#https://github.com/p0rtwalker/Auto-Checkpoint-FiveM

@dataclass
class Config:
    MONITOR = {"top": 0, "left": 0, "width": 1920, "height": 1080}
    STRIP_HEIGHT = 650
    CROP = {
        "top": MONITOR["height"] // 2 - STRIP_HEIGHT // 2,
        "left": 0,
        "width": MONITOR["width"],
        "height": STRIP_HEIGHT
    }

    LOWER_RED = np.array([0, 90, 90])
    UPPER_RED = np.array([10, 255, 255])
    MIN_AREA = 100
    CENTER_TOLERANCE = 120

    BURST_DURATION = 4.0
    TEASE_CHASE_DURATION = 6.0
    LOST_RED_SPRINT_DURATION = 400.0
    NO_RED_THRESHOLD = 55.0
    SPIN_INTERVAL = 15.0
    TURN_BASE_TIME = 0.0004 


config = Config()

pydirectinput.FAILSAFE = False
pydirectinput.PAUSE = 0


class State:
    def __init__(self):
        self.last_red_time = time.time()
        self.last_lost_time = 0.0
        self.tease_chase_end = 0.0
        self.burst_end_time = 0.0
        self.lost_red_sprint_end = 0.0
        self.last_360_spin = time.time()

    def time_since_red(self):
        return time.time() - self.last_red_time

state = State()


def status(text: str):
    print(f"\r{' ' * 100}\r[CPTerminator] {text}", end="", flush=True)

def release_all_keys():
    for key in 'wasd':
        pydirectinput.keyUp(key)

def press_key(key: str, duration: float):
    pydirectinput.keyDown(key)
    time.sleep(duration)
    pydirectinput.keyUp(key)

def turn_towards(dx: int):
    turn_time = min(0.12, abs(dx) * config.TURN_BASE_TIME)
    direction = 'd' if dx > 0 else 'a'
    direction_name = "RIGHT" if dx > 0 else "LEFT"
    press_key(direction, turn_time)
    status(f"STEERING {direction_name} → DX: {dx:+}")

def do_360_spin():
    status("PERFORMING 360° SPIN")
    press_key('d', 1.05)
    state.last_360_spin = time.time()


def main():
    print("Starting in 5 seconds...")
    time.sleep(5)
    print("""
Started 
you need to be in the game for it to work
-> CTRL + C to stop in the terminal.      
""")

    with mss.mss() as sct:
        while True:
            current_time = time.time()
            img = np.array(sct.grab(config.CROP))
            hsv = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)

            mask = cv2.inRange(hsv, config.LOWER_RED, config.UPPER_RED)
            kernel = np.ones((10, 10), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            release_all_keys()
            red_detected = False

            if contours:
                largest = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)

                if area > config.MIN_AREA:
                    red_detected = True
                    state.last_red_time = current_time
                    state.lost_red_sprint_end = 0
                    state.tease_chase_end = 0

                    M = cv2.moments(largest)
                    if M['m00'] != 0:
                        cx = int(M['m10'] / M['m00'])
                        dx = cx - config.MONITOR["width"] // 2

                        if state.burst_end_time == 0:
                            state.burst_end_time = current_time + config.BURST_DURATION
                            status(f"RED SPOTTED → {config.BURST_DURATION}s FULL BURST!")

                        pydirectinput.keyDown('w')

                        if current_time - state.last_360_spin >= config.SPIN_INTERVAL:
                            do_360_spin()
                        elif abs(dx) > config.CENTER_TOLERANCE:
                            turn_towards(dx)
                        else:
                            status("TARGET LOCKED → STRAIGHT AHEAD")

                        if state.burst_end_time != 0 and current_time >= state.burst_end_time:
                            state.burst_end_time = 0

                        time.sleep(0.01)
                        continue

            if not red_detected and state.last_red_time > state.last_lost_time:
                if current_time - state.last_red_time < 1.5:
                    state.last_lost_time = current_time
                    if state.tease_chase_end == 0:
                        state.tease_chase_end = current_time + config.TEASE_CHASE_DURATION
                        status(f"RED TEASED → {config.TEASE_CHASE_DURATION}s CHASE!")

            if state.tease_chase_end > current_time:
                pydirectinput.keyDown('w')
                remaining = int(state.tease_chase_end - current_time)
                status(f"CHASING TEASE → {remaining}s remaining")
                if current_time >= state.tease_chase_end:
                    state.tease_chase_end = 0
                time.sleep(0.01)
                continue

            if state.time_since_red() >= config.NO_RED_THRESHOLD:
                if state.lost_red_sprint_end == 0:
                    state.lost_red_sprint_end = current_time + config.LOST_RED_SPRINT_DURATION
                    status(f"NO RED FOR {config.NO_RED_THRESHOLD}s → {int(config.LOST_RED_SPRINT_DURATION)}s SEARCH SPRINT!")

                if current_time < state.lost_red_sprint_end:
                    pydirectinput.keyDown('w')
                    if int(current_time * 1000) % 3000 < 50:
                        press_key('d', 0.9)
                        status("SEARCH SPIN")
                    remaining = int(state.lost_red_sprint_end - current_time)
                    status(f"SEARCH SPRINT → {remaining}s + SCANNING")
                    time.sleep(0.01)
                    continue

            state.burst_end_time = 0
            press_key('d', 0.05)
            status(f"SCANNING → {int(state.time_since_red())}s without red")
            time.sleep(0.01)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        release_all_keys()

        print("\n\n[CPTerminator] Stopped by user.")
