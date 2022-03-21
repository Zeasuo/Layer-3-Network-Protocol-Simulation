import socket
import netifaces as ni
import select

forwarding_table = {}
if __name__ == "__main__":

    # initializing sockets for each interface other than loopback
    listen_sockets = {}
    interfaces = ni.interfaces()
    input_sockets = []
    output_sockets = []
    # Assign some sockets to all interfaces' broadcast IP
    for intf in interfaces:
        if intf != 'lo':
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']
            listen_sockets[intf] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            listen_sockets[intf].setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            listen_sockets[intf].bind((ip, 9000))

    while True:
        input_sockets = listen_sockets.values()
        readable, writable, exceptional = select.select(input_sockets,
                                                        [],
                                                        [])
        print("found")
        for s in readable:
            data, address = s.recvfrom(1024)
            print(data, address)
