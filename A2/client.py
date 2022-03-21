import getopt, sys
import socket

ip_address = None

long_options = ["Initialize", "Send", "Output ="]
if __name__ == "__main__":
    ip_address = sys.argv[1]
    port = 9000
    initialize_msg = b'hello'
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # bind the ip address to the socket with port
    socket.bind((ip_address, port))
    socket.sendto(initialize_msg, ("255.255.255.255", 9000))
    socket.close()

