#!/usr/bin/python
#!encoding=utf-8
from __future__ import print_function,unicode_literals,division
import sys
print(sys.version)
is_py2 = (sys.version[0] == '2')
is_py3 = (sys.version[0] == '3')
if is_py2:
    range = xrange
    import Queue as queue
elif is_py3:
    import queue
import socket
import argparse
from time import sleep
import re
import sys
import sqlite3
import threading
from holdme import Card,Hand,deck
from strategy import PreFlopLoose,FlopLoose,TurnLoose,RiverLoose,make_cache,CACHE
import logging

logging.basicConfig(filename="game.log",level=logging.DEBUG)

COLOR = {
        'SPADES': 'S',
        'HEARTS': 'H',
        'CLUBS': 'C',
        'DIAMONDS': 'D'}

POINT = {
        'A': 'A',
        '2': '2',
        '3': '3',
        '4': '4',
        '5': '5',
        '6': '6',
        '7': '7',
        '8': '8',
        '9': '9',
        '10': 'T',
        'J': 'J',
        'Q': 'Q',
        'K':'K',
        }


db = sqlite3.connect('../example.db')
cursor = db.cursor()
db.close()
messager = None
msg_queue = queue.Queue()
exit = threading.Event()

def toCard(msg):
    color,point = msg.split(' ')
    return Card(POINT[point]+COLOR[color])

'''
class Pot():

    def __init__(self):
        self.jetton = 0
        self.bet = 0
        self.actors = []

    def big_blind(self,num):
        self.jetton += num
        self.bet = num

    def small_blind(self,num):
        self.jetton += num
        if self.bet < num:
            self.bet = 2*num

    def raise(self,num):
        self.jetton += num
        self.bet += num

    def call(self,num):
        self.jetton += num
'''

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
                    exit.set()
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
                    print("recv:\n",msg)
                else:
                    print("Server disconnected.Exiting...")
                    sleep(1)
                    exit.set()
                    sys.exit()
            except Exception as e:
                print(e)
                sys.exit()
        return None

    def _send(self, msg):
        if self.connected:
            self.conn.send(msg.encode())
            print("send:",msg)
        else:
            print("Not connected to the server")
            sys.exit()

    def send(self,msg):
        # TO BE DEPRETED
        self._send(msg)

    def check(self):
        self._send("check \n")

    def call(self):
        self._send("call \n")

    def raise_(self,num):
        self._send("raise "+str(num)+" \n")

    def all_in(self):
        self._send("all_in \n")

    def fold(self):
        self._send("fold \n")

class Message():
    def __init__(self,name,content):
        self.name = name
        self.content = content

    def __repr__(self):
        return "<"+self.name+">\n"+self.content+"</"+self.name+">"

def process_msg(msg):
    msg = msg.strip()
    #print("===the next msg===")
    #print(msg)
    if "game-over" in msg:
        print("game over")
        sleep(1)
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

def process_inquire(state, msg):
    m_pot = re.search("total pot: (?P<pot>\d+)",msg.content)
    if m_pot:
        pot = int(m_pot.group("pot"))
        state.game.set_pot(pot)
    else:
        print("can't find total pot in \n============",msg.content,"\n================")

    m_actions = re.finditer("(?P<pid>\d+) (?P<jetton>\d+) (?P<money>\d+) (?P<bet>\d+) (?P<action>blind|check|call|raise|all_in|fold)",msg.content)
    for m in m_actions:
        pid = int(m.group("pid"))
        jetton = int(m.group("jetton"))
        money = int(m.group("money"))
        bet = int(m.group("bet"))
        action = m.group("action")
        if state.game.bet < bet:
            state.game.set_bet(bet)
        print(pid,jetton,money,bet,action)
        if state.player.pid == pid:
            if state.player.bet != bet:
                print("Warning: bet number did't match!")
                print("player bet:",state.player.bet)
                print("server bet:",bet)
        else:
            oppnent = state.game.players[pid]
            act = getattr(oppnent,'act_'+action)
            act(bet)
    pass


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
        self.game = player.game

class ReadyState(PlayerState):
    def __init__(self, player):
        PlayerState.__init__(self,"ready")
        self.player = player
        self.game = player.game

    def check_msg(self, msg):
        game = self.player.game
        if "seat" == msg.name:
            print(">sit")
            del game.seats[:]
            game.round_ += 1
            seats = msg.content.split('\n')
            num_seats = len(seats)
            game.num_players = num_seats
            game.active_players.clear()
            for i in range(num_seats):
                seat = seats[i]
                if ':' in seat:
                    seat = seat.split(':')[-1].strip()
                print(seat)
                seat = seat.strip()
                pid, jetton, money = seat.split(' ')
                pid = int(pid)
                jetton = int(jetton)
                money = int(money)
                game.active_players.add(pid)
                if self.player.is_self(pid):
                    self.player.sit(i,jetton,money)
                else:
                    if game.is_round(1):
                        opponent = Player(pid,game)
                    else:
                        opponent = game.players[pid]
                    opponent.sit(i,jetton,money)
                game.seats.append({'pid':pid,
                        'jetton':jetton,
                        'money':money
                        })
            game.sit()
            print(game.active_players)
            game.print_seats()
            return None
        elif msg.name == "blind":
            print(">blind")
            blinds = msg.content.split('\n')
            pid, bet = blinds[0].split(':')
            pid=int(pid)
            bet=int(bet)
            game.small_blind = bet
            game.set_bet(bet)
            game.add_bet(bet)
            if pid == self.player.pid:
                self.player.bet = bet
            if len(blinds) == 2:
                pid, bet = blinds[1].split(':')
                pid = int(pid)
                bet = int(bet)
                game.big_blind = bet
                game.set_bet(bet)
                game.add_bet(bet)
                if pid == self.player.pid:
                    self.player.bet = bet
            return None
        elif msg.name == "hold":
            print(">hold")
            cards = msg.content.split('\n')
            for i in range(2):
                card = cards[i].strip()
                self.player.cards[i] = toCard(card)
            print(self.player.cards)
            return "hold"

class HoldState(PlayerState):
    def __init__(self, player):
        PlayerState.__init__(self,"hold")
        self.player = player
        self.game = player.game

    def check_msg(self, msg):
        if "inquire" == msg.name:
            print(">inquire")
            process_inquire(self,msg)
            strategy = PreFlopLoose(self.game,self.player)
            strategy.act()
        elif "flop" == msg.name:
            print(">flop\n")
            cards = msg.content.split('\n')
            for i in range(3):
                card = cards[i].strip()
                self.player.game.flop[i] = toCard(card)
            print(self.player.game.flop)
            #make_cache(self.game.flop,self.player.cards)
            return "flop"
        elif "pot-win" == msg.name:
            return "ready"

class FlopState(PlayerState):
    def __init__(self, player):
        PlayerState.__init__(self,"flop")
        self.player = player
        self.game = player.game

    def check_msg(self, msg):
        if "inquire" == msg.name:
            print(">inquire")
            process_inquire(self,msg)
            strategy = FlopLoose(self.game,self.player)
            strategy.act()
        elif "turn" == msg.name:
            print(">turn\n")
            card = msg.content.strip()
            self.player.game.turn = toCard(card)
            print(self.player.game.turn)
            #make_cache(self.game.flop+[self.game.turn],self.player.cards)
            return "turn"
        elif "pot-win" == msg.name:
            return "ready"
        else:
            pass

class TurnState(PlayerState):
    def __init__(self, player):
        PlayerState.__init__(self,"turn")
        self.player = player
        self.game = player.game

    def check_msg(self, msg):
        if "inquire" == msg.name:
            print(">inquire")
            process_inquire(self,msg)
            strategy = TurnLoose(self.game,self.player)
            strategy.act()
            pass
        elif "river" == msg.name:
            print(">river")
            card = msg.content.strip()
            self.player.game.river = toCard(card)
            print(self.player.game.river)
            #make_cache(self.game.flop+[self.game.turn,self.game.river],self.player.cards)
            return "river"
        elif "pot-win" == msg.name:
            return "ready"
        else:
            pass

class RiverState(PlayerState):
    def __init__(self, player):
        PlayerState.__init__(self,"river")
        self.player = player
        self.game = player.game

    def check_msg(self, msg):
        if "inquire" == msg.name:
            print(">inquire")
            process_inquire(self,msg)
            strategy = RiverLoose(self.game,self.player)
            strategy.act()
            pass
        elif "showdown" == msg.name:
            print(">showdown")
            pass
        elif "pot-win" == msg.name:
            print(">pot-win")
            return "ready"

class Game():
    round_ = 0
    active_players = set()
    num_active_players = 0
    seats = []
    players = {}
    flop = [None, None, None]
    turn = None
    river = None
    pot = 0
    bet = 0
    raise_bet = 0

    @property
    def community(self):
        for c in self.flop:
            if not c:
                return None
        cards = self.flop
        if self.turn:
            cards = cards + [self.turn]
        if self.river:
            cards = cards + [self.river]
        return cards

    def sit(self):
        self.pot = 0
        self.bet = 0
        self.raise_bet = 0
        self.turn = None
        self.river = None
        print(type(self.seats))
        self.num_active_players = len(self.seats)

    def print_seats(self):
        print("pid  jetton  money")
        for seat in self.seats:
            print(seat['pid'],seat['jetton'],seat['money'])

    def raise_(self, num):
        self.bet += num

    def add_bet(self, num):
        self.pot += num

    def set_pot(self, pot):
        if type(pot) != int:
            raise Exception
        self.pot = pot

    def set_bet(self, bet):
        self.bet = bet

    def is_round(self, num):
        if self.round_ == num:
            return True
        else:
            return False


class Player():
    cards = [None,None]
    seat = None
    bet = 0
    jetton = 0
    money = 0

    def __init__(self,pid,game):
        self.pid = pid
        self.game = game
        self.game.players[self.pid] = self
        self.out = False

    def sit(self, seat, jetton,money):
        self.bet = 0
        self.seat = seat
        self.jetton = jetton
        self.money = money

    def set_bet(self, bet):
        self.bet = bet

    def act_blind(self, bet):
        self.bet = bet

    def act_call(self, bet):
        self.bet = self.game.bet
        pass

    def act_fold(self, bet):
        self.set_bet(0)
        if self.pid in self.game.active_players:
            self.game.num_active_players -= 1
            self.game.active_players.remove(self.pid)
        pass

    def act_check(self, bet):
        pass

    def act_raise(self,bet):
        raise_bet = bet - self.bet #raise number
        if self.game.raise_bet < raise_bet:
            self.game.raise_bet = raise_bet
        self.bet = bet

    def act_all_in(self,bet):
        if bet!= self.jetton:
            print("Warning! The bet number didn't match!")
            raise Exception
        self.bet = self.jetton

class Snowden(Player):
    messager = None
    def __init__(self,pid, game):
        self.pid = pid
        self.game = game
        self.game.players[self.pid] = self
        self.out = False
        self.states = {}
        self.active_state = None
        self.bet = 0
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

    @property
    def pot_odds(self):
        return self.game.bet/(self.game.bet+self.game.pot)

    def is_self(self,pid):
        if self.pid == pid:
            return True
        else:
            return False

    def add_state(self, state):
        self.states[state.name] = state

    def process(self,msg):
        if self.active_state is None:
            return
        new_state_name = self.active_state.check_msg(msg)
        print("current state:",self.active_state.name)
        print("next state:",new_state_name)
        if new_state_name is not None:
            self.set_state(new_state_name)

    def set_state(self, new_state_name):
        if self.active_state is not None:
            self.active_state.exit_actions()
        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()

    #TODO: check bet and actions
    def fold(self):
        self.messager.send('fold \n')
        print("fold")
        self.set_state("ready")

    def check(self):
        if self.bet >= self.game.bet:
            self.messager.check()
        else:
            self.call()

    def call(self):
        if self.bet < self.game.bet:
            if self.jetton > self.game.bet:
                self.messager.call()
                self.bet = self.game.bet
                print("call:",self.game.bet)
            else:
                self.messager.all_in()
        elif self.bet == self.game.bet:
            self.check()
        else:
            print("Warning: bet didn't match")
            print("player bet:",self.bet)
            print("game bet:",self.game.bet)
            raise Exception

    def raise_(self,num):
        if self.jetton > (num+self.bet):
            self.messager.raise_(num)
            self.bet += num
            print("raise:",num,"current bet:",self.game.bet)
        else:
            self.all_in()

    def all_in(self):
        self.messager.all_in()
        self.bet += self.jetton
        print("all in:",self.jetton,"current bet:",self.game.bet)

    def pre_flop_bet(self):
        strategy = PreFlopLoose(self.game,self)
        strategy.act()

    def action(self):
        self.call()


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
    player = Snowden(args.id, game)
    messager = Messager(args.player_ip, args.player_port, args.id)
    messager.connect(**server)
    player.set_state("ready")
    player.messager = messager
    try:
        messager.start()
        while not exit.is_set():
            if msg_queue.empty():
                continue
            else:
                msg = msg_queue.get()
            #msg = process_msg(msg)
                player.process(msg)
    except (KeyboardInterrupt, SystemExit):
          print('\n! Received keyboard interrupt, quitting threads.\n')

if __name__ == "__main__":
    main()
