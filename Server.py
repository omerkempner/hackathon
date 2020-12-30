import struct
import time
from socket import *
# from _thread import *
import threading
import scapy.all as scapy

l = threading.Lock()

BrightBlack = u"\u001b[30;1m"
BrightRed = u"\u001b[31;1m"
BrightGreen_ANSI = u"\u001b[32;1m"
BrightYellow = u"\u001b[33;1m"
BrightBlue_ANSI = u"\u001b[34;1m"
BrightMagenta = u"\u001b[35;1m"
BrightCyan = u"\u001b[36;1m"
BrightWhite = u"\u001b[37;1m"
Black = u"\u001b[30m"

BackgroundBrightWhite_ANSI = u"\u001b[47;1m"
BackgroundGreen_ANSI = u"\u001b[42m"
BackgroundBrightRed = u"\u001b[41;1m"

Reset = u"\u001b[0m"

Bold = u"\u001b[1m"

server_ip = scapy.get_if_addr("eth1")

# serverUdpPort = 1400
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind((server_ip, 0))
serverSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)  # enable broadcasts
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

serverTcpPort = 4322
server_tcp_socket = socket(AF_INET, SOCK_STREAM)
server_tcp_socket.bind((server_ip, serverTcpPort))
server_tcp_socket.listen(1)


def start_game():
    global_timer = 0

    teams_dictionary = {}
    group1 = {}
    group2 = {}
    threaded_client_list = []

    # print("Server started, listening on IP address: " + server_ip)
    print(BrightBlack + BackgroundBrightWhite_ANSI + "  Server started, listening on IP address:" + server_ip + Reset)

    broadcast_address = '172.1.255.255'
    broadcast_port = 13117

    magic_cookie = 0xfeedbeef
    message_type = 0x2
    invite_message = struct.pack('!IbH', magic_cookie, message_type, serverTcpPort)

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
                    my_points += len(data)
            except Exception:
                break

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
        time_out = time.time() + 10  # 10 seconds from now
        group_assignment = True
        while time.time() < time_out:
            try:
                server_tcp_socket.settimeout(max(time_out - time.time(), 0))
                conn, address = server_tcp_socket.accept()
            except Exception:
                break

            print('Connected to: ' + address[0] + ':' + str(address[1]))  # DELETE

            if group_assignment:
                group_num = 1
            else:
                group_num = 2

            group_assignment = not group_assignment
            t = threading.Thread(target=threaded_client, args=(conn, group_num))
            threaded_client_list.append(t)

        for t in threaded_client_list:
            t.start()

    t = threading.Thread(target=accept_connections, args=())
    t.start()

    for i in range(10):
        serverSocket.sendto(invite_message, (broadcast_address, broadcast_port))
        time.sleep(1)

    t.join()
    if len(threaded_client_list) == 0:
        print(BrightBlue_ANSI + "No one has connected :(" + Reset + "\n")
        return

    welcome_message = BrightBlack + BackgroundBrightWhite_ANSI + Bold
    welcome_message += "    $   Welcome to Keyboard Spamming Battle Royale  $   " + Reset + "\n"
    welcome_message += BrightGreen_ANSI + BackgroundGreen_ANSI + "  Green Group:  " + Reset + "\n ==\n" + BrightGreen_ANSI
    for team_name in group1.keys():
        welcome_message += team_name
    welcome_message += "\n" + Reset + BackgroundBrightRed
    welcome_message += BrightWhite + "  Red Group:  " + Reset + "\n    == \n"
    welcome_message += BrightWhite
    for team_name in group2.keys():
        welcome_message += team_name
    welcome_message += Reset
    welcome_message += "\n\n"

    welcome_message += Bold + BrightRed + " Start pressing keys on your keyboard as fast as you can ! ! !\n" + Reset

    print(welcome_message)
    for conn in teams_dictionary.values():
        conn.send(welcome_message.encode('utf-8'))
    print(BrightRed + " ************************************" + Reset)

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

    sum1 = 0
    sum2 = 0
    for points in group1.values():
        sum1 += points

    for points in group2.values():
        sum2 += points

    winner_group = ""
    winner_teams = ""

    is_tie = False

    if sum1 > sum2:
        winner_group = BrightGreen_ANSI + BackgroundGreen_ANSI + "Green Group" + Reset
        winner_teams += BrightGreen_ANSI
        for team_name in group1.keys():
            winner_teams += team_name
        winner_teams += Reset
    else:
        if sum1 < sum2:
            winner_group = BackgroundBrightRed + BrightWhite + "Red Group" + Reset
            winner_teams += BrightRed
            for team_name in group2.keys():
                winner_teams += team_name
            winner_teams += Reset
        else:
            is_tie = True

    print(Bold + BrightRed +
          """
           _____       ___       ___  ___   _____  
          /  ___|     /   |     /   |/   | |  ___| 
          | |        / /| |    / /|   /| | | |__   
          | |  _    / ___ |   / / |__/ | | |  __|  
          | |_| |  / /  | |  / /       | | | |___  
          \_____/ /_/   |_| /_/        |_| |_____|
  
           _____   _     _   _____   _____   
          /  _  \ | |   / / |  ___| |  _  \  
          | | | | | |  / /  | |__   | |_| |  
          | | | | | | / /   |  __|  |  _  /  
          | |_| | | |/ /    | |___  | | \ \  
          \_____/ |___/     |_____| |_|  \_\
  
          """ + Reset
          )
    end_message = "" + Reset
    # end_message = Bold + BrightRed + "    G a m e   o v e r !     " +Reset +" \n"
    end_message += Reset + BrightBlack + BackgroundBrightWhite_ANSI + "Group 1 typed in " + str(
        sum1) + " characters." + Reset + "\n"
    end_message += BrightBlack + BackgroundBrightWhite_ANSI + "Group 2 typed in " + str(
        sum2) + " characters." + Reset + "\n"
    if not is_tie:
        end_message += winner_group + BrightBlack + BackgroundBrightWhite_ANSI + " wins!" + Reset + "\n"
        end_message += BrightBlack + BackgroundBrightWhite_ANSI + "   Congratulations to the winners:" + Reset + "\n==\n" + winner_teams
    else:
        end_message += BrightBlack + BackgroundBrightWhite_ANSI + "TEKO TEKO!!!!!!!!!" + Reset + "\n"

    print(end_message)

    for conn in teams_dictionary.values():
        conn.close()

    time.sleep(7)
    # server_tcp_socket.close()


while True:
    start_game()