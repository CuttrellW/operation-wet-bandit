import socket
import curses


def main(stdscr):
    # Initialize connection parameters
    arduino_ip = "192.168.50.30"  # Replace with your Arduino's IP address
    arduino_port = 80             # Replace with the correct port if different

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

    step_size = 5
    while True:
        key = stdscr.getch()
        if key == curses.KEY_UP:
            y_pos = min(y_max, y_pos + step_size)
            send_command(f"x={x_pos}&y={y_pos}")
            stdscr.addstr(2, 0, f"Sent command: UP (x={x_pos}, y={y_pos})  ")
        elif key == curses.KEY_DOWN:
            y_pos = max(y_min, y_pos - step_size)
            send_command(f"x={x_pos}&y={y_pos}")
            stdscr.addstr(2, 0, f"Sent command: DOWN (x={x_pos}, y={y_pos})")
        elif key == curses.KEY_LEFT:
            x_pos = min(x_max, x_pos + step_size)
            send_command(f"x={x_pos}&y={y_pos}")
            stdscr.addstr(2, 0, f"Sent command: LEFT (x={x_pos}, y={y_pos})")
        elif key == curses.KEY_RIGHT:
            x_pos = max(x_min, x_pos - step_size)
            send_command(f"x={x_pos}&y={y_pos}")
            stdscr.addstr(2, 0, f"Sent command: RIGHT (x={x_pos}, y={y_pos})")
        elif key == ord('q'):
            x_pos, y_pos = 225, 45
            send_command(f"x={x_pos}&y={y_pos}")
            stdscr.addstr(2, 0, f"Sent command: UP-LEFT (x={x_pos}, y={y_pos})")
        elif key == ord('e'):
            x_pos, y_pos = 45, 45
            send_command(f"x={x_pos}&y={y_pos}")
            stdscr.addstr(2, 0, f"Sent command: UP-RIGHT (x={x_pos}, y={y_pos})")
        elif key == ord('a'):
            x_pos, y_pos = 225, 0
            send_command(f"x={x_pos}&y={y_pos}")
            stdscr.addstr(2, 0, f"Sent command: DOWN-LEFT (x={x_pos}, y={y_pos})")
        elif key == ord('d'):
            x_pos, y_pos = 45, 0
            send_command(f"x={x_pos}&y={y_pos}")
            stdscr.addstr(2, 0, f"Sent command: DOWN-RIGHT (x={x_pos}, y={y_pos})")
        elif key == ord('s'):
            x_pos, y_pos = 135, 0
            send_command(f"x={x_pos}&y={y_pos}")
            stdscr.addstr(2, 0, f"Sent command: RESET (x={x_pos}, y={y_pos}) ")
        elif key == ord('q'):
            break

        stdscr.refresh()

    client_socket.close()


curses.wrapper(main)