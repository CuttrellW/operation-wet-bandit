import socket
import curses

arduino_ip = "192.168.50.30"
arduino_port = 80

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the Arduino
client_socket.connect((arduino_ip, arduino_port))

def send_command(command):
    client_socket.send(command.encode('utf-8'))


def main(stdscr):
    stdscr.nodelay(True)
    stdscr.timeout(100)

    while True:
        key = stdscr.getch()
        if key == curses.KEY_UP:
            send_command("w")
            print("Sent command: UP (0x01)")
        elif key == curses.KEY_DOWN:
            send_command("s")
            print("Sent command: DOWN (0x02)")
        elif key == curses.KEY_LEFT:
            send_command("a")
            print("Sent command: LEFT (0x03)")
        elif key == curses.KEY_RIGHT:
            send_command("d")
        elif key == ord('q'):
            break

    client_socket.close()

curses.wrapper(main)
