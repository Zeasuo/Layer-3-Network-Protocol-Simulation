import socket
import netifaces as ni
import select

forwarding_table = {}
if __name__ == "__main__":

    # initializing sockets for each interface other than loopback
    listen_sockets = {}
    end_to_end_sockets = {}
    interfaces = ni.interfaces()
    input_sockets = []
    output_sockets = []
    # Assign some sockets to all interfaces' broadcast IP
    for intf in interfaces:
        if intf != 'lo':
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['broadcast']
            listen_sockets[intf] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            listen_sockets[intf].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listen_sockets[intf].setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(intf).encode('utf-8'))
            listen_sockets[intf].bind((ip, 9000))

            ip2 = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
            end_to_end_sockets[intf] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            end_to_end_sockets[intf].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            end_to_end_sockets[intf].setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, str(intf).encode('utf-8'))
            end_to_end_sockets[intf].bind((ip2, 9000))
            end_to_end_sockets[intf].listen(5)

    input_sockets = list(listen_sockets.values()) + list(end_to_end_sockets.values())
    print(list(listen_sockets.values()))
    while True:

        readable, writable, exceptional = select.select(input_sockets,
                                                        output_sockets,
                                                        [])
        for s in readable:
            if s.proto == 17:
                data, address = s.recvfrom(1024)
                print(data, address)
                print(socket.gethostbyname_ex(socket.gethostname()))
