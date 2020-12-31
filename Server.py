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

accepting_time = 10
game_time = 10
reloading_time = 7

server_ip = scapy.get_if_addr("eth1")
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind((server_ip, 0))
serverSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)  # enable broadcasts
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

server_tcp_socket = socket(AF_INET, SOCK_STREAM)
server_tcp_socket.bind((server_ip, 0))
server_tcp_socket.listen(1)

broadcast_address = '172.1.255.255'
broadcast_port = 13117

magic_cookie = 0xfeedbeef
message_type = 0x2
server_tcp_port = server_tcp_socket.getsockname()[1]


def start_game():
    global_timer = 0
    teams_dictionary = {}
    group1 = {}
    group2 = {}
    threaded_client_list = {}
    print(BrightBlack + BackgroundBrightWhite_ANSI + "  Server started, listening on IP address:" + server_ip + Reset)

    invite_message = struct.pack('!IbH', magic_cookie, message_type, server_tcp_port)

    # function that manages the game with the client
    def thread_for_game(connection, group_name):
        my_points = 0

        while time.time() < global_timer:
            try:
                connection.settimeout(max(global_timer - time.time(), 0))
                data = connection.recv(2048)
                if data:
                    my_points += len(data)
            except Exception:
                break

        if group_name in group1:
            l.acquire()
            group1[group_name] = my_points
            l.release()
        else:
            l.acquire()
            group2[group_name] = my_points
            l.release()

    # function for getting the team name from the client
    def threaded_client(connection, group_num, timer_for_connections, index):
        got_team_name = False
        try:
            connection.settimeout(max(timer_for_connections - time.time(), 0))
            data = connection.recv(2048)
            got_team_name = True
        except Exception:
            return

        if got_team_name:
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
        else:
            threaded_client_list.pop(index)
            connection.close()

    def accept_connections():
        index_for_threads = 0
        timer_for_connections = time.time() + accepting_time
        group_assignment = True
        while time.time() < timer_for_connections:
            try:
                server_tcp_socket.settimeout(max(timer_for_connections - time.time(), 0))
                conn, address = server_tcp_socket.accept()
            except Exception:
                break

            if group_assignment:
                group_num = 1
            else:
                group_num = 2

            group_assignment = not group_assignment
            index_for_threads = index_for_threads + 1
            t = threading.Thread(target=threaded_client,
                                 args=(conn, group_num, timer_for_connections, index_for_threads,))
            threaded_client_list[index_for_threads] = t
            t.start()

        # for t in threaded_client_list:
        #     t.start()

    t = threading.Thread(target=accept_connections, args=())
    t.start()

    for i in range(10):
        serverSocket.sendto(invite_message, (broadcast_address, broadcast_port))
        time.sleep(1)

    t.join()

    if len(threaded_client_list) == 0 or len(teams_dictionary) == 0:
        print(BrightBlue_ANSI + "No one has connected, or No one sent team name :(" + Reset + "\n")
        return

    # welcome message
    welcome_message = BrightBlack + BackgroundBrightWhite_ANSI + Bold
    welcome_message += "$   Welcome to Keyboard Spamming Battle Royale  $   " + Reset + "\n"
    welcome_message += BrightGreen_ANSI + BackgroundGreen_ANSI + "  Green Group:  " + Reset + "\n==\n" + BrightGreen_ANSI
    for team_name in group1.keys():
        welcome_message += team_name
    welcome_message += "\n" + Reset + BackgroundBrightRed
    welcome_message += BrightWhite + "  Red Group:  " + Reset + "\n== \n"
    welcome_message += BrightWhite
    for team_name in group2.keys():
        welcome_message += team_name
    welcome_message += Reset
    welcome_message += "\n\n"
    welcome_message += Bold + BrightRed + "Start pressing keys on your keyboard as fast as you can ! ! !\n" + Reset
    print(welcome_message)
    # end welcome message

    for conn in teams_dictionary.values():
        conn.send(welcome_message.encode('utf-8'))
    print(BrightRed + " ************************************" + Reset)

    # game starts
    l.acquire()
    global_timer = time.time() + game_time
    l.release()

    thread_list = []
    for key, value in teams_dictionary.items():
        t = threading.Thread(target=thread_for_game, args=(value, key))
        thread_list.append(t)

    for thread in thread_list:
        thread.start()

    time.sleep(game_time)

    # end of the game , calculating winners
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
        end_message += BrightBlack + BackgroundBrightWhite_ANSI + "Congratulations to the winners:" + Reset + "\n==\n" + winner_teams
    else:
        end_message += BrightBlack + BackgroundBrightWhite_ANSI + "TEKO TEKO!!!!!!!!!" + Reset + "\n"

    for conn in teams_dictionary.values():
        try:
            conn.send(end_message.encode())
        except:
            pass
    print(end_message)

    for conn in teams_dictionary.values():
        conn.close()

    print("Server Reloading")
    time.sleep(reloading_time)


while True:
    start_game()
