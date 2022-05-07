# The UDP Client for my coursework
# Import needed to generate randomized lost packets
from email.message import Message
from http import client
import sys
# Import needed to generate sockets
import socket
import time
# Import needed for UDP headers
import struct

""" FLAGTYPES
0 - QUIT
1 - ESTAB
2 - BROADCAST
3 - NAK
4 - REPLY
5 - ACK
 """

# Checksum to make sure the messages received dont get corrupted
import zlib
def CHECKSUM(message):
    checksum = zlib.crc32(message)
    return checksum

#Encoding
def encode(Message, flagType):
    # Message encoding then checksum calculation
    packet = Message.encode()
    checksum = CHECKSUM(packet)
    # As no packets we are sending will be too large to send all at once, we will only ever have to have one packet number per packet
    currentPacket = 1
    checksum = CHECKSUM(packet)
    udp_header = struct.pack("!IIII", currentPacket, 0, flagType, checksum)

    # Combine the UDP header with the actual encoded data
    combined_packet = udp_header + packet
    return combined_packet

# Unpack funtion
def unpack(full_packet):
    # First part of the packet contains the udp_header
    udp_header = full_packet[:16]
    
    # The other part of the packet contains the data (message)
    data = full_packet[16:]
    return udp_header, data

# Receive packet funtion
def receive():
    # Receive the packet and the address it was sent from
    full_packet, sender_address = clientSocket.recvfrom(1024)
    return full_packet, sender_address

# Checksum check
def compareCHECKSUM(correct_checksum, data):
    # Check the data is not corrupted
    checksum = CHECKSUM(data)

    # Compare checksums
    if correct_checksum == checksum:
        return True
    # If the data is corrupted respond
    else:
        return False

# Create a UDP socket
UDP_IP_ADDRESS = "127.0.0.1"
UDP_PORT_NO = 8000

# Set timeout for clients, then define the socket for the clients right after
socket.setdefaulttimeout(120)
clientSocket = socket.socket()

try:
    clientSocket.connect(('127.0.0.1', 8000))
except socket.error as e:
    print(str(e))
    # Let the client know that if the connection has not worked then there are too many connections
    print("There are too many connections in the server, try again later")

full_packet, sender_address = receive()
udp_header, data = unpack(full_packet)

print(data.decode())
print("")
time.sleep(1)

SignIn = input("Please enter your signature below:\n")
Message = input("Do you have any symptoms (please space them out with a comma and a space) or type '0' to leave:\n")
if Message == "0":
    clientSocket.send(encode("Quit", 0))
else:
    Message = SignIn + ", Symptoms: " + Message
    print("")


    # Check for logging the client off
    Received = False
    Quit = False
    while Quit == False:

        while Received == False:
            # Checker for when the message has been received properly
            Received = False
            Received2 = False
            # Send the packet
            clientSocket.send(encode(Message, 4))
            while Received2 == False:
                full_packet, sender_address = receive()
                udp_header, data = unpack(full_packet)
                # Unpack the header and retrieve the checksum
                udp_header = struct.unpack("!IIII", udp_header)
                correct_checksum = udp_header[3]

                if udp_header[2] == 3:
                    print("Checksum failed resending data")
                    time.sleep(1)
                    Received2 = True
                else:
                    if compareCHECKSUM(udp_header[3], data) == False:
                        print("Checksum failed: requesting resend...")
                        clientSocket.send(encode("Checksum failed", 3))
                    else:
                        clientSocket.send(encode("received", 5))
                        print("You have " + data.decode() + " of COVID")
                        time.sleep(1)
                        print(" ")
                        Received = True
                        Received2 = True
        
        full_packet, sender_address = receive()
        udp_header, data = unpack(full_packet)
        # Unpack the header and retrieve the checksum
        udp_header = struct.unpack("!IIII", udp_header)
        correct_checksum = udp_header[3]

        if compareCHECKSUM(udp_header[3], data) == False:
            print("Checksum failed: requesting resend...")
            clientSocket.send(encode("Checksum failed", 3))
        else:
            clientSocket.send(encode("received", 5))
            replyMSG = data.decode()
            print(replyMSG)
            time.sleep(1)
            if replyMSG != "No other clients connected to the server":
                replied = False
                while replied == False:
                    reply = input("Would you like to send a message to any of your ill colleagues? (y/n)\n")
                    if reply == "y":
                        replied = True
                        # Answer with a personalised message if they reply with 'y'
                        print("")
                        getWellMessage = input("What would you like to say? (we will sign your name for you)\n")
                        getwell = SignIn + ", Get well message: " + getWellMessage + ", Love from " + SignIn
                        clientSocket.send(encode(getwell, 4))
                    elif reply == "n":
                        replied = True
                        # Answer with no if they reply with 'n'
                        noReply = SignIn + ", no reply: No"
                        clientSocket.send(encode(noReply, 4))
                    elif reply == "0":
                        replied = True
                        clientSocket.send(encode("Quit", 0))
                        clientSocket.close()

        print("")
        print("(Waiting for response...)")
        print("")
        full_packet, sender_address = receive()
        udp_header, data = unpack(full_packet)

        print("New message:")
        print(data.decode())

    clientSocket.close()

    

    

    
        


