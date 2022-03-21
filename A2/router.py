import socket
import netifaces as ni


if __name__ == "__main__":
    listen_sockets = {}
    interfaces = ni.interfaces()
    for intf in interfaces:
        if intf != 'lo':
            ip = ni.ifaddresses(intf)[ni.AF_INET][0]['addr']
            print(ip)