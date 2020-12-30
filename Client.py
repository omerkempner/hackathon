import struct
import threading
import time
from socket import *
from getch import *
import queue
import tty, termios, sys

from multiprocessing import Process
import asyncio

# time_out = 0
magic_cookie = 0xfeedbeef


def send_char(data_queue, client_tcp_socket, time_out):
    get_data_thread = threading.Thread(target=get_char, args=(data_queue, time_out))
    get_data_thread.start()
    while time.time() < time_out:
        if not data_queue.empty():
            try:
                to_send = data_queue.get()
                print(to_send)
                client_tcp_socket.send(to_send.encode('utf-8'))
            except:  # ConnectionAbortedError | ConnectionResetError:
                break


# def get_from_server(client_tcp_socket):
#     while True:
#         try:
#             data = client_tcp_socket.recv(1024)
#             if not data:
#                 break
#         except:
#             print("SERVER DISCONNECTED")
#             break

def get_char(data_queue, time_out):
    while time.time() < time_out:
        char = getch()
        # char = sys.stdin.read(1)
        data_queue.put(char)


# def timeout_thread(time_out):
#     while time.time() < time_out:
#         time.sleep(1)
#         print(time.time())
#     print("Game Over, press any key to continue")


def start():
    while True:
        client_udp_socket = socket(AF_INET, SOCK_DGRAM)
        client_udp_socket.bind(('', 13117))
        client_udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

        client_udp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        client_udp_socket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)

        in_game = False
        print("Client started, listening for offer requests...")

        while not in_game:
            data, serverAddress = client_udp_socket.recvfrom(7)
            (sent_cookie, msg_type, msg_server_port) = struct.unpack('!IbH', data)
            (ip, port) = serverAddress

            if sent_cookie == magic_cookie and msg_type == 0x2 and ip == "172.1.0.73":
                print("Received offer from: " + ip + " , attempting to connect... ")

                # accepting offer, sending team name
                client_tcp_socket = socket(AF_INET, SOCK_STREAM)
                try:
                    client_tcp_socket.connect((ip, msg_server_port))
                    client_tcp_socket.send("Maccabi Kempner\n".encode("utf-8"))
                except:
                    break

                in_game = True
                client_udp_socket.close()
                data = client_tcp_socket.recv(1024)
                print(data.decode())

                # game starting
                data_queue = queue.Queue()
                time_out = time.time() + 10

                send_data_thread = threading.Thread(target=send_char, args=(data_queue, client_tcp_socket, time_out,))
                # get_from_server_thread = threading.Thread(target=get_from_server, args=(client_tcp_socket,))
                send_data_thread.start()
                # get_from_server_thread.start()
                send_data_thread.join()

                client_tcp_socket.close()
                print("game over, press any key to continue")
                print("Server disconnected, listening for offer requests...")


start()