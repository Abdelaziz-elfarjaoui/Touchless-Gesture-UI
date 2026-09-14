import cv2
import mediapipe as mp
import serial
import time
import os
from collections import deque
from datetime import datetime


# =========================================================
# CONFIGURATION
# =========================================================

COM_PORT = "COM6"
BAUD_RATE = 9600

USERNAME = "Aziz"
PASSWORD = "1234"

MODEL_PATH = "hand_landmarker.task"

WINDOW_NAME = "Touchless Gesture UI"

WIDTH = 640
HEIGHT = 480

UI_X = 40
UI_Y = 25
UI_W = 560
UI_H = 395


# =========================================================
# COLORS
# =========================================================

WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
BLUE = (255, 0, 0)
YELLOW = (0, 255, 255)
BLACK = (0, 0, 0)


# =========================================================
# PAGES
# =========================================================

PAGE_LOGIN = "LOGIN"
PAGE_MENU = "MENU"
PAGE_LED = "LED"
PAGE_MOTOR = "MOTOR"
PAGE_STATUS = "STATUS"

current_page = PAGE_LOGIN


# =========================================================
# LOGIN
# =========================================================

login_username = ""
login_password = ""

login_field = "USERNAME"


# =========================================================
# SYSTEM STATES
# =========================================================

red_state = False
blue_state = False
white_state = False

motor_speed = 0

last_sent_motor_speed = -1

# =========================================================
# PROFESSIONAL SAFETY / MONITORING
# =========================================================
HAND_LOST_TIMEOUT = 0.50
last_finger_time = 0
hand_detected = False
safety_stop_active = False
hand_confidence = 0.0
last_action = "System ready"

# =========================================================
# PROFESSIONAL MONITORING / EVENT LOG
# =========================================================
EVENT_LOG_FILE = "system.log"
MAX_EVENTS = 10
event_log = deque(maxlen=MAX_EVENTS)
last_fps = 0.0
fps_times = deque(maxlen=30)
last_reconnect_attempt = 0


# =========================================================
# SERIAL
# =========================================================

ser = None

try:

    ser = serial.Serial(
        COM_PORT,
        BAUD_RATE,
        timeout=0.01
    )

    time.sleep(2)

    print("Arduino connected on", COM_PORT)

except Exception as e:

    print("Serial connection error:", e)

    ser = None


# =========================================================
# EVENT LOGGING
# =========================================================

def log_event(message):

    global last_action

    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"{timestamp}  {message}"

    event_log.appendleft(entry)
    last_action = message

    try:
        with open(EVENT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass


def calculate_fps():

    global last_fps

    now = time.time()
    fps_times.append(now)

    if len(fps_times) >= 2:
        elapsed = fps_times[-1] - fps_times[0]
        if elapsed > 0:
            last_fps = (len(fps_times) - 1) / elapsed

    return last_fps


def try_reconnect():

    global ser
    global last_reconnect_attempt

    if ser is not None:
        return

    now = time.time()

    if now - last_reconnect_attempt < 3.0:
        return

    last_reconnect_attempt = now

    try:
        ser = serial.Serial(
            COM_PORT,
            BAUD_RATE,
            timeout=0.01
        )
        time.sleep(1)
        log_event(f"Arduino reconnected on {COM_PORT}")
        send_command("GET_STATE")
    except Exception:
        ser = None


# =========================================================
# SEND COMMAND
# =========================================================

def send_command(command):

    global ser

    if ser is None:

        print("SERIAL:", command)

        return

    try:

        ser.write(
            (command + "\n").encode()
        )

    except Exception as e:

        print("Serial write error:", e)
        ser = None


# =========================================================
# READ ARDUINO STATE
# =========================================================

def read_arduino_state():

    global red_state
    global blue_state
    global white_state
    global motor_speed

    if ser is None:

        return

    try:

        while ser.in_waiting > 0:

            line = ser.readline().decode(
                errors="ignore"
            ).strip()

            if not line:

                continue

            # WHITE
            if line.startswith("STATE:WHITE:"):

                white_state = (
                    line.split(":")[-1] == "ON"
                )

            # BLUE
            elif line.startswith("STATE:BLUE:"):

                blue_state = (
                    line.split(":")[-1] == "ON"
                )

            # RED
            elif line.startswith("STATE:RED:"):

                red_state = (
                    line.split(":")[-1] == "ON"
                )

            # SPEED
            elif line.startswith("STATE:SPEED:"):

                try:

                    motor_speed = max(
                        0,
                        min(
                            100,
                            int(
                                line.split(":")[-1]
                            )
                        )
                    )

                except ValueError:

                    pass

    except Exception as e:

        print("Serial read error:", e)


# =========================================================
# LED CONTROL
# =========================================================

def toggle_red():

    global red_state
    global last_action

    red_state = not red_state

    send_command(
        "RED:" + (
            "ON"
            if red_state
            else "OFF"
        )
    )
    log_event(f"RED LED -> {'ON' if red_state else 'OFF'}")


def toggle_blue():

    global blue_state
    global last_action

    blue_state = not blue_state

    send_command(
        "BLUE:" + (
            "ON"
            if blue_state
            else "OFF"
        )
    )
    log_event(f"BLUE LED -> {'ON' if blue_state else 'OFF'}")


def toggle_white():

    global white_state
    global last_action

    white_state = not white_state

    send_command(
        "WHITE:" + (
            "ON"
            if white_state
            else "OFF"
        )
    )
    log_event(f"WHITE LED -> {'ON' if white_state else 'OFF'}")


# =========================================================
# UI FRAME
# =========================================================

def draw_ui_frame(frame, title):

    cv2.rectangle(
        frame,
        (UI_X, UI_Y),
        (
            UI_X + UI_W,
            UI_Y + UI_H
        ),
        WHITE,
        2
    )

    cv2.putText(
        frame,
        title,
        (
            UI_X + 20,
            UI_Y + 37
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        WHITE,
        2,
        cv2.LINE_AA
    )


# =========================================================
# BUTTON
# =========================================================

def draw_button(
    frame,
    x1,
    y1,
    x2,
    y2,
    text,
    active=False
):

    color = GREEN if active else WHITE

    thickness = 3 if active else 2

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        color,
        thickness
    )

    font_scale = 0.65

    text_size = cv2.getTextSize(
        text,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        2
    )[0]

    tx = int(
        (x1 + x2 - text_size[0])
        / 2
    )

    ty = int(
        (y1 + y2 + text_size[1])
        / 2
    )

    cv2.putText(
        frame,
        text,
        (tx, ty),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        color,
        2,
        cv2.LINE_AA
    )


# =========================================================
# LOGIN KEYBOARD
# =========================================================

LETTER_ROWS = [
    "abcdefghij",
    "klmnopqrst",
    "uvwxyz"
]

NUMBER_ROWS = [
    "12345",
    "67890"
]

KEY_W = 42
KEY_H = 38
KEY_GAP = 7


# =========================================================
# GET LOGIN ITEM
# =========================================================

def get_login_item(x, y):

    # USERNAME
    if 75 <= y <= 108:

        return "USERNAME"

    # PASSWORD
    if 112 <= y <= 145:

        return "PASSWORD"

    # =====================================================
    # LETTER KEYBOARD
    # =====================================================

    if login_field == "USERNAME":

        start_y = 165

        for row_index, row in enumerate(
            LETTER_ROWS
        ):

            row_y = (
                start_y
                + row_index
                * (KEY_H + KEY_GAP)
            )

            total_width = (
                len(row) * KEY_W
                + (len(row) - 1)
                * KEY_GAP
            )

            start_x = int(
                (WIDTH - total_width)
                / 2
            )

            for i, char in enumerate(row):

                x1 = (
                    start_x
                    + i
                    * (KEY_W + KEY_GAP)
                )

                x2 = x1 + KEY_W

                if (
                    x1 <= x <= x2
                    and
                    row_y <= y
                    <= row_y + KEY_H
                ):

                    return char

    # =====================================================
    # NUMBER KEYBOARD
    # =====================================================

    else:

        start_y = 165

        for row_index, row in enumerate(
            NUMBER_ROWS
        ):

            row_y = (
                start_y
                + row_index
                * (KEY_H + KEY_GAP)
            )

            total_width = (
                len(row) * KEY_W
                + (len(row) - 1)
                * KEY_GAP
            )

            start_x = int(
                (WIDTH - total_width)
                / 2
            )

            for i, char in enumerate(row):

                x1 = (
                    start_x
                    + i
                    * (KEY_W + KEY_GAP)
                )

                x2 = x1 + KEY_W

                if (
                    x1 <= x <= x2
                    and
                    row_y <= y
                    <= row_y + KEY_H
                ):

                    return char

    # DELETE
    if (
        75 <= x <= 295
        and
        330 <= y <= 375
    ):

        return "DELETE"

    # ENTER
    if (
        345 <= x <= 565
        and
        330 <= y <= 375
    ):

        return "ENTER"

    return None


# =========================================================
# GET MENU ITEM
# =========================================================

def get_menu_item(x, y):

    # LED
    if 105 <= y <= 150:

        return "LED"

    # MOTOR
    if 165 <= y <= 210:

        return "MOTOR"

    # STATUS
    if 225 <= y <= 270:

        return "STATUS"

    # QUIT
    if 285 <= y <= 330:

        return "QUIT"

    return None


# =========================================================
# GET LED ITEM
# =========================================================

def get_led_item(x, y):

    # RED
    if (
        70 <= x <= 570
        and
        100 <= y <= 145
    ):

        return "RED"

    # BLUE
    if (
        70 <= x <= 570
        and
        165 <= y <= 210
    ):

        return "BLUE"

    # WHITE
    if (
        70 <= x <= 570
        and
        230 <= y <= 275
    ):

        return "WHITE"

    # BACK
    if (
        40 <= x <= 600
        and
        315 <= y <= 360
    ):

        return "BACK"

    return None


# =========================================================
# GET MOTOR ITEM
# =========================================================

def get_motor_item(x, y):

    if (
        100 <= x <= 540
        and
        145 <= y <= 215
    ):

        return "SPEED"

    if (
        40 <= x <= 600
        and
        315 <= y <= 360
    ):

        return "BACK"

    return None


# =========================================================
# GET STATUS ITEM
# =========================================================

def get_status_item(x, y):

    if (
        40 <= x <= 600
        and
        315 <= y <= 360
    ):

        return "BACK"

    return None


# =========================================================
# DRAW LOGIN
# =========================================================

def draw_login(
    frame,
    fingertip=None
):

    draw_ui_frame(
        frame,
        "TOUCHLESS LOGIN"
    )

    # =====================================================
    # USERNAME
    # =====================================================

    username_color = (
        GREEN
        if login_field == "USERNAME"
        else WHITE
    )

    cv2.rectangle(
        frame,
        (75, 75),
        (565, 108),
        username_color,
        2
    )

    cv2.putText(
        frame,
        "USERNAME",
        (85, 97),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        WHITE,
        1,
        cv2.LINE_AA
    )

    cv2.putText(
        frame,
        login_username,
        (220, 97),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        GREEN,
        2,
        cv2.LINE_AA
    )

    # =====================================================
    # PASSWORD
    # =====================================================

    password_color = (
        GREEN
        if login_field == "PASSWORD"
        else WHITE
    )

    cv2.rectangle(
        frame,
        (75, 112),
        (565, 145),
        password_color,
        2
    )

    cv2.putText(
        frame,
        "PASSWORD",
        (85, 134),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        WHITE,
        1,
        cv2.LINE_AA
    )

    stars = "*" * len(login_password)

    cv2.putText(
        frame,
        stars,
        (220, 134),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        GREEN,
        2,
        cv2.LINE_AA
    )

    # =====================================================
    # KEYBOARD
    # =====================================================

    rows = (
        LETTER_ROWS
        if login_field == "USERNAME"
        else NUMBER_ROWS
    )

    start_y = 165

    for row_index, row in enumerate(rows):

        row_y = (
            start_y
            + row_index
            * (KEY_H + KEY_GAP)
        )

        total_width = (
            len(row) * KEY_W
            + (len(row) - 1)
            * KEY_GAP
        )

        start_x = int(
            (WIDTH - total_width)
            / 2
        )

        for i, char in enumerate(row):

            x1 = (
                start_x
                + i
                * (KEY_W + KEY_GAP)
            )

            y1 = row_y

            x2 = x1 + KEY_W

            y2 = y1 + KEY_H

            active = (
                fingertip is not None
                and
                x1 <= fingertip[0] <= x2
                and
                y1 <= fingertip[1] <= y2
            )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                GREEN if active else WHITE,
                2
            )

            display_char = (
                char.upper()
                if login_field == "USERNAME"
                else char
            )

            cv2.putText(
                frame,
                display_char,
                (x1 + 13, y1 + 26),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                GREEN if active else WHITE,
                2,
                cv2.LINE_AA
            )

    # =====================================================
    # DELETE
    # =====================================================

    delete_active = (
        fingertip is not None
        and
        75 <= fingertip[0] <= 295
        and
        330 <= fingertip[1] <= 375
    )

    draw_button(
        frame,
        75,
        330,
        295,
        375,
        "DELETE",
        delete_active
    )

    # =====================================================
    # ENTER
    # =====================================================

    enter_active = (
        fingertip is not None
        and
        345 <= fingertip[0] <= 565
        and
        330 <= fingertip[1] <= 375
    )

    draw_button(
        frame,
        345,
        330,
        565,
        375,
        "ENTER",
        enter_active
    )


# =========================================================
# DRAW MENU
# =========================================================

def draw_menu(
    frame,
    fingertip=None
):

    draw_ui_frame(
        frame,
        "MAIN MENU"
    )

    items = [
        (
            "LED MANAGEMENT",
            105,
            150
        ),
        (
            "MOTOR SPEED MANAGEMENT",
            165,
            210
        ),
        (
            "SYSTEM STATUS",
            225,
            270
        ),
        (
            "QUIT",
            285,
            330
        )
    ]

    # System status line
    cv2.putText(frame, "● ONLINE" if ser is not None else "● OFFLINE",
                (455, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                GREEN if ser is not None else RED, 1, cv2.LINE_AA)

    for text, y1, y2 in items:

        active = (
            fingertip is not None
            and
            40 <= fingertip[0] <= 600
            and
            y1 <= fingertip[1] <= y2
        )

        draw_button(
            frame,
            40,
            y1,
            600,
            y2,
            text,
            active
        )


# =========================================================
# DRAW LED
# =========================================================

def draw_led(
    frame,
    fingertip=None
):

    draw_ui_frame(
        frame,
        "LED MANAGEMENT"
    )

    # =====================================================
    # RED
    # OFF = RED
    # ON  = GREEN
    # =====================================================

    red_color = (
        GREEN
        if red_state
        else RED
    )

    cv2.rectangle(
        frame,
        (70, 100),
        (570, 145),
        red_color,
        3
    )

    cv2.putText(
        frame,
        "RED",
        (295, 130),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        red_color,
        2,
        cv2.LINE_AA
    )

    # =====================================================
    # BLUE
    # OFF = RED
    # ON  = GREEN
    # =====================================================

    blue_color = (
        GREEN
        if blue_state
        else RED
    )

    cv2.rectangle(
        frame,
        (70, 165),
        (570, 210),
        blue_color,
        3
    )

    cv2.putText(
        frame,
        "BLUE",
        (290, 195),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        blue_color,
        2,
        cv2.LINE_AA
    )

    # =====================================================
    # WHITE
    # OFF = RED
    # ON  = GREEN
    # =====================================================

    white_color = (
        GREEN
        if white_state
        else RED
    )

    cv2.rectangle(
        frame,
        (70, 230),
        (570, 275),
        white_color,
        3
    )

    cv2.putText(
        frame,
        "WHITE",
        (280, 260),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        white_color,
        2,
        cv2.LINE_AA
    )

    # =====================================================
    # BACK
    # =====================================================

    back_active = (
        fingertip is not None
        and
        40 <= fingertip[0] <= 600
        and
        315 <= fingertip[1] <= 360
    )

    draw_button(
        frame,
        40,
        315,
        600,
        360,
        "BACK",
        back_active
    )


# =========================================================
# DRAW MOTOR
# =========================================================

def draw_motor(
    frame,
    fingertip=None
):

    draw_ui_frame(
        frame,
        "MOTOR SPEED MANAGEMENT"
    )

    # =====================================================
    # SPEED
    # =====================================================

    cv2.putText(
        frame,
        f"{motor_speed} km/h",
        (250, 115),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        WHITE,
        2,
        cv2.LINE_AA
    )

    # =====================================================
    # HORIZONTAL SPEED BAR
    # =====================================================

    x1 = 100
    x2 = 540
    y = 180

    cv2.rectangle(
        frame,
        (x1, y - 10),
        (x2, y + 10),
        WHITE,
        2
    )

    fill_x = int(
        x1
        + (x2 - x1)
        * motor_speed
        / 100
    )

    if fill_x > x1:

        cv2.rectangle(
            frame,
            (x1, y - 7),
            (fill_x, y + 7),
            GREEN,
            -1
        )

    cv2.circle(
        frame,
        (fill_x, y),
        9,
        GREEN,
        -1
    )

    # =====================================================
    # BACK
    # =====================================================

    back_active = (
        fingertip is not None
        and
        40 <= fingertip[0] <= 600
        and
        315 <= fingertip[1] <= 360
    )

    draw_button(
        frame,
        40,
        315,
        600,
        360,
        "BACK",
        back_active
    )


# =========================================================
# DRAW STATUS
# =========================================================

def draw_status(
    frame,
    fingertip=None
):

    draw_ui_frame(
        frame,
        "SYSTEM STATUS / MONITORING"
    )

    # Top monitoring indicators
    arduino_status = "CONNECTED" if ser is not None else "DISCONNECTED"
    hand_status = "DETECTED" if hand_detected else "SEARCHING"

    cv2.putText(frame, f"ARDUINO : {arduino_status}", (70, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48,
                GREEN if ser is not None else RED, 1, cv2.LINE_AA)
    cv2.putText(frame, f"HAND    : {hand_status}", (70, 97),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48,
                GREEN if hand_detected else YELLOW, 1, cv2.LINE_AA)
    cv2.putText(frame, f"CONF.   : {hand_confidence * 100:.0f}%", (300, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, WHITE, 1, cv2.LINE_AA)
    cv2.putText(frame, f"FPS     : {last_fps:.1f}", (300, 97),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, WHITE, 1, cv2.LINE_AA)

    # Hardware states
    states = [
        ("RED", red_state, 125),
        ("BLUE", blue_state, 150),
        ("WHITE", white_state, 175),
    ]

    for name, state, y in states:
        cv2.putText(frame, f"{name:<6}:", (70, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, WHITE, 1, cv2.LINE_AA)
        cv2.putText(frame, "ON" if state else "OFF", (160, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58,
                    GREEN if state else RED, 1, cv2.LINE_AA)

    cv2.putText(frame, f"MOTOR  : {motor_speed:3d} km/h", (70, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 0.58, GREEN, 1, cv2.LINE_AA)

    # Last action
    cv2.putText(frame, "LAST ACTION", (70, 230),
                cv2.FONT_HERSHEY_SIMPLEX, 0.50, YELLOW, 1, cv2.LINE_AA)
    cv2.putText(frame, last_action[:55], (70, 250),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, WHITE, 1, cv2.LINE_AA)

    # Event log panel
    cv2.rectangle(frame, (310, 115), (600, 300), WHITE, 1)
    cv2.putText(frame, "EVENT LOG", (325, 137),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, YELLOW, 1, cv2.LINE_AA)

    y = 158
    for entry in list(event_log)[:6]:
        cv2.putText(frame, entry[-40:], (320, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, WHITE, 1, cv2.LINE_AA)
        y += 22

    # BACK
    back_active = (
        fingertip is not None
        and 40 <= fingertip[0] <= 600
        and 315 <= fingertip[1] <= 360
    )

    draw_button(
        frame,
        40,
        315,
        600,
        360,
        "BACK",
        back_active
    )


# =========================================================
# UPDATE MOTOR
# =========================================================

def update_motor(x):

    global motor_speed
    global last_sent_motor_speed
    global last_action

    x = max(
        100,
        min(540, x)
    )

    new_speed = int(
        (x - 100)
        * 100
        / 440
    )

    new_speed = max(
        0,
        min(100, new_speed)
    )

    motor_speed = new_speed

    # Send every real speed change for smooth control
    if new_speed != last_sent_motor_speed:

        last_sent_motor_speed = new_speed

        send_command(
            f"SPEED:{new_speed}"
        )
        log_event(f"Motor speed -> {new_speed}%")


# =========================================================
# PROCESS LOGIN ITEM
# =========================================================

def process_login_item(item):

    global login_username
    global login_password
    global login_field
    global current_page

    if item is None:

        return

    # USERNAME
    if item == "USERNAME":

        login_field = "USERNAME"

        return

    # PASSWORD
    if item == "PASSWORD":

        login_field = "PASSWORD"

        return

    # DELETE
    if item == "DELETE":

        if login_field == "USERNAME":

            login_username = (
                login_username[:-1]
            )

            send_command(
                "LOGIN_USER:"
                + login_username
            )

        else:

            login_password = (
                login_password[:-1]
            )

            send_command(
                "LOGIN_PASS:"
                + login_password
            )

        return

    # ENTER
    if item == "ENTER":

        if (
            login_username.lower()
            == USERNAME.lower()
            and
            login_password
            == PASSWORD
        ):

            print("LOGIN SUCCESS")

            send_command(
                "LOGIN_OK"
            )

            log_event("LOGIN SUCCESS")

            current_page = PAGE_MENU

        else:

            print("LOGIN FAILED")

        return

    # CHARACTER / NUMBER
    if len(item) == 1:

        if login_field == "USERNAME":

            login_username += item

            send_command(
                "LOGIN_USER:"
                + login_username
            )

        else:

            login_password += item

            send_command(
                "LOGIN_PASS:"
                + login_password
            )


# =========================================================
# PROCESS MENU ITEM
# =========================================================

def process_menu_item(item):

    global current_page
    global login_username
    global login_password
    global login_field

    global hovered_item
    global item_consumed
    global hover_start_time

    if item == "LED":

        current_page = PAGE_LED

        send_command(
            "LED_PAGE"
        )
        log_event("Opened LED Management")

    elif item == "MOTOR":

        current_page = PAGE_MOTOR

        send_command(
            "MOTOR_PAGE"
        )
        log_event("Opened Motor Speed")

    elif item == "STATUS":

        current_page = PAGE_STATUS

        send_command(
            "STATUS_PAGE"
        )
        log_event("Opened System Status")

    # =====================================================
    # QUIT
    # =====================================================

    elif item == "QUIT":

        print("QUIT -> RETURN TO LOGIN")

        # -----------------------------------------------
        # Clear username/password
        # -----------------------------------------------

        login_username = ""

        login_password = ""

        # -----------------------------------------------
        # Start again from USERNAME
        # -----------------------------------------------

        login_field = "USERNAME"

        # -----------------------------------------------
        # Return to login
        # -----------------------------------------------

        current_page = PAGE_LOGIN

        # -----------------------------------------------
        # Reset hover system
        # -----------------------------------------------

        hovered_item = None

        item_consumed = False

        hover_start_time = 0

        # -----------------------------------------------
        # Tell Arduino
        # -----------------------------------------------

        send_command(
            "LOGIN_PAGE"
        )
        log_event("Logout / Return to Login")


# =========================================================
# PROCESS LED ITEM
# =========================================================

def process_led_item(item):

    global current_page

    if item == "RED":

        toggle_red()

    elif item == "BLUE":

        toggle_blue()

    elif item == "WHITE":

        toggle_white()

    elif item == "BACK":

        current_page = PAGE_MENU

        send_command(
            "BACK"
        )


# =========================================================
# PROCESS MOTOR ITEM
# =========================================================

def process_motor_item(item):

    global current_page

    if item == "BACK":

        current_page = PAGE_MENU

        send_command(
            "BACK"
        )


# =========================================================
# PROCESS STATUS ITEM
# =========================================================

def process_status_item(item):

    global current_page

    if item == "BACK":

        current_page = PAGE_MENU

        send_command(
            "BACK"
        )


# =========================================================
# MEDIAPIPE TASKS
# =========================================================

BaseOptions = mp.tasks.BaseOptions

HandLandmarker = (
    mp.tasks.vision.HandLandmarker
)

HandLandmarkerOptions = (
    mp.tasks.vision.HandLandmarkerOptions
)

VisionRunningMode = (
    mp.tasks.vision.RunningMode
)


options = HandLandmarkerOptions(

    base_options=BaseOptions(
        model_asset_path=MODEL_PATH
    ),

    running_mode=VisionRunningMode.VIDEO,

    num_hands=1,

    min_hand_detection_confidence=0.30,

    min_hand_presence_confidence=0.30,

    min_tracking_confidence=0.30
)


# =========================================================
# CAMERA
# =========================================================

cap = cv2.VideoCapture(0)

cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    WIDTH
)

cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    HEIGHT
)


# =========================================================
# FINGER SMOOTHING
# =========================================================

smooth_x = None
smooth_y = None

SMOOTHING = 0.5

last_finger_time = 0


# =========================================================
# HOVER CONTROL
# =========================================================

hovered_item = None

hover_start_time = 0

item_consumed = False


# =========================================================
# LOGIN KEYBOARD CONTROL
# =========================================================

keyboard_hovered = None

keyboard_hover_start = 0

keyboard_consumed = False


# =========================================================
# TIMING
# =========================================================

# Menu / Status / Motor BACK
NORMAL_HOVER_TIME = 0.30

# LED click
LED_HOVER_TIME = 0.30

# Login keys
KEY_HOVER_TIME = 0.5


# =========================================================
# MAIN LOOP
# =========================================================

with HandLandmarker.create_from_options(
    options
) as landmarker:

    timestamp_ms = 0

    log_event("System started")

    while True:

        # =================================================
        # READ ARDUINO / AUTO RECONNECT
        # =================================================

        try_reconnect()
        read_arduino_state()

        calculate_fps()

        # =================================================
        # CAMERA
        # =================================================

        ret, frame = cap.read()

        if not ret:

            print("Camera error")

            break

        # Mirror camera
        frame = cv2.flip(
            frame,
            1
        )

        frame = cv2.resize(
            frame,
            (WIDTH, HEIGHT)
        )

        # =================================================
        # RGB
        # =================================================

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        timestamp_ms += 33

        result = (
            landmarker.detect_for_video(
                mp_image,
                timestamp_ms
            )
        )

        fingertip = None

        # =================================================
        # INDEX FINGER TIP = LANDMARK 8
        # =================================================

        if result.hand_landmarks:

            hand = result.hand_landmarks[0]

            if result.handedness and result.handedness[0]:
                hand_confidence = float(result.handedness[0][0].score)
            else:
                hand_confidence = 1.0

            tip = hand[8]

            raw_x = int(
                tip.x * WIDTH
            )

            raw_y = int(
                tip.y * HEIGHT
            )

            raw_x = max(
                0,
                min(
                    WIDTH - 1,
                    raw_x
                )
            )

            raw_y = max(
                0,
                min(
                    HEIGHT - 1,
                    raw_y
                )
            )

            # =================================================
            # SMOOTH
            # =================================================

            if smooth_x is None:

                smooth_x = raw_x

                smooth_y = raw_y

            else:

                smooth_x = (
                    SMOOTHING
                    * raw_x
                    +
                    (1 - SMOOTHING)
                    * smooth_x
                )

                smooth_y = (
                    SMOOTHING
                    * raw_y
                    +
                    (1 - SMOOTHING)
                    * smooth_y
                )

            fingertip = (
                int(smooth_x),
                int(smooth_y)
            )

            hand_detected = True

            last_finger_time = (
                time.time()
            )

            # Finger cursor
            cv2.circle(
                frame,
                fingertip,
                10,
                GREEN,
                -1
            )

        else:

            hand_detected = False
            hand_confidence = 0.0

            # Keep last position briefly
            if (
                time.time()
                - last_finger_time
                < 0.20
                and
                smooth_x is not None
            ):

                fingertip = (
                    int(smooth_x),
                    int(smooth_y)
                )

        # =================================================
        # SAFETY: STOP MOTOR IF HAND IS LOST
        # =================================================
        if hand_detected:
            safety_stop_active = False

        if (
            current_page == PAGE_MOTOR
            and
            not hand_detected
            and
            motor_speed > 0
            and
            not safety_stop_active
            and
            time.time() - last_finger_time >= HAND_LOST_TIMEOUT
        ):

            motor_speed = 0
            last_sent_motor_speed = 0
            send_command("SPEED:0")
            safety_stop_active = True
            log_event("SAFETY STOP - hand lost")

        # =================================================
        # LOGIN
        # =================================================

        if current_page == PAGE_LOGIN:

            draw_login(
                frame,
                fingertip
            )

            item = None

            if fingertip is not None:

                item = get_login_item(
                    fingertip[0],
                    fingertip[1]
                )

            # Finger outside
            if item is None:

                keyboard_hovered = None

                keyboard_consumed = False

                keyboard_hover_start = 0

            else:

                # =================================================
                # USERNAME / PASSWORD / ENTER
                # INSTANT
                # =================================================

                if item in (
                    "USERNAME",
                    "PASSWORD",
                    "ENTER"
                ):

                    if (
                        keyboard_hovered
                        != item
                    ):

                        keyboard_hovered = item

                        keyboard_consumed = False

                        keyboard_hover_start = (
                            time.time()
                        )

                    if not keyboard_consumed:

                        process_login_item(
                            item
                        )

                        keyboard_consumed = True

                # =================================================
                # KEY / DELETE
                # 0.5 SECOND
                # =================================================

                else:

                    if (
                        keyboard_hovered
                        != item
                    ):

                        keyboard_hovered = item

                        keyboard_hover_start = (
                            time.time()
                        )

                        keyboard_consumed = False

                    else:

                        if (
                            not keyboard_consumed
                            and
                            time.time()
                            - keyboard_hover_start
                            >= KEY_HOVER_TIME
                        ):

                            process_login_item(
                                item
                            )

                            keyboard_consumed = True

        # =================================================
        # MAIN MENU
        # =================================================

        elif current_page == PAGE_MENU:

            draw_menu(
                frame,
                fingertip
            )

            item = None

            if fingertip is not None:

                item = get_menu_item(
                    fingertip[0],
                    fingertip[1]
                )

            # Outside
            if item is None:

                hovered_item = None

                item_consumed = False

                hover_start_time = 0

            else:

                # New item
                if (
                    hovered_item
                    != item
                ):

                    hovered_item = item

                    hover_start_time = (
                        time.time()
                    )

                    item_consumed = False

                # Same item
                else:

                    if (
                        not item_consumed
                        and
                        time.time()
                        - hover_start_time
                        >= NORMAL_HOVER_TIME
                    ):

                        process_menu_item(
                            item
                        )

                        item_consumed = True

        # =================================================
        # LED MANAGEMENT
        # =================================================

        elif current_page == PAGE_LED:

            draw_led(
                frame,
                fingertip
            )

            item = None

            if fingertip is not None:

                item = get_led_item(
                    fingertip[0],
                    fingertip[1]
                )

            # Finger outside all buttons
            if item is None:

                hovered_item = None

                item_consumed = False

                hover_start_time = 0

            else:

                # New item
                if (
                    hovered_item
                    != item
                ):

                    hovered_item = item

                    hover_start_time = (
                        time.time()
                    )

                    item_consumed = False

                # Same item
                else:

                    if (
                        not item_consumed
                        and
                        time.time()
                        - hover_start_time
                        >= LED_HOVER_TIME
                    ):

                        process_led_item(
                            item
                        )

                        # Prevent repeat
                        # until finger leaves
                        item_consumed = True

        # =================================================
        # MOTOR
        # =================================================

        elif current_page == PAGE_MOTOR:

            draw_motor(
                frame,
                fingertip
            )

            # =================================================
            # SPEED SLIDER
            # =================================================

            if fingertip is not None:

                x = fingertip[0]

                y = fingertip[1]

                if (
                    100 <= x <= 540
                    and
                    145 <= y <= 215
                ):

                    update_motor(x)

            # =================================================
            # BACK
            # =================================================

            item = None

            if fingertip is not None:

                item = get_motor_item(
                    fingertip[0],
                    fingertip[1]
                )

            if item == "BACK":

                if (
                    hovered_item
                    != item
                ):

                    hovered_item = item

                    hover_start_time = (
                        time.time()
                    )

                    item_consumed = False

                else:

                    if (
                        not item_consumed
                        and
                        time.time()
                        - hover_start_time
                        >= NORMAL_HOVER_TIME
                    ):

                        process_motor_item(
                            item
                        )

                        item_consumed = True

            elif not (
                fingertip is not None
                and
                100 <= fingertip[0] <= 540
                and
                145 <= fingertip[1] <= 215
            ):

                hovered_item = None

                item_consumed = False

        # =================================================
        # STATUS
        # =================================================

        elif current_page == PAGE_STATUS:

            draw_status(
                frame,
                fingertip
            )

            item = None

            if fingertip is not None:

                item = get_status_item(
                    fingertip[0],
                    fingertip[1]
                )

            if item is None:

                hovered_item = None

                item_consumed = False

                hover_start_time = 0

            else:

                if (
                    hovered_item
                    != item
                ):

                    hovered_item = item

                    hover_start_time = (
                        time.time()
                    )

                    item_consumed = False

                else:

                    if (
                        not item_consumed
                        and
                        time.time()
                        - hover_start_time
                        >= NORMAL_HOVER_TIME
                    ):

                        process_status_item(
                            item
                        )

                        item_consumed = True

        # =================================================
        # SHOW
        # =================================================

        cv2.imshow(
            WINDOW_NAME,
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        # =================================================
        # ESC
        # =================================================

        if key == 27:

            break

        # =================================================
        # PHYSICAL KEYBOARD
        # =================================================

        elif current_page == PAGE_LOGIN:

            # TAB
            if key == 9:

                if login_field == "USERNAME":

                    login_field = "PASSWORD"

                else:

                    login_field = "USERNAME"

                # Reset keyboard hover
                keyboard_hovered = None
                keyboard_consumed = False

            # BACKSPACE
            elif key == 8:

                process_login_item(
                    "DELETE"
                )

            # ENTER
            elif key == 13:

                process_login_item(
                    "ENTER"
                )

            # USERNAME letters
            elif (
                login_field == "USERNAME"
                and
                97 <= key <= 122
            ):

                process_login_item(
                    chr(key)
                )

            # PASSWORD numbers
            elif (
                login_field == "PASSWORD"
                and
                48 <= key <= 57
            ):

                process_login_item(
                    chr(key)
                )


# =========================================================
# CLEANUP
# =========================================================

cap.release()

cv2.destroyAllWindows()

if ser is not None:

    try:

        ser.close()

    except:

        pass