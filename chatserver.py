import socket
import threading
import sys
from datetime import datetime
import time


class Server:
    def __init__(self, channels):
        self.channels = channels
        self.muted = {}

    def start(self):
        server_thread = threading.Thread(target=self.server_input)
        server_thread.start()
        for channel in self.channels:
            channel_thread = threading.Thread(target=channel.start)
            channel_thread.start()

    def server_input(self):
        while True:
            message = input()
            self.server_commands(message)

    def server_commands(self, message):
        if len(message) == 0:
            return
        command = message.split()[0]
        if command == "/kick":
            self.kick_command(message)
        elif command == "/mute":
            self.mute_command(message)
        elif command == "/empty":
            self.empty_command(message)
        elif command == "/shutdown":
            self.shutdown_command(message)

    def kick_command(self, message):
        user_kick = message.split()[1]
        for channel in channel_list:
            for user in channel.clients:
                if user_kick == user.username:
                    channel.clients.remove(user)
                    user.connection.send('/quit'.encode())
                    user.connection.close()
                    channel.broadcast(None,
                                      f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {user_kick} has left the channel')
                    channel.broadcast(None,
                                      f'[Server message ({datetime.now().strftime("%H:%M:%S")})] Kicked {user_kick}')
                    print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] Kicked {user_kick}')
                    return
        print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {user_kick} is not here.')

    def mute_command(self, message):
        mute_user = message.split()[1]
        mute_time = int(message.split()[2])
        for channel in channel_list:
            for user in channel.clients:
                if mute_user == user.username:
                    self.muted[mute_user] = time.time() + mute_time
                    print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] Muted {mute_user} for'
                          f' {mute_time} seconds.')
                    user.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] You have been'
                                         f' muted for {mute_time} seconds.'.encode())
                    for channels in channel_list:
                        channels.broadcast(None, f'[Server message ({datetime.now().strftime("%H:%M:%S")})] '
                                                 f'{mute_user} has been muted for {mute_time} seconds.')

                    return
        print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {mute_user} is not here.')

    def empty_command(self, message):
        empty_channel = message.split()[1]
        for channel in channel_list:
            if empty_channel == channel.name:
                for client in channel.queue:
                    channel.queue.remove(client)
                    client.connection.send('/quit'.encode())
                    client.connection.close()
                for client in channel.clients:
                    channel.clients.remove(client)
                    client.connection.send('/quit'.encode())
                    client.connection.close()
                print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {empty_channel} has been emptied.')
                return
        print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {empty_channel} does not exist.')

    def shutdown_command(self, message):
        for channel in channel_list:
            for client in channel.clients:
                client.connection.send('/quit'.encode())
                client.connection.close()
            channel.socket.close()
        exit(1)


def matched_username(channel, username):
    for client in channel.queue + channel.clients:
        if client.username == username:
            return True
    return False


def add_to_channel(channel, client):
    # Adds client to queue
    channel.queue.append(client)
    client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] You are in the waiting'
                           f' queue and there are {channel.queue.index(client)} user(s) ahead of you.\n'.encode())

    # If fewer clients in channel than capacity, add client
    if len(channel.clients) < channel.capacity:
        channel.queue.pop(channel.queue.index(client))
        channel.clients.append(client)
        client.connection.send(
            f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has joined the '
            f'channel.'.encode())
        print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has joined the '
              f'{channel.name} channel.')
        channel.receive(client)


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

    def start(self):
        while True:
            try:
                conn, addr = self.socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.start()
            except:
                exit(1)

    def handle_client(self, conn, addr):
        uname = conn.recv(1024).decode()
        client = ServerClient(uname, conn, addr)
        self.add_client(client)

    def add_client(self, client):
        # Send welcome message
        client.connection.send(
            f'[Server message ({datetime.now().strftime("%H:%M:%S")})] Welcome to the {self.name} channel,'
            f' {client.username}.'.encode())

        # If there is matched username, cannot enter
        # TODO: add how this blocks from entering
        if matched_username(self, client.username):
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

    def receive(self, client):
        while True:
            try:
                message = client.connection.recv(1024).decode()
                self.command_check(message, client)
            except:
                break

    # Check to see if any commands occur
    def command_check(self, message, client):
        if len(message) == 0:
            return
        command = message.split()[0]
        if command == "/whisper":
            self.whisper_command(message, client)
        elif command == "/quit":
            self.quit_command(message, client)
        elif command == "/list":
            self.list_command(message, client)
        elif command == "/switch":
            self.switch_command(message, client)
        elif command == "/send":
            self.send_command(message, client)
        else:
            print(f'[{client.username} ({datetime.now().strftime("%H:%M:%S")})] {message}')
            self.broadcast(client, message)

    # Broadcast message to all clients in channel
    def broadcast(self, sender, message):
        # If no sender, broadcast message alone
        if sender is None:
            for client in self.clients:
                client.connection.send(message.encode())
        # Check if sender muted, if time elapsed, remove from muted list
        elif sender.username in server.muted:
            if time.time() < server.muted[sender.username]:
                for client1 in self.clients:
                    if sender.username == client1.username:
                        client1.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] You are '
                                                f'still muted for {server.muted[sender.username] - time.time()} seconds.'
                                                .encode())
            else:
                del server.muted[sender.username]

        # Broadcast message with user
        else:
            for client in self.clients:
                client.connection.send(f'[{sender.username} ({datetime.now().strftime("%H:%M:%S")})] {message}'
                                       .encode())

    def whisper_command(self, message, client):
        send_user = message.split()[1]
        message_only = ' '.join(message.split()[2:])
        print(f'[{client.username} whispers to {send_user}: ({datetime.now().strftime("%H:%M:%S")})]: {message_only}')
        for user in self.clients:
            if user.username == send_user:
                user.connection.send(f'[{client.username} whispers to you: ({datetime.now().strftime("%H:%M:%S")})] '
                                     f'{message_only}'.encode())
                return
        client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {send_user} is not here.'
                               .encode())

    def quit_command(self, message, client):
        if client in self.clients:

            self.clients.remove(client)
            self.broadcast(None, f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has left'
                                 f' the channel.'.encode())
        else:
            self.queue.remove(client)

        client.connection.send(f'/quit'.encode())
        print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has left'
              f' the channel.')

    def list_command(self, message, client):
        for channel in channel_list:
            client.connection.send(f'[Channel] {channel.name} {len(channel.clients)}/{channel.capacity}/'
                                   f'{len(channel.queue)}.'.encode())

    def switch_command(self, message, client):
        destination_channel = message.split()[1]
        for channel in channel_list:
            # If the channel exists
            if channel.name == destination_channel:
                # If someone in destination_channel or queue with same username, don't switch
                if matched_username(channel, client.username):
                    client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")}) Cannot switch to '
                                           f'the {destination_channel} channel.'.encode())
                # Else, remove from queue or channel and add to destination_channel
                else:
                    if client in self.clients:
                        self.clients.remove(client)
                        # If queue not empty, add next in line to clients
                        if len(self.queue) != 0:
                            next_client = self.queue[0]
                            self.queue.pop(0)
                            self.clients.append(next_client)

                    else:
                        self.queue.remove(client)
                    self.broadcast(None,
                                   f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has '
                                   f'left the channel.'.encode())
                    print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has '
                          f'left the channel.')
                    add_to_channel(channel, client)
                return
        client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")}) {destination_channel} does '
                               f'not exist.'.encode())

    # TODO: implement send
    def send_command(self, message, client):
        print('/send Command')


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
