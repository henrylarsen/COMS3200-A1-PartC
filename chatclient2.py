import os
import socket
import sys
import threading


class Client:
    def __init__(self, channel_port, username):
        self.channel_port = channel_port
        self.username = username
        self.host = socket.gethostname()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.terminate = False

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
                self.socket.send(message.encode())
            except:
                self.socket.close()
                break
        os._exit(0)

    def receive(self):
        while True:
            try:
                message = self.socket.recv(1024).decode()
                if message == '/quit':
                    self.socket.close()
                    os._exit(1)
                print(f'{message}\n')

            except:
                self.socket.close()
                os._exit(1)

            # except:
            #     self.socket.close()
            #     sys.exit()



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


client = Client(12351, "user0")
client.connect_channel()
# exit(1)

# while True:
#     message = input()
#     client.send(message)

# if message == 'quit':
#     client_skt.close()

# python3 chatclient.py 12351 user0
# python3 chatclient.py 12352 user1
