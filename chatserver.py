import socket
import threading
import sys
from datetime import datetime


class Server:
    def __init__(self, channels):
        self.channels = channels


    def start(self):
        # Create the server socket
        # server_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to local host
        # server_skt.bind((self.host, channel_port))

        for channel in self.channels:
            channel_thread = threading.Thread(target=channel.start())
            channel_thread.start()

        # Listen for incoming connections
        # server_skt.listen()
        print('The server is listening for connections')

        # while True:
        #     conn, addr = server_skt.accept()
        #
        #     print(f'Accepted new connection from {addr}')
        #     client_thread = threading.Thread(target=self.client_handler, args=(conn, addr, channel_name))
        #     client_thread.start()


    # def client_handler(self, conn, addr, channel_port):
    #     print(f'New client connection: {addr}')
    #     username = conn.recv(1024).decode()
    #     time = datetime.now().strftime("%H:%M:%S")
    #     conn.send(f'[Server message ({time})] welcome to the {chan_name} channel, {username}.'.encode())
    #     # while True


class Channel:
    def __init__(self, name, port, capacity):
        self.port = port
        self.name = name
        self.capacity = capacity
        self.clients = []
        self.queue = []
        self.host = socket.gethostname()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to local host
        self.socket.bind((self.host, self.port))
        self.socket.listen()

    def start(self):
        while True:
            conn, addr = self.socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            client_thread.start()

    def handle_client(self, conn, addr):
        print(f'New client connection: {addr}')
        username = conn.recv(1024).decode()
        time = datetime.now().strftime("%H:%M:%S")
        conn.send(f'[Server message ({time})] welcome to the {self.name} channel, {username}.'.encode())
        # while True


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


# python3 chatserver.py configfile

