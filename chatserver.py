import socket
import threading
import sys

SERVER_HOST = socket.gethostname()


def client_handler(conn, addr, chan_name):
    print(f'New client connection: {addr}')
    username = conn.recv(1024).decode()
    conn.send(f'[Server message (<time>)] welcome to the {chan_name} channel, {username}.'.encode())
    # while True


def initiate_chat_channel(channel_name, channel_port, channel_cap):
    # Create the server socket
    server_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to local host
    server_skt.bind((SERVER_HOST, channel_port))
    # Listen for incoming connections
    server_skt.listen()
    print('The server is listening for connections')
    clients = []

    while True:
        conn, addr = server_skt.accept()

        print(f'Accepted new connection from {addr}')
        client_thread = threading.Thread(target=client_handler, args=(conn, addr, channel_name))
        client_thread.start()


if len(sys.argv) != 2:
    exit(1)

config_file = sys.argv[1]

# Gets channel info from configfile, creates channels from it.
for line in open(config_file):
    if line.startswith('channel'):
        fields = line.strip().split()
        if len(fields) != 4:
            print(f'Incorrect formatting in config file.')

        channel_name = fields[1]
        channel_port = int(fields[2])
        channel_cap = int(fields[3])

        server = threading.Thread(target=initiate_chat_channel, args=(channel_name, channel_port, channel_cap))
        server.start()


# python3 chatserver.py configfile

