import getopt, sys
import socket
import netifaces as ni

ip_address = None

long_options = ["Initialize", "Send", "Output ="]
if __name__ == "__main__":
    ip_address = sys.argv[1]
    port = 9000
    subnet_address = ip_address[:len(ip_address)-3] + '255'
    print(subnet_address)
    initialize_msg = b'hello'
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # bind the ip address to the socket with port
    s.bind((ip_address, port))
    # send broadcast message
    s.sendto(initialize_msg, (subnet_address, 9000))
    # expected to receive reply and know the IP address of the router
    data, router_ip = s.recvfrom(1024)
    s.close()

    print(data)

