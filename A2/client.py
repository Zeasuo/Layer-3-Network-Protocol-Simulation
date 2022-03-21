import getopt, sys
import select
import socket
import json

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
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        readable, writable, exceptional = select.select([connection], [connection], [])

        if readable:
            message, source = connection.recvfrom(1024)
            print(data, source)

        if writable:
            message = input("Input your message here: ")
            destination = input("The destination: ")
            port = input("Enter the port number of the destination: ")
            if destination[:len(destination)-3] == subnet_address:
                writable[0].sendto(str.encode(message), (destination, port))
            else:
                data = {'message': message,
                        'destination': destination,
                        'port': port}
                data_string = json.dumps(data)
                writable[0].sendto(str.encode(data_string), (router_ip, 9000))

