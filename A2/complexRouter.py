import socket
import threading
import time

import netifaces as ni
import select
import json

forwarding_table = {}


def advertise():
    intfs = ni.interfaces()
    broadcasts = []
    socket_b_ip = {}
    for intf in intfs:
        if intf != 'lo':
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
            broadcast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                      socket.IPPROTO_UDP)
            broadcast.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            broadcast.bind((ip, 9001))
            broadcasts.append(broadcast)
            socket_b_ip[broadcast] = ni.ifaddresses(intf)[ni.AF_INET][0][
                'broadcast']

    while True:
        readable, writable, exceptional = select.select([], broadcasts, [])
        for s in writable:
            s.sendto(str.encode(json.dumps(forwarding_table)),
                     (socket_b_ip[s], 9002))
        time.sleep(5)


def get_advertise():
    intfs = ni.interfaces()
    receive_from = []
    for intf in intfs:
        if intf != 'lo':
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']
            receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                    socket.IPPROTO_UDP)
            receive.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            receive.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE,
                               str(intf).encode('utf-8'))
            receive.bind((ip, 9002))
            receive_from.append(receive)

    while True:
        r, w, e = select.select(receive_from, [], [])
        for sock in r:
            sourcedata, sourceaddress = sock.recvfrom(1024)
            receiveddata = json.loads(sourcedata.decode())
            print(receiveddata)
            for (key, value) in receiveddata.items():
                if key not in forwarding_table.keys() \
                        or (key in forwarding_table.keys() and value[1] + 1 <
                            forwarding_table[key][1]):
                    forwarding_table[key] = (sourceaddress[0], value[1]+1)

            print("forwarding_table:")
            print(forwarding_table)
        time.sleep(5)


if __name__ == "__main__":
    # initializing sockets for each interface other than loopback
    listen_sockets = {}
    end_to_end_sockets = {}
    interfaces = ni.interfaces()
    # sockets that should be input or output to
    input_sockets = []
    output_sockets = []
    # dictionary that map broadcast ip to inet addr
    broadcast_to_tcp = {}
    # dictionary the map client ip address to a specific socket
    client_connections = {}
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
    print(input_sockets)

    threading.Thread(target=advertise).start()
    threading.Thread(target=get_advertise).start()
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
                print("connection established on ip ", client_ip)

            if s in client_connections.values():
                received = s.recv(1024)
                data = json.loads(received.decode())
                print(data)
                destination = data['destination']
                port = data['port']
                if (destination, int(port)) not in client_connections:
                    s.send("The destination is unreachable")
                data['ttl'] -= 1
                client_connections[(destination, int(port))].send(received)
