import os
import socket
import threading
from datetime import datetime
import time
import sys


class Server:
    def __init__(self, channels):
        self.channels = channels
        self.muted = {}
        self.TIMEOUT_VALUE = 100

    def start(self):
        server_thread = threading.Thread(target=self.server_input)
        server_thread.start()
        for channel in self.channels:
            channel_thread = threading.Thread(target=channel.start)
            channel_thread.start()

    def server_input(self):
        while True:
            try:
                message = input()
                self.server_commands(message)
            except EOFError:
                continue

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
        kick_channel = message.split()[1].split(':')[0]
        user_kick = message.split()[1].split(':')[1]

        for channel in channel_list:
            if kick_channel == channel.name:
                for user in channel.clients:
                    if user_kick == user.username:
                        channel.clients.remove(user)
                        user.connection.send('/quit'.encode())
                        user.connection.close()
                        channel.broadcast(None, f'[Server message ({datetime.now().strftime("%H:%M:%S")})] '
                                                f'{user_kick} has left the channel')
                        channel.broadcast(None,
                                          f'[Server message ({datetime.now().strftime("%H:%M:%S")})] Kicked {user_kick}.')
                        print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] Kicked {user_kick}.',
                              flush=True)
                        if len(channel.queue) != 0:
                            next_client = channel.queue[0]
                            channel.queue.pop(0)
                            channel.clients.append(next_client)

                        return
                    print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {user_kick} is not in '
                          f'{kick_channel}.', flush=True)
                    return
        print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {kick_channel} does not exist.', flush=True)

    def mute_command(self, message):
        mute_time = float(message.split()[2])
        if not (mute_time > 0 and mute_time % 1 == 0):
            print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] Invalid mute time.', flush=True)
            return
        mute_time = int(mute_time)
        mute_info = message.split()[1]
        mute_channel = mute_info.split(':')[0]
        mute_user = mute_info.split(':')[1]
        for channel in channel_list:
            if channel.name == mute_channel:
                for user in channel.clients:
                    if mute_user == user.username:
                        self.muted[(mute_channel, mute_user)] = time.time() + mute_time
                        print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] Muted {mute_user} for'
                              f' {mute_time} seconds.', flush=True)
                        user.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] You have been'
                                             f' muted for {mute_time} seconds.'.encode())
                        for channels in channel_list:
                            channels.broadcast(None, f'[Server message ({datetime.now().strftime("%H:%M:%S")})] '
                                                     f'{mute_user} has been muted for {mute_time} seconds.'.encode())

                        return
        print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {mute_user} is not here.', flush=True)

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
                print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {empty_channel} has been emptied.',
                      flush=True)
                return
        print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {empty_channel} does not exist.', flush=True)

    def shutdown_command(self, message):
        for channel in channel_list:
            for client in channel.clients:
                client.connection.send('/quit'.encode())
                client.connection.close()
            channel.socket.close()
        os._exit(1)


def matched_username(channel, username):
    for client in channel.queue + channel.clients:
        if client.username == username:
            return True
    return False


def add_to_channel(channel, client):
    # Adds client to queue
    channel.queue.append(client)

    # If fewer clients in channel than capacity, add client
    if len(channel.clients) < channel.capacity:
        channel.queue.pop(channel.queue.index(client))
        channel.clients.append(client)
        client.connection.send(
            f'[Server message ({datetime.now().strftime("%H:%M:%S")})] Welcome to the {channel.name} channel, '
            f'{client.username}.\n'.encode())
        channel.broadcast(None,
                          f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has joined the '
                          f'channel.'.encode())
        print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has joined the '
              f'{channel.name} channel.', flush=True)
        channel.receive(client)

    else:
        client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] You are in the waiting'
                               f' queue and there are {channel.queue.index(client)} user(s) ahead of you.'.encode())


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
        timeout_thread = threading.Thread(target=self.set_timeout, args=(client,))
        timeout_thread.start()
        self.add_client(client)

    def set_timeout(self, client):

        first_mute_iteration = True
        # while the client timeout is greater than the current time - timeout value
        while client.timeout >= time.time() - server.TIMEOUT_VALUE:
            # if the client is muted
            if (self.name, client.username) in server.muted:

                if first_mute_iteration:
                    client.timeout = server.muted[(self.name, client.username)] - time.time() + client.timeout
                # If the clients mute time is up, remove
                if time.time() >= server.muted[(self.name, client.username)]:
                    del server.muted[(self.name, client.username)]
                    first_mute_iteration = True
                # Otherwise, the timeout = client.timeout
                else:
                    first_mute_iteration = False

        client.connection.send('/quit'.encode())
        client.connection.close()
        if client in self.queue:
            self.queue.remove(client)
        else:
            self.clients.remove(client)
            if len(self.queue) != 0:
                next_client = self.queue[0]
                self.queue.pop(0)
                self.clients.append(next_client)
                self.broadcast(None,
                               f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {next_client.username} has joined the '
                               f'channel.'.encode())
                print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {next_client.username} has joined the '
                      f'{self.name} channel.', flush=True)
            print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} went AFK.', flush=True)
            self.broadcast(None, f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} '
                                 f'went AFK.'.encode())

    def add_client(self, client):
        # Send welcome message
        client.connection.send(
            f'[Server message ({datetime.now().strftime("%H:%M:%S")})] Welcome to the {self.name} channel,'
            f' {client.username}.'.encode())

        # If there is matched username, cannot enter
        if matched_username(self, client.username):
            client.connection.send(f'\n[Server message ({datetime.now().strftime("%H:%M:%S")})] Cannot enter the '
                                   f'{self.name} channel.'.encode())
            client.connection.send('/quit'.encode())
            client.connection.close()
            return

        # Adds client to queue
        self.queue.append(client)
        if len(self.clients) >= self.capacity:
            client.connection.send(f'\n[Server message ({datetime.now().strftime("%H:%M:%S")})] You are in the waiting'
                                   f' queue and there are {self.queue.index(client)} user(s) ahead of you.'.encode())

        # If fewer clients in channel than capacity, add client
        if len(self.clients) < self.capacity:
            self.queue.pop(self.queue.index(client))
            self.clients.append(client)
            self.broadcast(None, f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has '
                                 f'joined the channel.'.encode())
            print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has joined the '
                  f'{self.name} channel.', flush=True)

        # client can now receive
        self.receive(client)

    def receive(self, client):
        while True:
            try:
                message = client.connection.recv(1024).decode()
                if (self.name, client.username) not in server.muted:
                    client.timeout = time.time()
                self.command_check(message, client)
            except:
                break

    # Check to see if any commands occur
    def command_check(self, message, client):
        not_queue = True
        muted = False
        if len(message) == 0:
            return
        if client in self.queue:
            not_queue = False
        if (self.name, client.username) in server.muted:
            muted = True
        command = message.split()[0]
        if command == "/whisper" and not_queue:
            if muted:
                return
            else:
                self.whisper_command(message, client)
        elif command == "/quit":
            self.quit_command(client)
        elif command == "/list":
            self.list_command(client)
        elif command == "/switch":
            self.switch_command(message, client)
        elif command == "/send" and not_queue:
            self.send_command(message, client)
        elif not_queue:
            print(f'[{client.username} ({datetime.now().strftime("%H:%M:%S")})] {message}', flush=True)
            self.broadcast(client, message)

    # Broadcast message to all clients in channel
    def broadcast(self, sender, message):
        # If no sender, broadcast message alone
        if sender is None:
            for client in self.clients:
                client.connection.send(message)
        # Check if sender muted, if time elapsed, remove from muted list
        elif (self.name, sender.username) in server.muted:
            sender.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] You are '
                                   f'still muted for {int(server.muted[(self.name, sender.username)] - time.time())}'
                                   f' seconds.'.encode())

        # Broadcast message with user
        else:

            for client in self.clients:
                client.connection.send(f'[{sender.username} ({datetime.now().strftime("%H:%M:%S")})] {message}'
                                       .encode())

    def whisper_command(self, message, client):
        send_user = message.split()[1]
        message_only = ' '.join(message.split()[2:])
        print(f'[{client.username} whispers to {send_user}: ({datetime.now().strftime("%H:%M:%S")})] {message_only}',
              flush=True)
        for user in self.clients:
            if user.username == send_user:
                user.connection.send(f'[{client.username} whispers to you: ({datetime.now().strftime("%H:%M:%S")})] '
                                     f'{message_only}'.encode())
                return
        client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {send_user} is not here.'
                               .encode())

    def quit_command(self, client):
        if client in self.clients:

            self.clients.remove(client)
            self.broadcast(None, f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has left'
                                 f' the channel.'.encode())
            if len(self.queue) != 0:
                next_client = self.queue[0]
                self.queue.pop(0)
                self.clients.append(next_client)
                self.broadcast(None,
                               f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {next_client.username} has joined the '
                               f'channel.'.encode())
                print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {next_client.username} has joined the '
                      f'{self.name} channel.', flush=True)
        else:
            self.queue.remove(client)

        client.connection.send(f'/quit'.encode())
        client.connection.close()
        print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has left'
              f' the channel.', flush=True)

    def list_command(self, client):
        first = True
        for channel in channel_list:
            if first:
                client.connection.send(f'[Channel] {channel.name} {len(channel.clients)}/{channel.capacity}/'
                                       f'{len(channel.queue)}.'.encode())
                first = False
            else:
                client.connection.send(f'\n[Channel] {channel.name} {len(channel.clients)}/{channel.capacity}/'
                                       f'{len(channel.queue)}.'.encode())

    def switch_command(self, message, client):
        destination_channel = message.split()[1]

        for channel in channel_list:
            # If the channel exists
            if channel.name == destination_channel:
                # If someone in destination_channel or queue with same username, don't switch
                if matched_username(channel, client.username):
                    client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] Cannot switch to '
                                           f'the {destination_channel} channel.'.encode())
                # Else, remove from queue or channel and add to destination_channel
                else:
                    if client in self.clients:

                        self.clients.remove(client)
                        self.broadcast(None,
                                       f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has'
                                       f' left the channel.'.encode())
                        # If queue not empty, add next in line to clients
                        if len(self.queue) != 0:
                            next_client = self.queue[0]
                            self.queue.pop(0)
                            self.clients.append(next_client)
                            self.broadcast(None,
                                           f'[Server message ({datetime.now().strftime("%H:%M:%S")})] '
                                           f'{next_client.username} has joined the channel.'.encode())
                            print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has '
                                  f'joined the {self.name} channel.', flush=True)
                    # Else the client must be in queue, remove from queue
                    else:
                        self.queue.remove(client)

                    print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} has '
                          f'left the channel.', flush=True)
                    add_to_channel(channel, client)
                return
        client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {destination_channel} does '
                               f'not exist.'.encode())

    def send_command(self, message, client):
        target, file_path, file_size = message.split()[1:]
        file_size = int(file_size)
        for user in self.clients:
            if user.username == target:
                # If file_size == 0 then the path does not exist
                if file_size == 0:
                    client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {file_path} '
                                           f'does not exist.'.encode())
                    return
                user.connection.send(message.encode())
                file_data = b''
                while len(file_data) < file_size:
                    data = client.connection.recv(1024)
                    if not data:
                        break
                    file_data += data
                user.connection.sendall(file_data)
                client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] You sent '
                                       f'{file_path} to {target}.'.encode())
                print(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {client.username} sent {file_path}'
                      f' to {target}', flush=True)
                return
        client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {target} is '
                               f'not here.'.encode())
        # If file_size == 0 then the path does not exist
        if file_size == 0:
            client.connection.send(f'[Server message ({datetime.now().strftime("%H:%M:%S")})] {file_path} '
                                   f'does not exist.'.encode())


class ServerClient:
    def __init__(self, username, connection, address):
        self.username = username
        self.connection = connection
        self.address = address
        self.timeout = time.time()


# RUN FROM TERMINAL

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
                os._exit(1)

            channel_name = fields[1]
            channel_port = int(fields[2])
            channel_cap = int(fields[3])

            if channel_port < 5:
                os._exit(1)

            # duplicate check
            for channel in channel_list:
                if (channel.name == channel_name) or (channel.port == channel_port):
                    os._exit(1)
            if channel_port == 0:
                os._exit(1)
            new_channel = Channel(channel_name, channel_port, channel_cap)
            channel_list.append(new_channel)

    if len(channel_list) < 3:
        exit(1)
    server = Server(channel_list)
    server.start()

# RUN FROM IN PYCHARM
"""
channel_list = [Channel('first', 12351, 2), Channel('second', 12352, 5), Channel('third', 12353, 5)]
server = Server(channel_list)
server.start()
"""
# python3 chatserver.py configfile    
