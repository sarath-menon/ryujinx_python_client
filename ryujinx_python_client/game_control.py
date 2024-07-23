import pyautogui
import time
import requests
import websocket
import threading
import time
import io
from PIL import Image
import cv2
import numpy as np
import json
import queue
import atexit

class GameController:
    def __init__(self):
        self.game_url = "http://localhost:8086"

        self.score = 0
        self.level = 1
        self.is_game_over = False
        self.is_running = True
        self.screen_width, self.screen_height = pyautogui.size()

        self.frame_count = 0
        self.start_time = time.time()
        self.image_queue = queue.LifoQueue(maxsize=100)

        # Example variables - replace these with actual values
        self.image_data = b'...'  # This should be your _imageByte data
        # self.width = 1920  # for captain toad
        # self.height = 1080  

        self.width = 1600  # for Mario
        self.height = 900

        # for receiving images (observations)
        self.obs_ws = websocket.WebSocket()
        # for sending actions (keypresses)
        self.action_ws = websocket.WebSocket()

        # Register the cleanup function
        atexit.register(self.close_websockets)

    def connect_websockets(self):
        try:    
            if not self.obs_ws.connected:
                self.obs_ws.connect("ws://localhost:8086/stream_websocket")
            if not self.action_ws.connected:
                self.action_ws.connect("ws://localhost:8086/keypress_websocket")

            self.obs_ws.settimeout(2)# Set websocket timeout to 2 seconds 
            self.action_ws.settimeout(2)# Set websocket timeout to 2 seconds 
        except websocket.WebSocketException as e:
            print(f"Failed to connect to websockets: {e}")
            return

    def close_websockets(self):
        try:
            if self.obs_ws: self.obs_ws.close()
            if self.action_ws: self.action_ws.close()
        except websocket.WebSocketException as e:
            print(f"Failed to close websockets: {e}")

    def keypress(self, key, duration):
        msg = { "action": "keypress",
                "key": key,
                "duration": duration
                }
        try:
            self.action_ws.send(json.dumps(msg))
            print(f"Sent message: {msg}")
        except websocket.WebSocketException as e:
            print(f"Failed to send message: {e}")

    def move_player(self, direction, duration=3000):
        key = None
        if direction == "forward":
            key = 'W'
        elif direction == "backward":
            key = 'S'
        elif direction == "left":
            key = 'A'
        elif direction == "right":
            key = 'D'
        else:
            print(f"Invalid direction: {direction}")
            return None

        self.keypress(key, duration)
       

    def get_screenshot(self):

        message = {"duration": 0, "fps": 0, "screenshot": "True"}
        self.obs_ws.send(json.dumps(message))

        try:
            message = self.obs_ws.recv()
        except websocket.WebSocketTimeoutException:
            print("Timeout occurred while waiting for a message")
            return
        
        image = Image.frombytes(mode='RGBA', size=(self.width, self.height), data=message)
        # Remove alpha channel from image
        image = image.convert("RGB")
        return image

    def click_center(self):
        pyautogui.moveTo(self.screen_width/2, self.screen_height/2)
        pyautogui.mouseDown()
        time.sleep(0.1)
        pyautogui.mouseUp()

    def go_to_game_window(self):
        self.click_center()

    def pause_game(self):
        try:
            response = requests.post(self.game_url + '/pause_game')
            response.raise_for_status()  
            return response.status_code
        except requests.RequestException as e:
            print(f"Error pausing game: {e}")

    def resume_game(self):
        try:
            response = requests.post(self.game_url + '/resume_game')
            response.raise_for_status()  
            return response.status_code
        except requests.RequestException as e:
            print(f"Error resuming game: {e}")

    def orbit_camera(self, direction, duration=300):
        key = None
        if direction == "up":
            key = 'Up'
        elif direction == "down":
            key = 'Down'
        elif direction == "left":
            key = 'Left'
        elif direction == "right":
            key = 'Right'
        else:
            print(f"Invalid direction: {direction}")
            return None
        self.keypress(key, duration)

    def special_action(self, action):
        key = None
        duration = 500

        if action == "jump":
            key = 'B'
        elif action == "throw_hat":
            key = 'Y'
        else:
            print(f"Invalid special action: {action}")
            return None

        self.keypress(key, duration)
        

    def camera_down(self):
        pyautogui.hotkey('fn', 'f7')

    def get_game_state(self):
        return {
            "score": self.score,
            "level": self.level,
            "is_game_over": self.is_game_over
        }
    
    def collect_treasure(self, direction):
        print(f"Collecting treasure in {direction}")
        
