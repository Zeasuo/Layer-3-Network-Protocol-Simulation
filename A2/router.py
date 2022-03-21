import socket
import netifaces as ni
import select

forwarding_table = {}
if __name__ == "__main__":

    # initializing sockets for each interface other than loopback
    listen_sockets = {}
    interfaces = ni.interfaces()
    output_sockets = []
    for intf in interfaces:
        if intf != 'lo':
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
            listen_sockets[intf] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listen_sockets[intf].bind((ip, 9000))
            listen_sockets[intf].listen(5)

    while True:
        readable, writable, exceptional = select.select(listen_sockets.values(),
                                                        [],
                                                        [])
        for s in readable:
            data, address = s.recvfrom(1024)
            print(data, address)




