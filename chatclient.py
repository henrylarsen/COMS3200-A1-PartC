import socket
import sys

class Client:
    def __init__(self, channel_port, username):
        self.channel_port = channel_port
        self.username = username
        self.host = socket.gethostname()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_channel(self):
        self.socket.connect((self.host, self.channel_port))
        self.socket.send(username.encode())
        # Receive and print welcome message
        welcome_message = self.socket.recv(1024).decode()
        print(welcome_message)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        exit(1)

    SERVER_PORT = int(sys.argv[1])
    username = sys.argv[2]

    client = Client(SERVER_PORT, username)
    client.connect_channel()

    # while True:
    #     message = input()
    #     client.send(message)

# if message == 'quit':
#     client_skt.close()

# python3 chatclient.py 12351 user0
# python3 chatclient.py 12352 user1
