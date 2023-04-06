import socket
import sys

SERVER_HOST = socket.gethostname()
client_skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

if len(sys.argv) != 3:
    exit(1)

SERVER_PORT = int(sys.argv[1])
username = sys.argv[2]


client_skt.connect((SERVER_HOST, SERVER_PORT))
# send username to server
client_skt.send(username.encode())
# Receive and print welcome message
welcome_message = client_skt.recv(1024).decode()
print(welcome_message)

# message = input('Input: ')
# client_skt.send(message.encode())

response = client_skt.recv(1024).decode()

print('Received from server: ', response)

# if message == 'quit':
#     client_skt.close()

# python3 chatclient.py 12351 tank
