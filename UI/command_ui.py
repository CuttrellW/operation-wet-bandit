import socket


class ArduinoController:
    def __init__(self, spoof=False, ip="192.168.50.30", port=80):
        self.spoof = spoof
        self.arduino_ip = ip
        self.arduino_port = port
        self.x_pos, self.x_min, self.x_max = 135, 0, 270
        self.y_pos, self.y_min, self.y_max = 0, 0, 75
        self.step_size = 10
        if spoof:
            print("Spoofing Arduino Controller")
        else:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        if self.spoof:
            return True
        else:
            try:
                self.client_socket.connect((self.arduino_ip, self.arduino_port))
                print(f"Connected to Arduino at {self.arduino_ip}:{self.arduino_port}")
            except Exception as e:
                print(f"Error connecting to Arduino: {e}")
                self.client_socket.close()
                return False
            return True

    def send_command(self, command):
        if self.spoof:
            print(f"Sent spoof command: {command}")
            return
        else:
            try:
                self.client_socket.sendall((command + "\n").encode("utf-8"))
            except Exception as e:
                zs

    def update_position(self, new_x, new_y, action_name, spoof=False):
        self.x_pos = max(self.x_min, min(self.x_max, new_x))
        self.y_pos = max(self.y_min, min(self.y_max, new_y))
        self.send_command(f"x={self.x_pos}&y={self.y_pos}")
        print(f"Sent command: {action_name} (x={self.x_pos}, y={self.y_pos})")

    def toggle_solenoid(self):
        self.send_command("solenoid=toggle")
        print("Sent command: TOGGLE SOLENOID")

    def handle_key(self, key):
        actions = {
            "UP": lambda: self.update_position(
                self.x_pos, self.y_pos + self.step_size, "UP"
            ),
            "DOWN": lambda: self.update_position(
                self.x_pos, self.y_pos - self.step_size, "DOWN"
            ),
            "LEFT": lambda: self.update_position(
                self.x_pos + self.step_size, self.y_pos, "LEFT"
            ),
            "RIGHT": lambda: self.update_position(
                self.x_pos - self.step_size, self.y_pos, "RIGHT"
            ),
            "q": lambda: self.update_position(225, 45, "UP-LEFT"),
            "e": lambda: self.update_position(45, 45, "UP-RIGHT"),
            "w": lambda: self.update_position(135, 45, "UP-CENTER"),
            "a": lambda: self.update_position(225, 0, "DOWN-LEFT"),
            "d": lambda: self.update_position(45, 0, "DOWN-RIGHT"),
            "s": lambda: self.update_position(135, 0, "DOWN-CENTER"),
            " ": self.toggle_solenoid,
        }

        action = actions.get(key)
        if action:
            action()
        else:
            print(f"Unmapped key pressed: {key}")
