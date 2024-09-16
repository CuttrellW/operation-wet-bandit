import socket
import curses


def main(stdscr):
    # Initialize connection parameters
    arduino_ip = "192.168.50.30"
    arduino_port = 80

    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the Arduino
    try:
        client_socket.connect((arduino_ip, arduino_port))
        stdscr.addstr(0, 0, "Connected to Arduino at {}:{}".format(arduino_ip, arduino_port))
    except Exception as e:
        stdscr.addstr(0, 0, f"Error connecting to Arduino: {e}")
        stdscr.refresh()
        client_socket.close()
        return

    # Function to send commands to Arduino
    def send_command(command):
        try:
            # Add newline character as Arduino expects
            client_socket.sendall((command + '\n').encode('utf-8'))
        except Exception as e:
            stdscr.addstr(1, 0, f"Error sending command: {e}")
            stdscr.refresh()

    # Initialize curses window
    stdscr.nodelay(True)
    stdscr.timeout(100)

    x_pos, x_min, x_max = 135, 0, 270
    y_pos, y_min, y_max = 0, 0, 75

    step_size = 10

    # Function to update position and send command
    def update_position(new_x, new_y, action_name):
        nonlocal x_pos, y_pos
        x_pos = max(x_min, min(x_max, new_x))
        y_pos = max(y_min, min(y_max, new_y))
        send_command(f"x={x_pos}&y={y_pos}")
        stdscr.addstr(2, 0, f"Sent command: {action_name} (x={x_pos}, y={y_pos})   ")
        stdscr.clrtoeol()

    def toggle_solenoid():
        send_command("solenoid=toggle")
        stdscr.addstr(2, 0, "Sent command: TOGGLE SOLENOID       ")
        stdscr.clrtoeol()

    # Action dictionary mapping keys to functions
    actions = {
        curses.KEY_UP: lambda: update_position(x_pos, y_pos + step_size, "UP"),
        curses.KEY_DOWN: lambda: update_position(x_pos, y_pos - step_size, "DOWN"),
        curses.KEY_LEFT: lambda: update_position(x_pos + step_size, y_pos, "LEFT"),
        curses.KEY_RIGHT: lambda: update_position(x_pos - step_size, y_pos, "RIGHT"),
        ord('q'): lambda: update_position(225, 45, "UP-LEFT"),
        ord('e'): lambda: update_position(45, 45, "UP-RIGHT"),
        ord('w'): lambda: update_position(135, 45, "UP-CENTER"),
        ord('a'): lambda: update_position(225, 0, "DOWN-LEFT"),
        ord('d'): lambda: update_position(45, 0, "DOWN-RIGHT"),
        ord('s'): lambda: update_position(135, 0, "DOWN-CENTER"),
        ord(' '): toggle_solenoid,
        ord('x'): "EXIT",  # Special case for exiting the loop

    }

    # Main loop
    while True:
        key = stdscr.getch()
        if key != -1:
            action = actions.get(key)
            if action:
                if action == "EXIT":
                    break  # Exit the program
                else:
                    action()  # Execute the associated action
            else:
                stdscr.addstr(3, 0, f"Unmapped key pressed: {key}   ")
                stdscr.clrtoeol()

            stdscr.refresh()


curses.wrapper(main)