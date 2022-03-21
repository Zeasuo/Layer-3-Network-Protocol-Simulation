import socket
import netifaces as ni


if __name__ == "__main__":
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ni.ifaddresses('eth0')
    ip = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
    print(ip)