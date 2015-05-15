#!/usr/bin/python3
import socket
import argparse
from time import sleep
import re
import sys
import sqlite3
import threading
import queue

COLOR = {
        'SPADES': 0x10,
        'HEARTS': 0x20,
        'CLUBS': 0x30,
        'DIAMONDS': 0x40}

POINT = {
        'A': 0x01,
        '2': 0x02,
        '3': 0x04,
        '4': 0x05,
        '5': 0x06,
        '6': 0x06,
        '7': 0x07,
        '8': 0x08,
        '9': 0x09,
        '10': 0x0a,
        'J': 0x0b,
        'Q': 0x0c,
        'K': 0x0d
        }


db = sqlite3.connect('../example.db')
cursor = db.cursor()
db.close()
messager = None
msg_queue = queue.Queue()
exit = threading.Event()

class Messager(threading.Thread):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connected = False
    _try_connect_time = 20

    def __init__(self,ip,port,pid, connect=False):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.pid = pid
        self.conn.bind((ip,port))
        #TODO:
        if connect:
            self.connect()

    def connect(self,ip,port):
        try_count = 0
        while True:
            try:
                self.conn.connect((ip,port))
                break
            except Exception as e:
                print(e)
                print('connect to %s failed, retrying...'%(ip))
                try_count += 1
                if try_count > self._try_connect_time:
                    print("Reached max connect time %d, exiting."%(self._try_connect_time))
                    return False
                sleep(1)
        print("connect to server %s:%d success."%(ip,port))
        self.connected = True
        if self.register():
            return True
        else:
            return False

    def register(self):
        if self.connected:
            reg_msg = "reg: " + str(self.pid) + " " + "test" + "\n"
            print(reg_msg,end='')
            self.conn.send(reg_msg.encode())
            return True
        else:
            print("Must connect to a server before registering.")
            return False

    def run(self):
        while True:
            try:
                msg = self.conn.recv(1024)
                if msg:
                    msg = process_msg(msg.decode())
                else:
                    print("Server disconnected.")
                    exit.set()
                    sys.exit()
            except Exception as e:
                print(e)
                sys.exit()
        return None

    def send(self, msg):
        if self.connected:
            self.conn.send(msg.encode())
        else:
            print("Not connected to the server")
            sys.exit()

class Message():
    def __init__(self,name,content):
        self.name = name
        self.content = content

    def __repr__(self):
        return "<"+self.name+">\n"+self.content+"</"+self.name+">"

def process_msg(msg):
    msg = msg.strip()
    print("===the next msg===")
    print(msg)
    if "game-over" in msg:
        exit.set()
        sys.exit()
    msg_re = re.compile("(?P<type>seat|blind|hold|inquire|flop|turn|river|showdown|pot-win)\/(?P<info>[\s\S]+)\/(?P=type)")
    matches = msg_re.finditer(msg)
    for match in matches:
        info_type = match.group("type").strip()
        info_content = match.group("info").strip()
        msg = Message(info_type, info_content)
        msg_queue.put(msg)
    return msg
    '''
    else:
        print("un recognized message: \n%s"%(msg))
        return None
    '''



class PlayerState():
    def __init__(self,name):
        self.name = name

    def check_msg(self,msg):
        pass

    def do_actions(self):
        pass

    def entry_actions(self):
        pass

    def exit_actions(self):
        pass

class PrepareState(PlayerState):
    def __init__(self, player):
        PlayerState.__init__(self,"prepare")
        self.player = player

class ReadyState(PlayerState):
    def __init__(self, player):
        PlayerState.__init__(self,"ready")
        self.player = player

    def check_msg(self, msg):
        if "seat" == msg.name:
            print(">sit")
            game = self.player.game
            game.seats.clear()
            seats = msg.content.split('\n')
            num_seats = len(seats)
            for i in range(num_seats):
                seat = seats[i]
                if ':' in seat:
                    seat = seat.split(':')[-1].strip()
                pid, jetton, money = seat.split(' ')
                if pid == self.player.pid:
                    self.player.seat = i
                game.seats.append({'pid':pid,
                        'jetton':jetton,
                        'money':money
                        })
                #TODO:            game.print_seats()
            return None
        elif msg.name == "blind":
            print(">blind")
            return None
        elif msg.name == "hold":
            print(">hold")
            cards = msg.content.split('\n')
            for i in range(2):
                card = cards[i].strip()
                color,point = card.split(' ')
                self.player.cards[i] = COLOR[color]+POINT[point]
            print(self.player.cards)
            return "hold"

class HoldState(PlayerState):
    def __init__(self, player):
        PlayerState.__init__(self,"hold")
        self.player = player

    def check_msg(self, msg):
        if "inquire" == msg.name:
            print(">inquire")
            self.player.fold()
            return "ready"
        elif "flop" == msg.name:
            print(">flop\n")
            cards = msg.content.split('\n')
            for i in range(3):
                card = cards[i].strip()
                color,point = card.split(' ')
                self.player.game.flop[i] = COLOR[color]+POINT[point]
            print(self.player.game.flop)
            return "flop"

class FlopState(PlayerState):
    def __init__(self, player):
        PlayerState.__init__(self,"flop")
        self.player = player

    def check_msg(self, msg):
        if "inquire" == msg.name:
            print(">inquire")
            self.player.hold()
            return "ready"
        elif "turn" == msg.name:
            print(">turn\n")
            card = msg.content.strip()
            color, point = card.split(' ')
            self.player.game.turn = COLOR[color] + POINT[point]
            print(self.player.game.turn)
            return "turn"
        else:
            pass

class TurnState(PlayerState):
    def __init__(self, player):
        PlayerState.__init__(self,"turn")
        self.player = player

    def check_msg(self, msg):
        if "inquire" == msg.name:
            print(">inquire")
            pass
        elif "river" == msg.name:
            print(">river")
            card = msg.content.strip()
            color, point = card.split(' ')
            self.player.game.river = COLOR[color] + POINT[point]
            print(self.player.game.river)
            return "river"
        else:
            pass

class RiverState(PlayerState):
    def __init__(self, player):
        PlayerState.__init__(self,"river")
        self.player = player

    def check_msg(self, msg):
        if "inquire" == msg.name:
            print("inquire")
            pass
        elif "showdown" == msg.name:
            print("showdown")
            pass
        elif "pot-win" == msg.name:
            print("pot-win")
            return "ready"

class Game():
    _round = 0
    num_players = 0
    seats = []
    flop = [0x00,
            0x00,
            0x00]
    turn = [0x00]
    river = [0x00]
    pass



class Player():
    cards = [0x00,0x00]
    messager = None
    seat = None
    def __init__(self,pid, game):
        self.pid = pid
        self.game = game
        self.states = {}
        self.active_state = None
        prepare_state = PrepareState(self)
        ready_state = ReadyState(self)
        hold_state = HoldState(self)
        flop_state = FlopState(self)
        turn_state = TurnState(self)
        river_state = RiverState(self)
        self.add_state(prepare_state)
        self.add_state(ready_state)
        self.add_state(hold_state)
        self.add_state(flop_state)
        self.add_state(turn_state)
        self.add_state(river_state)
        self.set_state("prepare")

    def add_state(self, state):
        self.states[state.name] = state

    def process(self,msg):
        if self.active_state is None:
            return
        new_state_name = self.active_state.check_msg(msg)
        if new_state_name is not None:
            self.set_state(new_state_name)

    def set_state(self, new_state_name):
        if self.active_state is not None:
            self.active_state.exit_actions()
        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()

    def fold(self):
        if messager:
            messager.send('fold \n')


def main():
    global messager
    parser = argparse.ArgumentParser(description='The game player.')
    parser.add_argument('server_ip',)
    parser.add_argument('server_port',type=int)
    parser.add_argument('player_ip')
    parser.add_argument('player_port',type=int)
    parser.add_argument('id',type=int)

    args = parser.parse_args()
    print(args)
    server ={'ip':args.server_ip,
            'port':args.server_port
            }

    game = Game()
    player = Player(args.id, game)
    messager = Messager(args.player_ip, args.player_port, args.id)
    messager.connect(**server)
    player.set_state("ready")
    player.messager = messager
    messager.start()
    while not exit.is_set():
        if msg_queue.empty():
            continue
        else:
            msg = msg_queue.get()
        #msg = process_msg(msg)
            player.process(msg)


if __name__ == "__main__":
    main()
