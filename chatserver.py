import socket
import threading
import sys
from datetime import datetime


class Server:
    def __init__(self, channels):
        self.channels = channels
        print("Server Initiated")

    def start(self):
        for channel in self.channels:
            print(f'Check {channel.name}')
            channel_thread = threading.Thread(target=channel.start)
            channel_thread.start()
        print("Server started")


class Channel:
    def __init__(self, name, port, capacity):
        self.port = port
        self.name = name
        self.capacity = capacity
        self.clients = []
        self.queue = []
        self.host = socket.gethostname()

        # Create the server socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to local host
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        print(f'{self.name} channel initialized.')

    def start(self):
        print(f'{self.name} channel started.')
        while True:
            conn, addr = self.socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            client_thread.start()
            print("Started client thread.")

    def handle_client(self, conn, addr):
        print(f'New client connection: {addr}')
        uname = conn.recv(1024).decode()
        client = ServerClient(uname, conn, addr)
        self.add_client(client)

    def add_client(self, client):
        # Send welcome message
        client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] Welcome to the {self.name} channel,'
                  f' {client.username}.'.encode())

        # If there is matched username, cannot enter
        # TODO: add how this blocks from entering
        if self.matched_username(client.username):
            client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] Cannot enter the '
                                   f'{self.name} channel.'.encode())

        # Adds client to queue
        self.queue.append(client)
        client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] You are in the waiting'
                               f' queue and there are {self.queue.index(client)} user(s) ahead of you.\n'.encode())

        # If fewer clients in channel than capacity, add client
        if len(self.clients) < self.capacity:
            self.queue.pop(self.queue.index(client))
            self.clients.append(client)
            client.connection.send(
                f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has joined the '
                f'channel.'.encode())
            print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has joined the '
                  f'{self.name} channel.')
            self.receive(client)

    def matched_username(self, username):
        for client in self.queue + self.clients:
            if client.username == username:
                return True
        return False

    def receive(self, client):
        while True:
            message = client.connection.recv(1024).decode()
            # self.command_check(message)
            print(f'[{client.username} ({datetime.now().strftime("%H:%M:%S")})] {message}')
            self.broadcast(client, message)

    def command_check(self, message):
        command = message.split()[0]
        if command == "/whisper":
            self.whisper_command(message)
        elif command == "/quit":
            self.quit_command(message)
        elif command == "/list":
            self.list_command(message)
        elif command == "/switch":
            self.switch_command(message)
        elif command == "/send":
            self.send_command(message)



    def broadcast(self, sender, message):
        for client in self.clients:
            client.connection.send(f'[{sender.username} ({datetime.now().strftime("%H:%M:%S")})] {message}'.encode())


class ServerClient:
    def __init__(self, username, connection, address):
        self.username = username
        self.connection = connection
        self.address = address


# RUN FROM TERMINAL
"""
if __name__ == '__main__':
    # If no config file, exit
    if len(sys.argv) != 2:
        exit(1)

    config_file = sys.argv[1]

    channel_list = []

    # Gets channel info from configfile, creates channels from it.
    for line in open(config_file):
        if line.startswith('channel'):
            fields = line.strip().split()
            if len(fields) != 4:
                print(f'Incorrect formatting in config file.')

            channel_name = fields[1]
            channel_port = int(fields[2])
            channel_cap = int(fields[3])

            channel_list.append(Channel(channel_name, channel_port, channel_cap))

    server = Server(channel_list)
    server.start()
"""


# RUN FROM IN PYCHARM
channel_list = [Channel('first', 12351, 5), Channel('second', 12352, 5), Channel('third', 12353, 5)]
server = Server(channel_list)
server.start()

# python3 chatserver.py configfile    