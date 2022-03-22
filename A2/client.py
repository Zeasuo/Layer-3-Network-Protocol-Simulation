import getopt, sys
import select
import socket
import json
from threading import Thread

ip_address = None

long_options = ["Initialize", "Send", "Output ="]


if __name__ == "__main__":
    ip_address = sys.argv[1]
    port = 9000
    subnet_address = ip_address[:len(ip_address)-3]
    print(subnet_address)
    initialize_msg = b'hello'
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # bind the ip address to the socket with port
    s.bind((ip_address, port))
    # send broadcast message
    s.sendto(initialize_msg, (subnet_address+'255', 9000))
    # expected to receive reply and know the IP address of the router
    data, reply_ip = s.recvfrom(1024)
    s.close()

    router_ip = data.decode()
    print(router_ip)
    read = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    read.bind((ip_address, port))

    write = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    write.bind((ip_address, port))
    write.connect((router_ip, 9000))

    while True:
        readable, writable, exceptional = select.select([read], [write], [])

        if read in readable:
            read.recv(1024)
            if not data:
                sys.exit(0)
            print(data)

        if write in writable:
            message = input("Enter Your Message Here: ")
            destination = input("Input Destination IP Address Here: ")
            port = input("Input Destination Port Here: ")

            if destination[:len(destination)-3] == subnet_address:
                write.sendto(str.encode(message), (destination, int(port)))

            else:
                data = {'message': message,
                        'destination': destination,
                        'port': port}
                data_string = json.dumps(data)
                write.send(str.encode(data_string))



