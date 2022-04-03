import socket
import threading
import time

import netifaces as ni
import select
import json

forwarding_table = {}
# sockets that should be input or output to
input_sockets = []
output_sockets = []
client_connections = {}
router_connections = []

neighbor_routers = {}


def get_neighbour():
    global input_sockets
    global output_sockets
    global router_connections
    tIntfs = ni.interfaces()
    broadcasts = []
    receive_from = []
    socket_b_ip = {}
    nearby_router = []
    bip_to_inet = {}
    for intf in tIntfs:
        if intf != 'lo':
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
            broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                      socket.IPPROTO_UDP)
            broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            broadcast.bind((ip, 9001))
            broadcasts.append(broadcast)
            socket_b_ip[broadcast] = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']

            ip_b = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']
            receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                    socket.IPPROTO_UDP)
            receive.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            receive.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE,
                               str(intf).encode('utf-8'))
            receive.bind((ip_b, 9002))
            receive_from.append(receive)

            bip_to_inet[ip_b] = ip

    while True:
        readable, writable, exceptional = select.select(receive_from, broadcasts, [])
        if readable:
            for s in readable:
                sourcedata, sourceAddress = s.recvfrom(1024)
                if sourceAddress[0] != bip_to_inet[s.getsockname()[0]]:
                    receivedData = json.loads(sourcedata.decode())
                    print("Received: from " + sourceAddress[0])
                    neighbor_routers[bip_to_inet[s.getsockname()[0]]] = sourceAddress[0]
                    print_forwarding_table()

                    if sourceAddress[0] not in nearby_router:
                        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        new_socket.bind((bip_to_inet[s.getsockname()[0]], 9005))
                        new_socket.connect((sourceAddress[0], 9000))
                        input_sockets.append(new_socket)
                        output_sockets.append(new_socket)
                        router_connections.append(new_socket)
                        nearby_router.append(sourceAddress[0])
        else:
            for s in writable:
                s.sendto(str.encode(json.dumps('hello there')), (socket_b_ip[s], 9002))
                time.sleep(5)
        time.sleep(5)


def print_forwarding_table():
    global forwarding_table
    print("Forwarding Table:")
    for key in forwarding_table.keys():
        print(key + ": " + forwarding_table[key][0] + " " + str(forwarding_table[key][1]))

'''
This function creates a socket to OSPFMonitor and writes the forwarding table to it.
Only use golable variables forwards_table 
'''

def send_forwarding_table():
    pass





if __name__ == "__main__":
    # initializing sockets for each interface other than loopback
    listen_sockets = {}
    end_to_end_sockets = {}
    interfaces = ni.interfaces()
    # dictionary that map broadcast ip to inet addr
    broadcast_to_tcp = {}
    # dictionary the map client/router ip address to a specific socket

    ip_to_intf = {}
    # Assign some sockets to all interfaces' broadcast IP
    for intf in interfaces:
        if intf != 'lo':
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']
            listen_sockets[ip] = socket.socket(socket.AF_INET,
                                               socket.SOCK_DGRAM,
                                               socket.IPPROTO_UDP)
            listen_sockets[ip].setsockopt(socket.SOL_SOCKET,
                                          socket.SO_REUSEADDR, 1)
            listen_sockets[ip].setsockopt(socket.SOL_SOCKET,
                                          socket.SO_BINDTODEVICE,
                                          str(intf).encode('utf-8'))
            listen_sockets[ip].bind((ip, 9000))

            ip2 = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
            end_to_end_sockets[ip2] = socket.socket(socket.AF_INET,
                                                    socket.SOCK_STREAM)
            end_to_end_sockets[ip2].setsockopt(socket.SOL_SOCKET,
                                               socket.SO_REUSEADDR, 1)
            end_to_end_sockets[ip2].setsockopt(socket.SOL_SOCKET,
                                               socket.SO_BINDTODEVICE,
                                               str(intf).encode('utf-8'))
            end_to_end_sockets[ip2].bind((ip2, 9000))
            end_to_end_sockets[ip2].listen(5)

            broadcast_to_tcp[ip] = ip2

            ip_to_intf[ip2] = intf

    input_sockets = list(listen_sockets.values()) + list(
        end_to_end_sockets.values())

    threading.Thread(target=get_neighbour).start()

    while True:

        readable, writable, exceptional = select.select(input_sockets,
                                                        output_sockets,
                                                        [])
        for s in readable:
            if s.proto == 17:
                data, address = s.recvfrom(1024)
                interface_ip = broadcast_to_tcp[s.getsockname()[0]]
                forwarding_table[address[0]] = (interface_ip, 0)
                s.sendto(str.encode(interface_ip), (address[0], address[1]))

            if s in end_to_end_sockets.values():
                print("new connection come in")
                new_connection, client_ip = s.accept()
                new_connection.setsockopt(socket.SOL_SOCKET,
                                          socket.SO_BINDTODEVICE, str(
                        ip_to_intf[s.getsockname()[0]]).encode('utf-8'))
                client_connections[client_ip] = new_connection
                input_sockets.append(new_connection)
                output_sockets.append(new_connection)
                print(client_connections)
                print(router_connections)
                print("connection established on ip ", client_ip)

            if s in client_connections.values() or s in router_connections:
                received = s.recv(1024)
                data = json.loads(received.decode())
                ttl = int(data['ttl'])
                ttl -= 1
                print(data)
                destination = data['destination']
                port = data['port']
                data['ttl'] = ttl
                sent = json.dumps(data)
                if (destination, int(port)) in client_connections:
                    client_connections[(destination, int(port))].send(str.encode(sent))
                elif destination in forwarding_table:
                    print("sending to other router")
                    client_connections[(forwarding_table[destination][0], 9005)].send(str.encode(sent))
                else:
                    s.send(str.encode(json.dumps("The destination is unreachable")))
