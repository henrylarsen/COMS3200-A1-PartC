import os
import socket
import sys
import threading
from datetime import datetime


class Client:
    def __init__(self, channel_port, username):
        self.channel_port = channel_port
        self.username = username
        self.host = socket.gethostname()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_channel(self):
        self.socket.connect((self.host, self.channel_port))
        self.socket.send(self.username.encode())
        # Receive and print welcome message
        welcome_message = self.socket.recv(1024).decode()
        print(welcome_message)
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()
        send_thread = threading.Thread(target=self.send)
        send_thread.start()

    def send(self):
        while True:
            try:
                message = input()
            except:
                self.socket.close()
                break
            # If sending a file
            if message.startswith('/send'):
                _, target, file_path = message.split(' ')
                try:
                    file_data = open(file_path, 'rb').read()
                    self.socket.send(f'/send {target} {file_path} {len(file_data)}'.encode())
                    self.socket.sendall(file_data)
                except:
                    print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})]: {file_path} does not exist.')

            else:
                self.socket.send(message.encode())

        os._exit(0)

    def receive(self):
        while True:
            try:
                message = self.socket.recv(1024).decode()
                if message.startswith('/send'):
                    _, sender, file_name, file_size = message.split()
                    file_size = int(file_size)
                    file_data = b''

                    while len(file_data) < file_size:
                        data = self.socket.recv(1024)
                        if not data:
                            break
                        file_data += data

                    file_name = file_name.split('\\')[-1].split('1')[0]
                    # print(os.path.splitext(sys.argv[0])[-1])
                    file_path = f'{os.getcwd()}\{file_name}'
                    open(file_path, 'wb').write(file_data)

                if message == '/quit':
                    self.socket.close()
                    os._exit(1)
                print(f'{message}')

            except:
                self.socket.close()
                os._exit(1)


# RUN FROM TERMINAL
"""
if __name__ == '__main__':
    if len(sys.argv) != 3:
        exit(1)

    SERVER_PORT = int(sys.argv[1])
    username = sys.argv[2]

    client = Client(SERVER_PORT, username)
    client.connect_channel()
"""


client = Client(12351, "user2")
client.connect_channel()
