import time
from socket import *

#import pynput
# from pynput import keyboard


# def on_press(key):
#     try:
#         print('alphanumeric key {0} pressed'.format(
#             key.char))
#     except AttributeError:
#         print('special key {0} pressed'.format(
#             key))


# def on_release(key):
#     # print('{0} released'.format(
#     #     key))
#     # timeout = time.time() + 10
#     # while time.time() < timeout:
#     try:
#         client_tcp_socket.send('{0}'.format(key).encode('utf-8'))
#     except:  # ConnectionAbortedError | ConnectionResetError:
#         # if key == keyboard.Key.esc:
#         #     # Stop listener
#         return False


while True:
    client_udp_socket = socket(AF_INET, SOCK_DGRAM)
    client_udp_socket.bind(('', 13117))
    client_udp_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    print("Client started, listening for offer requests...")

    data, serverAddress = client_udp_socket.recvfrom(2048)
    print("The server sent: " + data.decode())

    # TO CHECK IF THE MESSAGE IS VALID

    (ip, port) = serverAddress
    print("Received offer from: " + ip + " , attempting to connect... ")
    offer_port = 1500  # TO CHANGE TO THE VALUE GETTING IN THE OFFER
    client_udp_socket.close()

    client_tcp_socket = socket(AF_INET, SOCK_STREAM)
    client_tcp_socket.connect((ip, offer_port))
    client_tcp_socket.send("Maccabi Kempner2\n".encode("utf-8"))

    data = client_tcp_socket.recv(1024)
    print(data.decode())

    # Collect events until released

    # with keyboard.Listener(
    #         # on_press=on_press,
    #         on_release=on_release) as listener:
    #
    #     time.sleep(7)
    #     listener.stop()

    time_out = time.time() + 10
    while time.time() < time_out:
        data = input()
        try:
            client_tcp_socket.send(data)
        except:  # ConnectionAbortedError | ConnectionResetError:
            break

    client_tcp_socket.close()
    print("Server disconnected, listening for offer requests...")

# # ...or, in a non-blocking fashion:
# listener = keyboard.Listener(
#     on_press=on_press,
#     on_release=on_release)
# listener.start()

# client_tcp_socket.close()
