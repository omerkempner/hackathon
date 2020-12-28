import struct
import time
from socket import *
# from _thread import *
import threading

l = threading.Lock()

serverUdpPort = 1400
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverUdpPort))
serverSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)  # enable broadcasts

serverTcpPort = 1500
server_tcp_socket = socket(AF_INET, SOCK_STREAM)
server_tcp_socket.bind(('', serverTcpPort))
server_tcp_socket.listen(1)

while True:
    global_timer = 0

    teams_dictionary = {}
    group1 = {}
    group2 = {}

    print("Server started, listening on IP address 172.1.0.4 ")

    broadcast_address = '255.255.255.255'
    broadcast_port = 13117


    # magic_cookie = 0xfeedbeef
    # message_type = 0x2
    # invite_message = struct.pack('!Ibh', magic_cookie, message_type, serverPort)

    # invite_message = "You are invited to the Game".encode("utf-8")
    # serverSocket.sendto(invite_message, (broadcast_address, broadcast_port))

    def threaded_client(connection, group_num):
        data = connection.recv(2048)
        thread_team_name = data.decode('utf-8')
        l.acquire()
        teams_dictionary[thread_team_name] = connection
        l.release()
        if group_num == 1:
            l.acquire()
            group1[thread_team_name] = 0
            l.release()
        else:
            l.acquire()
            group2[thread_team_name] = 0
            l.release()


    def thread_for_game(connection, group_name):
        my_points = 0

        while time.time() < global_timer:
            try:
                connection.settimeout(max(global_timer - time.time(), 0))
                # connection.setblocking(False)
                # TO CHECKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK
                data = connection.recv(2048)
                if data:
                    my_points += 1
                    print(data.decode())
            except Exception:
                pass

            # if not data:
            #     break

        if group_name in group1:
            l.acquire()
            group1[group_name] = my_points
            l.release()
        else:
            l.acquire()
            group2[group_name] = my_points
            l.release()


    def accept_connections():
        print("accepting connections ")
        group_assignment = True
        time_out = time.time() + 7  # 10 seconds from now
        while True:
            if time.time() > time_out:
                break
            conn, address = server_tcp_socket.accept()
            print('Connected to: ' + address[0] + ':' + str(address[1]))

            if group_assignment:
                group_num = 1
            else:
                group_num = 2
            group_assignment = not group_assignment

            t = threading.Thread(target=threaded_client, args=(conn, group_num))
            t.start()
          # start_new_thread(threaded_client, (conn, group_num))

            # ThreadCount += 1
            # print('Thread Number: ' + str(ThreadCount))


    t = threading.Thread(target=accept_connections, args=())
    t.start()
    # start_new_thread(accept_connections, ())

    for i in range(10):
        print(i)
        invite_message = "You are invited to the Game".encode("utf-8")
        serverSocket.sendto(invite_message, (broadcast_address, broadcast_port))
        time.sleep(1)

    # group_assignment = True
    #
    # for pair in teams_dictionary:
    #     # print(pair)
    #     if group_assignment:
    #         group1[pair] = teams_dictionary.get(pair)
    #     else:
    #         group2[pair] = teams_dictionary.get(pair)
    #     group_assignment = not group_assignment

    welcome_message = """Welcome to Keyboard Spamming Battle Royale.
    Group 1:
    ==\n"""
    for team_name in group1.keys():
        welcome_message += team_name
    welcome_message += """"
    Group 2:
    =="""
    for team_name in group2.keys():
        welcome_message += team_name

    welcome_message += "Start pressing keys on your keyboard as fast as you can!!"

    print(welcome_message)
    for conn in teams_dictionary.values():
        conn.send(welcome_message.encode('utf-8'))
    print("*************************************************")

    l.acquire()
    global_timer = time.time() + 10
    l.release()

    thread_list = []
    for key, value in teams_dictionary.items():
        t = threading.Thread(target=thread_for_game, args=(value, key))
        thread_list.append(t)

    for thread in thread_list:
        thread.start()

    # for thread in thread_list:
    #     thread.join()

    time.sleep(10)

    print("Time over")

    sum1 = 0
    sum2 = 0
    for points in group1.values():
        sum1 += points

    for points in group2.values():
        sum2 += points

    winner_group = ""
    winner_teams = ""

    if sum1 > sum2:
        winner_group = "Group 1"
        for team_name in group1.keys():
            winner_teams += team_name
    else:
        winner_group = "Group 2"
        for team_name in group2.keys():
            winner_teams += team_name

    end_message = """Game over! Group 1 typed in """ + str(sum1) + """ characters. Group 2 typed in """ \
                  + str(sum2) + """" characters. """ + winner_group + \
                  """"" wins!\n Congratulations to the winners:\n ==\n""" + winner_teams

    print(end_message)

    for conn in teams_dictionary.values():
        conn.close()

    # server_tcp_socket.close()
