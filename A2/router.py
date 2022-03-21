import socket


if __name__ == "__main__":
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(socket.gethostbyname(socket.gethostname()))