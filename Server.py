# The UDP Server for my coursework
# We will need the following module to generate randomized lost packets
from ast import Or, Return
from email import message
from inspect import signature
from msilib.schema import Class
from posixpath import split
import random
import socket
# Import needed for UDP headers
import struct
import time

# Import threads
from _thread import *

""" FLAGTYPES
0 - QUIT
1 - ESTAB
2 - BROADCAST
3 - NAK
4 - REPLY
5 - ACK
 """

# Create a UDP socket
# Notice the use of SOCK_DGRAM for UDP packets
socket.setdefaulttimeout(60)
serverSocket = socket.socket()
# Assign IP address and port number to socket
serverSocket.bind(('127.0.0.1', 8000))

serverSocket.listen(5)

# List of clients
clients = []

# Count of clients to make sure too many don't join
NumberofClients = 0

# Agreed upon mild symptoms by the group
mild_symptoms = [
    "COUGH",
    "SNEEZE",
    "FEVER",
    "HEADACHE"
]

# Agreed upon severe symptoms by the group
severe_symptoms = [
    "LOSS OF SMELL",
    "LOSS OF TASTE"
]

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

# Function to determine what symptoms a client has
def symptomsReturn(message):
    # Split up the message (we dont want commas)
    split_message = message.split(", ")

    # Count of number of mild or severe symptoms
    MildSymptoms = 0
    SevereSymptoms = 0

    # Response to be sent back
    Return_Message = ""

    if split_message == "no symptoms":
        Return_Message = "no symptoms"
        return Return_Message

    # Iterate through the mild symptoms and cross check them with the message, if they match then increase the number of mild symptoms
    for i in range (0, len(mild_symptoms)):
        for x in range (0, len(split_message)):
            if split_message[x].upper() == mild_symptoms[i]:
                MildSymptoms += 1
    # Iterate through the severe symptoms and cross check them with the message, if they match then increase the number of severe symptoms
    for i in range (0, len(severe_symptoms)):
        for x in range (0, len(split_message)):
            if split_message[x].upper() == severe_symptoms[i]:
                SevereSymptoms += 1

    # Form the response based on number of severe symptoms or mild symptoms (number of mild symptoms needed agreed upon by group)
    if MildSymptoms >= 3 and SevereSymptoms == 0:
        Return_Message = "mild symptoms"
    elif SevereSymptoms >0 :
        Return_Message = "severe symptoms"
    elif MildSymptoms < 3 and SevereSymptoms == 0:
        Return_Message = "no symptoms"

    return Return_Message

# Unpack funtion
def unpack(full_packet):
    # First part of the packet contains the udp_header
    udp_header = full_packet[:16]

    # The other part of the packet contains the data (message)
    data = full_packet[16:]
    return udp_header, data


def threaded_client(connection, address):
    connection.send(encode("Welcome to the Server", 1))
    Quit = False
    while Quit == False:
        # Receive the packet and the address it was sent from
        full_packet = connection.recv(2048)
        # Short wait time so the server messages dont all come at once
        print("")
        print("Received packet...")
        time.sleep(1)
        print("Unpacking...")
        time.sleep(1)
        print("")

        # Unpack the data
        udp_header, data = unpack(full_packet)
        # Unpack the header and retrieve the checksum
        udp_header = struct.unpack("!IIII", udp_header)
        correct_checksum = udp_header[3]

        # Quit function
        if udp_header[2] == 0:
                print("")
                print("Client quit")
                connection.close()
                Quit = True
        elif compareCHECKSUM(udp_header[3], data) == False:
            print ("Checksum failed: requesting resend...")
            connection.send(encode("Checksum failed", 3))
        else:

            # Split the message between the message and its subject
            split_message = data.decode()
            split_message = split_message.split(": ")
            temp = split_message[0].split(", ")
            messageSubject = temp[1]
            signature = temp[0]

            # If the received message is about someones symptoms run this code
            if messageSubject == "Symptoms":
                addClient(data, address, connection)
                # Set the return message
                Return_message = symptomsResponse(correct_checksum, data)
                # Reply based on return_message
                currentClient = retrieveClient(signature)
                # Respond
                print("Sending message: " + Return_message + " - Client: " + currentClient.signature)
                time.sleep(1)
                print("")
                sent = False
                while sent == False:
                    # Send a broadcast type flag message with all the clients
                    connection.send(encode(Return_message, 2))
                    new_packet = connection.recv(2048)
                    # Unpack the data
                    new_header, newdata = unpack(new_packet)
                    # Unpack the header and retrieve the checksum
                    new_header = struct.unpack("!IIII", new_header)
                    Flag = new_header[2]
                    if Flag == 5:
                        sent = True

                # Check the other clients and send the list to the user and ask if they would like to send get well soon messages to those who are ill
                clientList = checkClients(signature)
                
                sent = False
                while sent == False:
                    # Send a message of the other clients on the server to this client
                    connection.send(encode(clientList, 4))
                    new_packet = connection.recv(2048)
                    # Unpack the data
                    new_header, newdata = unpack(new_packet)
                    # Unpack the header and retrieve the checksum
                    new_header = struct.unpack("!IIII", new_header)
                    Flag = new_header[2]
                    if Flag == 5:
                        sent = True
            
            # If the received message is about someones get well soon message run this code
            elif messageSubject == "Get well message":
                sendGetWellMSG(signature, split_message)
            
            # If the client decided to not reply then wait for another message
            elif messageSubject == "no reply":
                print("")
                print("Client declined to reply")
                time.sleep(1)


def sendGetWellMSG(signature, split_message):
    get_well_message = split_message[1]
    # Get a list of ill clients
    illClients = getIllClients(signature)
    for x in range(len(illClients)):
        tempClient = retrieveClient(illClients[x].signature)
        # Iterate through the list of ill clients and send the get well message
        print("Sending message: " + get_well_message + " - Client: " + tempClient.signature)
        time.sleep(1)
        print("")
        # Send the get well message to the client selected
        tempClient.socket.send(encode(get_well_message, 2))

# Checksum check
def compareCHECKSUM(correct_checksum, data):
    # Check the data is not corrupted
    checksum = CHECKSUM(data)
    if correct_checksum == checksum:
        return True
    else:
        return False

def symptomsResponse(correct_checksum, data):
    # Compare checksums
        corrupted = compareCHECKSUM(correct_checksum, data)
        if corrupted == False:
            return "Checksum failed: please resend message"
        # If the data is not corrupted respond
        elif corrupted == True:
            # Split the message between the message and its subject
            split_message = data.decode()
            split_message = split_message.split(": ")
            return symptomsReturn(split_message[1])

# Client list iterater
def checkClients(signature):
    # If this the first connecting client then no replies needed
    if len(clients) == 1:
        clientList = "No other clients connected to the server"
    else:
        print("Currently connected clients:")
        # Get a list of connected clients
        clientList = "Here are the other Clients also connected to the server:\n"
        for x in range(len(clients)):
            client = clients[x]
            print(client.data.decode())
            if client.signature != signature:
                clientList = clientList + client.data.decode() + "\n"

    return clientList

def getIllClients(signature):
    # Get a list of connected clients
    IllClientList = []
    for x in range(len(clients)):
        client = clients[x]
        if (client.signature != signature) and (client.symptoms == "mild symptoms" or client.symptoms == "severe symptoms"):
            IllClientList.append(client)

    return IllClientList

def addClient(data, address, socket):
    # Split the message between the message and its signature
    splitter = data.decode()
    splitter = splitter.split(": ")
    temp = splitter[0].split(", ")
    signature = temp[0]
    symptoms = symptomsResponse(CHECKSUM(data), data)

    # Add the client to the client list
    lastdata = ""
    newclient = Client(data, address, lastdata, signature, symptoms, socket)
    clients.append(newclient)


# Retrieve information
def retrieveClient(signature):
    for x in range(len(clients)):
        client = clients[x]
        if client.signature == signature:
            return client

# Client class for storing names and addresses
class Client:
  def __init__(self, data, address, lastdata, signature, symptoms, socket):
    self.data = data
    self.address = address
    self.lastdata = lastdata
    self.signature = signature
    self.symptoms = symptoms
    self.socket = socket


# Check for shutting down the server
Quit = False
while Quit == False:
    print("")
    print("(Waiting for connection...)")
    print("")

    # This is for Security, to prevent any DOS attacks, the server will limit the number of clients that are connected to it
    if NumberofClients < 4 :
        newClient, address = serverSocket.accept()
        print("Connected to: " + address[0] + ":" + str(address[1]))
        NumberofClients += 1

        start_new_thread(threaded_client, (newClient, address))
    else:
        serverSocket.listen(5)

serverSocket.close()

    

        


    