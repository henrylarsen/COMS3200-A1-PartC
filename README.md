# COMS3200-A1-PartC:

### Multi-channel chat server


#### Goals:
To implement a multi-channel chat application using socket programming in Python 3 or C. To create two programs; a chat
 client (`chatclient.py`) and a chat server (`chatserver.py`).

#### Approach/Functions:
This code takes an object-oriented approach to create the multi-channel chat server. When started, the channels from the
configfile are created as Channel objects. A Server object is then created where all of the setup occurs including 
creating threads for all of the channels. When connecting with server, clients connect directly with a Channel. The 
server can communicate to all Channels using its channels field. When clients connect, a ServerClient object is created
with its own thread and added to the queue of the channel if it meets the requirements. On the client side, the Client
object is created, and a socket is created and connected to the given channel. The client creates a thread to send 
messages, and one to create them. Here is the breakdown of the classes used in each respective file:

### chatclient.py

#### Client

- Class for the clients of the server from the client-side. One client object is created every time the chatclient.py 
file is executed.

##### __init__(self, channel_port, username)

- Initialized new client object with the following fields:
  - `self.channel_port` – initialized with given port
  - `self.username` – initialized with given username
  - `self.host` – initialized by getting the host name locally
  - `self.socket` – starts TCP socket connection

##### connect_channel(self)

- Called after Client is created.
- Connects the socket to the server channel and sends its username.
- Starts threads for sending and receiving messages to the channel.

##### send(self)

- Sends out messages to server that the user has inputted. 
- If `/send` is used, it sends out the data of the file being sent.
- Exits if it cannot send anymore.

##### receive(self)

- Receives any message that is sent from the channel.
- For `/send` commands directed to it, it deals with incoming file data.
- If received `/quit`, then it terminates the process.

### chatserver.py

#### Server

- Class for the overall server. This handles all server-side commands. All channels are created from this.

##### __init__(self, channels)

- `self.channels` – initialized with channels from the configfile
- `self.muted` – list of muted clients, initialized to empty.
- `self.TIMOUT_VALUE` - the amount of time (seconds) that client has of inactivity before disconnecting

##### start(self)

- Starts the `server_thread` which waits for any incoming server-side commands.
- Creates the threads for all channels in the `channel_list`.

##### server_input(self)

- Waits for incoming server-side commands.

##### server_commands(self, message)

- Directs the server-side commands to the right function.

##### kick_command(self, message)

- Handles the kick command, removing a user from the server (as per specification).

##### mute_command(self, message)

- Handles the mute command, muting a user for given seconds (as per specification).

##### empty_command(self, message)

- Handles the empty command, removing all users from a given channel (as per specification).

##### shutdown_command(self, message)

- Handles the shutdown command, shutting down the server and ending all connections.

#### Channel

##### __init__(self, name, port, capacity)

- Creates the TCP server socket, binds it to a port and the host, and starts listening.
  - `self.port` – initialized to given port
  - `self.name` – initialized to given channel name
  - `self.capacity` – initialized to given channel capacity
  - `self.clients` – clients in the channel, initialized to empty list
  - `self.queue` – clients in channel queue, initialized to empty list
  - `self.host` - initialized by getting the host name locally

##### start(self)

- Starts the thread of any client trying to enter the channel.

##### handle_client(self, conn, addr)

- Gets the username and creates a ServerClient object for the connection. Calls add_client on the client.

##### set_timeout(self, client)
- Handles all dynamic timing of clients including timeout and mute values.
- Updates `server.muted` list.

##### add_client(self, client)

- Adds the given client to the queue. If there is space in the channel, it removes the client from the queue and adds it
 to the client.
- If client has the same username as another, it does not let it enter.

##### receive(self, client)

- Received any client message and forwards it to command_check.

##### command_check(self, message, client)

- Forwards to proper command function. If none, broadcast the message to the channel using broadcast.

##### broadcast(self, sender, message)

-	Broadcasts messages. The messages are either sent with user info, or as a server message.
-	Does not broadcast to muted clients.

##### whisper_command(self, message, client)
-	Handles whisper command. Sends message to only the given user if they are in the channel or tells client that target
 does not exist.

##### quit_command(self, message, client)
-	Handles quit command. Removes the client from the channel and closes it’s connection.

##### list_command(self, client)
-	Handles list command. Sends client a list of the channels with capacity, current users, and number of clients in 
queue.

##### switch_command(self, client)
-	Handles switch command. If the channel exits and there is not a user with the same username, switch the client to
 that channel and a update queuing.

##### send_command(self, message, client)
-	Handles send command. Sends a given file to the given user and copies it into the directory of the client’s
 executable.

#### ServerClient
-	Client from the server-side. 
##### __init__(self, username, connection, address)
   - `self.username` – Username of the client, initialized with given value.
   - `self.connection` – Initialized with given connection.
   - `self.address` – Initialized with given address.
   - `self.timeout` -  Current time (seconds) until client times-out.

#### Global Functions
##### matched_username(channel, username)
- Returns `True` if username is in `channel.queue` or `channel.clients`.

##### add_to_channel(channel, client)
- Adds client to channel.

### Testing
This program was tested extensively using personal testing methods, and the course-provided testing scripts. Here is 
the log kept for the course testing. Note that some results are inconsistent, meaning that they will not always pass 
due to race conditions caused by the scripts.

##### CONFORMITY
test-illegals. ---GOOD		

##### CONFIG FILE 
test-badconf-ephemeral.sh		---GOOD

test-badconf-nonexist.sh		---GOOD

test-badconf-numchannel.sh		---GOOD

test-badconf-alphacap.sh		---GOOD

test-badconf-smallcap.sh		---GOOD

test-badconf-alphaport.sh		---GOOD

test-badconf-twochannels.sh		---GOOD

test-badconf-dupname.sh			---GOOD

test-badconf-dupport.sh			---GOOD

test-badconf-missingno.sh		---GOOD

##### SERVER

test-server-noconfig.sh			---GOOD

test-server-overload.sh			---GOOD

##### CLIENT

test-client-noargs.sh			---GOOD

test-client-noport.sh			---GOOD

test-client-alphaport.sh		---GOOD	

test-client-noname.sh			---GOOD

test-client-overload.sh			---GOOD

##### CONJUNCTION

test-connect1.sh				---GOOD

test-connect2.sh				---GOOD

test-channels.sh				---GOOD (inconsistent)	

test-queue-dup.sh				---GOOD


##### CLIENT COMMANDS

test-whisper-good.sh		---GOOD (inconsistent)

test-whisper-bad.sh			---GOOD

test-quit-channel.sh	    ---GOOD (inconsistent)

test-quit-queue.sh			

test-list.sh				- timing seems all over the place, try again later

test-switch-good.sh			---GOOD (inconsistent)

test-switch-bad.sh			---GOOD (inconsistent)

test-switch-full.sh			- come back, timing off but also not working

test-switch-dup.sh   			---GOOD              

test-send-good.sh				- needs work

test-send-badfile.sh                                    

test-send-badclient.sh                               

test-send-both.sh      

test-noncommand.sh

##### SERVER COMMANDS

test-kick-badchannel.sh             ---GOOD    

test-kick-badclient.sh         	    ---GOOD      

test-kick-badclientandchannel.sh    ---GOOD

test-kick-good.sh                                    

test-mute-badchannel.sh			---GOOD

test-mute-badclient.sh			---GOOD

test-mute-timer.sh			    ---GOOD

test-mute-good.sh				---GOOD

***test-mute-timeout.sh	-- Manual testing for this***
                                                                                            
test-empty-bad.sh				---GOOD

test-empty-multichannel.sh                    

test-shutdown.sh           		---GOOD  

37/47 tests pass