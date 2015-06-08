#!/usr/bin/python
#!encoding=utf-8
from __future__ import print_function,unicode_literals,division
import sys
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
#from holdme import Card,deck,score5 as score5,score7
from utils import Card, deck, cal_score, prob_best, prob_best_after_flop, prob_best_after_turn
from random import random,randint

RANKS = '23456789TJQKA'
SUITS = 'CHSD'

HOLE_CARDS = {1:['AA','KK','QQ'],
        2:['JJ','AKs','TT','AQs','AJs','KQs','AKo'],
        3:['99','ATs','KJs','QJs','JTs','AQo'],
        4:['88','KTs','QTs','J9s','T9s','98s','AJo','KQo'],
        5:['77','A9s','A8s','A7s','A6s','A5s','A4s','A3s','A2s','Q9s','T8s','97s','87s','76s','KJo','QJo','JTo'],
        6:['66','55','K9s','J8s','86s','75s','54s','ATo','KTo','QTo'],
        7:['44','33','22','K8s','K7s','K6s','K5s','K4s','K3s','K2s','Q8s','T7s','64s','53s','43s','J9o','T9o','98o'],
        8:['J7s','96s','85s','74s','42s','32s','A9o','K9o','Q9o','J8o','T8o','87o','76o','65o','54o']}


PHIL = {1:['AA','KK','QQ'],
        2:['JJ','TT','99','AKs','AK'],
        3:['88','77','AQs','AQ',],
        4:['66','55','44','33','22','AJs','ATs','A9s','A8s'],
        5:['A7s','A6s','A5s','A4s','A3s','A2s','KQs','KQ'],
        6:['QJs','JTs','T9s','98s','87s','76s','65s']
        }


TEST_TIME = 3000 #概率计算次数
CALL_BET_PRE_FLOP = 150 #翻牌前弱牌最大跟注金额
RAISE_BET_PRE_FLOP = 300 #翻牌前与对方火拼的最大注额
PROB_IN_STANDBY = 0.92 #极度消极策略中加注的最低胜率
FOLDABLE = 110#消极策略中盖牌的对方加注额

TOTAL_ROUND = 600
CACHE = {}

#TODO: opponents' player style

class HoleCards():
    MAX_TIER = 100

    def __init__(self,card_a,card_b):
        self.a = card_a
        self.b = card_b

    @property
    def suits(self):
        if self.a.suit == self.b.suit:
            return 's'
        else:
            return 'o'

    @property
    def ranks(self):
        if self.a.rank >= self.b.rank:
            return RANKS[self.a.rank] + RANKS[self.b.rank]
        else:
            return RANKS[self.b.rank] + RANKS[self.a.rank]

    def tier(self,table=HOLE_CARDS):
        for i in table:
            if self.is_tier(i,table):
                return i
        return self.MAX_TIER

    def is_tier(self,i,table):
        if self.ranks in table[i] or self.ranks+self.suits in table[i]:
            return True
        return False



class Master():
    preflop = {}
    flop = {}
    turn = {}
    river = {}
    style = None

    def __init__(self, game, player):
        self.game = game
        self.player = player
        self.style = "loose"

    # Add strategies

        self.preflop['loose'] = PreFlopLoose(game, player)
        self.preflop['tightpassive'] = PreFlopTightPassive(game, player)
        self.preflop['standby'] = PreFlopStandBy(game, player)
        self.preflop['tightaggressive'] = PreFlopTightAggressive(game, player)

        self.flop['loose'] = FlopLoose(game, player)
        self.flop['tightpassive'] = FlopTightPassive(game, player)
        self.flop['standby'] = FlopStandBy(game, player)
        self.flop['tightaggressive'] = FlopTightAggressive(game, player)

        self.turn['loose'] = TurnLoose(game, player)
        self.turn['tightpassive'] = TurnTightPassive(game, player)
        self.turn['standby'] = TurnStandBy(game, player)
        self.turn['tightaggressive'] = TurnTightAggressive(game, player)

        self.river['loose'] = RiverLoose(game, player)
        self.river['tightpassive'] = RiverTightPassive(game, player)
        self.river['standby'] = RiverStandBy(game, player)
        self.river['tightaggressive'] = RiverTightAggressive(game, player)

    def switch(self,style):
        self.style = style

    def pre_action(self):
        #if self.game.num_players <= 4:
        #    self.switch("loose")
        if self.can_stand_by():
            self.switch("standby")
        else:
            self.switch("tightaggressive")
        #self.switch("tightaggressive")

    def preflop_act(self):
        self.pre_action()
        self.preflop[self.style].act()
        pass

    def flop_act(self):
        self.pre_action()
        self.flop[self.style].act()
        pass

    def turn_act(self):
        self.pre_action()
        self.turn[self.style].act()
        pass

    def river_act(self):
        self.pre_action()
        self.river[self.style].act()
        pass

    def can_stand_by(self):
        game = self.game
        player = self.player
        res_round = TOTAL_ROUND - game.round_
        num_alive_players = game.num_players
        print("res round",res_round,"current money",player.money+player.jetton)
        print("rank", player.rank)
        if player.rank <= 4 and ((player.money+player.jetton) - res_round * 1.5 * game.big_blind /num_alive_players) > 4000:
            print("Can live")
            return True
        else:
            print("!!!Can NOT live")
            return False

class Strategy():

    def __init__(self, game, player):
        self.game = game
        self.player = player
        '''
        if player.cards[0] and player.cards[1]:
            self.hole = HoleCards(player.cards[0],player.cards[1])
        else:
            print("Warning! the player must hold 2 cards")
            '''

    def act(self):
        pass

    def learn():
        pass


class PreFlopTightAggressive(Strategy):

    def act(self):
        if self.player.cards[0] and self.player.cards[1]:
            self.hole = HoleCards(self.player.cards[0],self.player.cards[1])
        else:
            print("Warning! the player must hold 2 cards")
        print("active playres:",self.game.num_active_players)
        if self.game.num_players > 6:
            behind = [0, 1, 2]
            middle = [6, 7]
            front = [3, 4, 5]
        elif self.game.num_players > 4:
            behind = [0, 1, 2]
            middle = [5]
            front = [3, 4]
        else:
            behind = [0, 1]
            front = [2]
            middle = [3]
        if self.player.seat in behind: # button and blind
            if self.hole.tier() == 1:
                if self.game.inquire_round > 2:
                    self.player.call()
                    return
                self.player.raise_(self.game.pot/2)
                return
            elif self.hole.tier() in [2, 3, 4]:
                if self.game.inquire_round >= 2:
                    self.player.call()
                    return
                else:
                    if self.game.bet < 200:
                        self.player.raise_(self.game.raise_bet)
                    else:
                        self.player.fold()
                    return
            elif self.hole.tier() in [5, 6, 7]:
                if self.game.inquire_round >= 2:
                    self.player.call()
                    return
                else:
                    if self.game.bet < 100:
                        self.player.raise_(self.game.raise_bet)
                    else:
                        self.player.fold()
                    return
            else:
                self.player.fold()
                return

        elif self.player.seat in middle:
            if self.hole.tier() == 1:
                if self.game.inquire_round > 2:
                    self.player.call()
                    return
                self.player.raise_(self.game.pot/2)
                return
            elif self.hole.tier() in [2, 3]:
                if self.game.inquire_round >= 2:
                    self.player.call()
                    return
                else:
                    if self.game.bet < 200:
                        self.player.raise_(self.game.raise_bet)
                    else:
                        self.player.fold()
                    return
            elif self.hole.tier() in [4,5,6]:
                if self.game.inquire_round >= 2:
                    self.player.call()
                    return
                else:
                    if self.game.bet < 100:
                        self.player.raise_(self.game.raise_bet)
                    else:
                        self.player.fold()
                    return
            else:
                self.player.fold()
                return

        elif self.player.seat in front:
            if self.hole.tier() == 1:
                if self.game.inquire_round > 2:
                    self.player.call()
                    return
                self.player.raise_(self.game.pot/2)
                return
            elif self.hole.tier() in [2, 3]:
                if self.game.inquire_round >= 2:
                    self.player.call()
                    return
                else:
                    if self.game.bet < 200:
                        self.player.raise_(self.game.raise_bet)
                    else:
                        self.player.fold()
                    return
            elif self.hole.tier() in [4,]:
                if self.game.inquire_round >= 2:
                    self.player.call()
                    return
                else:
                    if self.game.bet < 100:
                        self.player.raise_(self.game.raise_bet)
                    else:
                        self.player.fold()
                    return
            else:
                self.player.fold()
                return

class FlopTightAggressive(Strategy):

    def act(self):
        self.hand = Hand(self.game.flop+self.player.cards)
        self.pot_odds = self.player.pot_odds
        print("active playres:",self.game.num_active_players)
        #self.prob_win = prob_win(self.game.flop, self.player.cards, self.game.num_active_players-1,out=True)
        self.prob = prob_best_after_flop(self.game,self.player)
        print("prob best after flop", self.prob)
        print("pot odds", self.pot_odds)
        if self.game.num_players > 6:
            behind = [0, 6, 7]
            middle = [4, 5]
            front = [1, 2, 3]
        elif self.game.num_players > 4:
            front = [1, 2]
            middle = [3, 4]
            behind = [0, 5]
        else:
            front = [1]
            middle = [2, 3]
            behind = [0]

        if self.prob >= 0.9:
            r = random()
            if r>0.2:
                self.player.raise_(self.game.pot*randint(1,10))
            else:
                self.player.call()
            return

        RR = self.prob/self.pot_odds
        if self.player.seat in front:
            if RR > 2.5:
                r = random()
                if r>0.4:
                    self.player.raise_(self.game.raise_bet)
                else:
                    self.player.call()
                return
            elif RR > 1.8:
                r = random()
                if r>0.9:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.2:
                    self.player.call()
                else:
                    self.player.fold()
                return
            elif RR > 1:
                r = random()
                if r>0.95:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.3:
                    self.player.call()
                else:
                    self.player.fold()
                return
            else:
                self.player.fold()
                return
        elif self.player.seat in middle:
            if RR > 2:
                r = random()
                if r>0.4:
                    self.player.raise_(self.game.raise_bet)
                else:
                    self.player.call()
                return
            elif RR > 1.5:
                r = random()
                if r>0.9:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.2:
                    self.player.call()
                else:
                    self.player.fold()
                return
            elif RR > 1:
                r = random()
                if r>0.95:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.3:
                    self.player.call()
                else:
                    self.player.fold()
                return
            else:
                self.player.fold()
                return

        elif self.player.seat in behind:
            if RR > 1.6:
                r = random()
                if r>0.4:
                    self.player.raise_(self.game.raise_bet)
                else:
                    self.player.call()
                return
            elif RR > 1.3:
                r = random()
                if r>0.9:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.2:
                    self.player.call()
                else:
                    self.player.fold()
                return
            elif RR > 1:
                r = random()
                if r>0.95:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.3:
                    self.player.call()
                else:
                    self.player.fold()
                return
            else:
                self.player.fold()
                return

class TurnTightAggressive(Strategy):

    def act(self):
        self.hand = Hand(self.game.flop+self.player.cards)
        self.pot_odds = self.player.pot_odds
        print("active playres:",self.game.num_active_players)
        self.prob = prob_best_after_turn(self.game,self.player)
        print("prob best after flop", self.prob)
        print("pot odds", self.pot_odds)
        if self.game.num_players > 6:
            behind = [0, 6, 7]
            middle = [4, 5]
            front = [1, 2, 3]
        elif self.game.num_players > 4:
            front = [1, 2]
            middle = [3, 4]
            behind = [0, 5]
        else:
            front = [1]
            middle = [2, 3]
            behind = [0]

        if self.prob >= 0.9:
            r = random()
            if r>0.2:
                self.player.raise_(self.game.pot*randint(1,10))
            else:
                self.player.call()
            return

        RR = self.prob/self.pot_odds
        if self.player.seat in front:
            if RR > 2.5:
                r = random()
                if r>0.4:
                    self.player.raise_(self.game.raise_bet)
                else:
                    self.player.call()
                return
            elif RR > 1.8:
                r = random()
                if r>0.9:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.2:
                    self.player.call()
                else:
                    self.player.fold()
                return
            elif RR > 1:
                r = random()
                if r>0.95:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.3:
                    self.player.call()
                else:
                    self.player.fold()
                return
            else:
                self.player.fold()
                return
        elif self.player.seat in middle:
            if RR > 2:
                r = random()
                if r>0.4:
                    self.player.raise_(self.game.raise_bet)
                else:
                    self.player.call()
                return
            elif RR > 1.5:
                r = random()
                if r>0.9:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.2:
                    self.player.call()
                else:
                    self.player.fold()
                return
            elif RR > 1:
                r = random()
                if r>0.95:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.3:
                    self.player.call()
                else:
                    self.player.fold()
                return
            else:
                self.player.fold()
                return

        elif self.player.seat in behind:
            if RR > 1.6:
                r = random()
                if r>0.4:
                    self.player.raise_(self.game.raise_bet)
                else:
                    self.player.call()
                return
            elif RR > 1.3:
                r = random()
                if r>0.9:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.2:
                    self.player.call()
                else:
                    self.player.fold()
                return
            elif RR > 1:
                r = random()
                if r>0.95:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.3:
                    self.player.call()
                else:
                    self.player.fold()
                return
            else:
                self.player.fold()
                return


class RiverTightAggressive(Strategy):

    def act(self):
        self.hand = Hand(self.game.flop+self.player.cards)
        self.pot_odds = self.player.pot_odds
        print("active playres:",self.game.num_active_players)
        self.prob = prob_best(self.game,self.player)
        print("prob best after flop", self.prob)
        print("pot odds", self.pot_odds)
        if self.game.num_players > 6:
            behind = [0, 6, 7]
            middle = [4, 5]
            front = [1, 2, 3]
        elif self.game.num_players > 4:
            front = [1, 2]
            middle = [3, 4]
            behind = [0, 5]
        else:
            front = [1]
            middle = [2, 3]
            behind = [0]

        if self.prob >= 0.9:
            r = random()
            if r>0.2:
                self.player.raise_(self.game.pot*randint(1,10))
            else:
                self.player.call()
            return

        RR = self.prob/self.pot_odds
        if self.player.seat in front:
            if RR > 2.5:
                r = random()
                if r>0.4:
                    self.player.raise_(self.game.raise_bet)
                else:
                    self.player.call()
                return
            elif RR > 1.8:
                r = random()
                if r>0.9:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.2:
                    self.player.call()
                else:
                    self.player.fold()
                return
            elif RR > 1:
                r = random()
                if r>0.95:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.3:
                    self.player.call()
                else:
                    self.player.fold()
                return
            else:
                self.player.fold()
                return
        elif self.player.seat in middle:
            if RR > 2:
                r = random()
                if r>0.4:
                    self.player.raise_(self.game.raise_bet)
                else:
                    self.player.call()
                return
            elif RR > 1.5:
                r = random()
                if r>0.9:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.2:
                    self.player.call()
                else:
                    self.player.fold()
                return
            elif RR > 1:
                r = random()
                if r>0.95:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.3:
                    self.player.call()
                else:
                    self.player.fold()
                return
            else:
                self.player.fold()
                return

        elif self.player.seat in behind:
            if RR > 1.6:
                r = random()
                if r>0.4:
                    self.player.raise_(self.game.raise_bet)
                else:
                    self.player.call()
                return
            elif RR > 1.3:
                r = random()
                if r>0.9:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.2:
                    self.player.call()
                else:
                    self.player.fold()
                return
            elif RR > 1:
                r = random()
                if r>0.95:
                    self.player.raise_(self.game.raise_bet)
                elif r>0.3:
                    self.player.call()
                else:
                    self.player.fold()
                return
            else:
                self.player.fold()
                return


class PreFlopLoose(Strategy):
    play_tier = 5 #PLAYTIER
    raise_tier = 1 #RAISETIER

    def act(self):
        if self.player.cards[0] and self.player.cards[1]:
            self.hole = HoleCards(self.player.cards[0],self.player.cards[1])
        else:
            print("Warning! the player must hold 2 cards")
        print("active playres:",self.game.num_active_players)
        if self.game.num_active_players == 1:
            self.player.call()
            return
        if self.game.bet > 200:
            self.player.fold()
            return
        elif self.hole.tier() <= 8:
            self.player.all_in()
            return
        else:
            self.player.fold()
            return

class FlopLoose(Strategy):
    plable_lev = 1

    def __init__(self,game, player):
        Strategy.__init__(self, game, player)
        #self.prob = self.hand.cal_prob(self.plable_lev)
        #self.prob_win = prob_win(game.cards, player.cards, game.alive_oponents)

    def act(self):
        self.hand = Hand(self.game.flop+self.player.cards)
        self.pot_odds = self.player.pot_odds
        print("active playres:",self.game.num_active_players)
        #self.prob_win = prob_win(self.game.flop, self.player.cards, self.game.num_active_players-1,out=True)
        self.prob = prob_best_after_flop(self.game,self.player)
        print("prob best after flop", self.prob)
        print("pot odds", self.pot_odds)
        if self.game.num_active_players <=4 :
            if self.prob >= 0.8:
                self.player.all_in()
                return
        RR = self.prob/self.pot_odds
        if RR > 1.3:
            if self.game.round_ >= 3:
                self.player.call()
                return
            else:
                self.player.raise_(self.game.raise_bet)
                return
        elif RR > 1:
            #self.player.raise_(self.game.raise_bet)
            self.player.call()
            #or call
        else:
            self.player.fold()

class TurnLoose(Strategy):
    plable_lev = 1

    def __init__(self, game, player):
        Strategy.__init__(self, game, player)

    def act(self):
        cards = self.game.flop + self.player.cards
        cards.append(self.game.turn)
        self.hand = Hand(cards)
        self.pot_odds = self.player.pot_odds
        print("active playres:",self.game.num_active_players)
        #self.prob_win = prob_win(self.game.flop+[self.game.turn], self.player.cards, self.game.num_active_players-1,out=True)
        self.prob = prob_best_after_turn(self.game,self.player)
        print("prob best after turn", self.prob)
        print("pot odds", self.pot_odds)
        if self.game.num_active_players <=4 :
            if self.prob >= 0.8:
                self.player.all_in()
                return
        RR = self.prob/self.pot_odds
        if RR > 1.3:
            self.player.raise_(self.game.raise_bet)
        elif RR > 1:
            #self.player.raise_(self.game.raise_bet)
            self.player.call()
            #or call
        elif self.game.raise_bet < 200:
            self.player.check()
        else:
            self.player.fold()


class RiverLoose(Strategy):

    def __init__(self, game, player):
        Strategy.__init__(self, game, player)

    def act(self):
        cards = self.game.community
        self.hand = Hand(cards)
        self.pot_odds = self.player.pot_odds
        print("active playres:",self.game.num_active_players)
        #self.prob_win = prob_win(self.game.flop+[self.game.turn,self.game.river], self.player.cards, self.game.num_active_players-1)
        #hand = Hand(self.game.community+self.player.cards)
        self.prob = prob_best(self.game,self.player)
        print("prob best after river", self.prob)
        print("pot odds", self.pot_odds)
        if self.prob > self.pot_odds or self.prob > (1/self.game.num_active_players):
            self.player.call()
            return
        else:
            self.player.fold()

        '''
        if self.game.num_active_players == 2:
            if hand.prob >= 0.5:
                self.player.all_in()
            elif hand.prob >= self.pot_odds:
                self.player.raise_(self.game.raise_bet)
            else:
                self.player.call()
        elif 3 <= self.game.num_active_players and self.game.num_active_players <=4:
            if hand.lev >= 3:
                self.player.all_in()
            elif hand.lev >=2:
                self.player.check()
            else:
                self.player.fold()
        else:
            if hand.lev >=4:
                self.player.call()
            else:
                self.player.fold()
        self.prob = prob(self.game,self.player)
        if self.prob > self.pot_odds:
            if self.game.bet < 300:
                self.player.raise_(self.game.raise_bet)
            else:
                self.player.call()
            #or call
        else:
            self.player.fold()
        '''

def bluffable(game,player):
    return False

def bluff(game,player):
    self.player.all_in()

class PreFlopTightPassive(PreFlopTightAggressive):
    pass
'''
class PreFlopTightPassive(Strategy):

    def act(self):
        if self.player.cards[0] and self.player.cards[1]:
            self.hole = HoleCards(self.player.cards[0],self.player.cards[1])
        else:
            print("Warning! the player must hold 2 cards")
        print("active playres:",self.game.num_active_players)
        if self.game.num_active_players == 1:
            self.player.call()
        if self.game.num_active_players == 2:
            if self.game.raise_bet < CALL_BET_PRE_FLOP:
                if self.hole.tier():
                    self.player.call()
                    return
                else:
                    self.player.fold()
                    return
            else:
                if self.hole.tier() == 1:
                    self.player.call()
                    return
                else:
                    self.player.fold()
                    return

        elif self.game.num_active_players == 3 or self.game.num_active_players == 4:
            if self.hole.tier():
                if self.hole.tier() <= 1:
                    r = random()
                    if r>0.2:
                        self.player.raise_(self.game.raise_bet*randint(1,10))
                        return
                    else:
                        self.player.call()
                        return
                elif self.hole.tier() <= 3:
                    r = random()
                    if r>0.2*self.hole.tier():
                        self.player.raise_(self.game.raise_bet)
                        return
                    else:
                        self.player.fold()
                        return
                elif self.hole.tier() <= 5 and self.game.raise_bet < CALL_BET_PRE_FLOP:
                    r = random()
                    if r>0.5:
                        self.player.raise_(self.game.raise_bet)
                    else:
                        self.player.fold()
                elif self.game.raise_bet < CALL_BET_PRE_FLOP:
                    r = random()
                    if r>0.9:
                        print("raise bet",self.game.raise_bet)
                        self.player.raise_(self.game.raise_bet)
                        return
                    else:
                        self.player.fold()
                        return
                else:
                    self.player.fold()
                    return
            else:
                self.player.fold()
                return
            pass

        elif self.game.num_active_players <= 6:
            if self.hole.tier():
                if self.hole.tier() <=1:
                    self.player.call()
                elif self.hole.tier() and self.game.raise_bet < CALL_BET_PRE_FLOP:
                    r = random()
                    if r>0.2*self.hole.tier():
                        print("raise bet",self.game.raise_bet)
                        self.player.raise_(self.game.raise_bet)
                        return
                    elif r>0.1*self.hole.tier():
                        self.player.fold()
                        return
                    else:
                        self.player.call()
                else:
                    self.player.fold()
            else:
                self.player.fold()
        elif self.game.num_active_players > 6:
            if self.hole.tier():
                if self.hole.tier() == 1:
                    self.player.call()
                elif self.hole.tier() <= 3 and self.game.bet < CALL_BET_PRE_FLOP:
                    self.player.call()
                elif self.hole.tier() and self.game.raise_bet < CALL_BET_PRE_FLOP:
                    r = random()
                    if r>0.5:
                        print("raise bet",self.game.raise_bet)
                        self.player.raise_(self.game.raise_bet)
                        return
                    else:
                        self.player.fold()
                elif self.game.bet < CALL_BET_PRE_FLOP:
                    r = random()
                    if r>0.99:
                        print("raise bet",self.game.raise_bet)
                        self.player.raise_(self.game.raise_bet)
                        return
                    else:
                        self.player.fold()
                else:
                    self.player.fold()
'''

class FlopTightPassive(Strategy):
    plable_lev = 1

    def __init__(self,game, player):
        Strategy.__init__(self, game, player)
        #self.prob = self.hand.cal_prob(self.plable_lev)
        #self.prob_win = prob_win(game.cards, player.cards, game.alive_oponents)

    def act(self):
        self.hand = Hand(self.game.flop+self.player.cards)
        self.pot_odds = self.player.pot_odds
        print("active playres:",self.game.num_active_players)
        #self.prob_win = prob_win(self.game.flop, self.player.cards, self.game.num_active_players-1,out=True)
        self.prob = prob_best_after_flop(self.game,self.player)
        print("prob best after flop", self.prob)
        print("pot odds", self.pot_odds)
        if self.prob >= 0.9:
            r = random()
            if r>0.2:
                self.player.raise_(self.game.pot)
            else:
                self.player.call()
            return
        if self.game.raise_bet >= FOLDABLE:
            self.player.fold()
            return
        RR = self.prob/self.pot_odds
        if RR > 1.3:
            r = random()
            if r>0.4:
                self.player.raise_(self.game.raise_bet)
            else:
                self.player.call()
            return
        elif RR > 1:
            r = random()
            if r>0.9:
                self.player.raise_(self.game.raise_bet)
            elif r>0.2:
                self.player.call()
            else:
                self.player.fold()
            return
            #or call
        else:
            r = random()
            #TODO: caution enemies
            if r>0.9:
                if bluffable(self.game,self.player):
                    bluff(self.game,self.player)
                    return
                else:
                    self.player.raise_(self.game.pot)
                    return
            elif r>0.7:
                self.player.call()
            else:
                self.player.fold()

class TurnTightPassive(Strategy):
    plable_lev = 1

    def __init__(self, game, player):
        Strategy.__init__(self, game, player)

    def act(self):
        cards = self.game.flop + self.player.cards
        cards.append(self.game.turn)
        self.hand = Hand(cards)
        self.pot_odds = self.player.pot_odds
        print("active playres:",self.game.num_active_players)
        self.prob = prob_best_after_turn(self.game,self.player)
        print("prob best after turn", self.prob)
        print("pot odds", self.pot_odds)
        if self.prob >= 0.9:
            r = random()
            if r>0.7:
                self.player.raise_(self.game.pot*3)
            elif r>0.4:
                self.player.raise_(self.game.pot)
            elif r>0.2:
                self.player.raise_(self.game.raise_bet)
            else:
                self.player.call()
            return

        if self.game.raise_bet >= FOLDABLE:
            self.player.fold()
            return
        RR = self.prob/self.pot_odds
        if RR > 1.3:
            r = random()
            if r>0.8:
                self.player.raise_(self.game.raise_bet)
            else:
                self.player.call()
                return
        elif RR > 1:
            #self.player.raise_(self.game.raise_bet)
            r = random()
            if r>0.9:
                self.player.raise_(self.game.raise_bet)
            elif r>0.2:
                self.player.call()
            else:
                self.player.fold()
            return
            #or call
        else:
            r = random()
            #TODO: caution enemies
            if r>0.9:
                self.player.raise_(self.game.pot)
                return
            elif r>0.7:
                self.player.call()
            else:
                self.player.fold()
            return


class RiverTightPassive(Strategy):

    def __init__(self, game, player):
        Strategy.__init__(self, game, player)

    def act(self):
        cards = self.game.community
        self.hand = Hand(cards)
        self.pot_odds = self.player.pot_odds
        print("active playres:",self.game.num_active_players)
        self.prob = prob_best(self.game,self.player)
        print("prob best after river", self.prob)
        print("pot odds", self.pot_odds)

        if self.prob >= 0.9:
            r = random()
            if r>0.7:
                self.player.raise_(self.game.pot*3)
            elif r>0.4:
                self.player.raise_(self.game.pot)
            elif r>0.2:
                self.player.raise_(self.game.raise_bet)
            else:
                self.player.call()
            return

        if self.game.raise_bet >= FOLDABLE:
            self.player.fold()
            return

        RR = self.prob/self.pot_odds
        if RR > 1.3:
            r = random()
            if r>0.9:
                self.player.raise_(self.game.raise_bet)
            else:
                self.player.call()
                return
        elif RR > 1:
            #self.player.raise_(self.game.raise_bet)
            r = random()
            if r>0.9:
                self.player.raise_(self.game.raise_bet)
            elif r>0.2:
                self.player.call()
            else:
                self.player.fold()
            return
            #or call
        else:
            r = random()
            #TODO: caution enemies
            if r>0.9:
                self.player.raise_(self.game.pot)
                return
            elif r>0.7:
                self.player.call()
            else:
                self.player.fold()
            return



#极度消极策略
class PreFlopStandBy(Strategy):

    def act(self):
        if self.player.is_big_blind and self.game.bet <= self.game.big_blind:
            self.player.check()
        else:
            self.player.fold()

class FlopStandBy(Strategy):

    def __init__(self,game, player):
        Strategy.__init__(self, game, player)

    def act(self):
        self.hand = Hand(self.game.flop+self.player.cards)
        self.pot_odds = self.player.pot_odds
        print("active playres:",self.game.num_active_players)
        self.prob = prob_best(self.game,self.player)
        print("prob best after flop", self.prob)
        print("pot odds", self.pot_odds)
        if self.game.bet <= self.player.bet:
            self.player.check()
        elif self.prob > PROB_IN_STANDBY:
            self.player.raise_(self.game.raise_bet*randint(1,10))#TODO: specify it
        else:
            self.player.fold()

class TurnStandBy(Strategy):

    def __init__(self, game, player):
        Strategy.__init__(self, game, player)

    def act(self):
        cards = self.game.flop + self.player.cards
        cards.append(self.game.turn)
        self.hand = Hand(cards)
        self.pot_odds = self.player.pot_odds

        print("active playres:",self.game.num_active_players)
        self.prob = prob_best(self.game,self.player)
        print("prob best after turn", self.prob)
        print("pot odds", self.pot_odds)
        if self.game.bet <= self.player.bet:
            self.player.check()
        elif self.prob > PROB_IN_STANDBY:
            self.player.raise_(self.game.raise_bet*randint(1,10))#TODO: specify it
        else:
            self.player.fold()



class RiverStandBy(Strategy):

    def __init__(self, game, player):
        Strategy.__init__(self, game, player)

    def act(self):
        cards = self.game.community
        self.hand = Hand(cards)
        self.pot_odds = self.player.pot_odds

        print("active playres:",self.game.num_active_players)
        self.prob = prob_best(self.game,self.player)
        print("prob best after river", self.prob)
        print("pot odds", self.pot_odds)
        if self.game.bet <= self.player.bet:
            self.player.check()
        elif self.prob > PROB_IN_STANDBY:
            self.player.raise_(self.game.raise_bet*randint(1,10))#TODO: specify it
        else:
            self.player.fold()





def play_prob(game,player):
    '''
    估算这副牌打下去赢的概率
    '''
    hand = Hand(game.community+player.cards)
    prob = hand.cal_prob()
    return prob



def isInsideStraight(cards):
    if len(cards) < 4:
        return None
    masks = [0b10111,0b11011,0b11101]
    s_masks = [0b1000000001011,0b1000000001101,0b1000000001110]
    rank_mask = 0b00001111111111111
    cards_bit = 0x00

    for c in cards:
        cards_bit = cards_bit | (c.bitmask >> 13 * c.suit)
    for i in range(9):
        for m in masks:
            if ((cards_bit >> i) & 0b11111)==m:
                return True
    for m in s_masks:
        if (cards_bit & 0b1000000001111) == m:
            return True
    return False

def cal_prob_after_turn(outs):
    prob = (93*outs - outs*outs)/2162
    return prob

def cal_prob_on_river(outs):
    prob = 1 - (46 - outs)/46
    return prob

def prob_win(community,hole, num_oponent, out=False):
    if out:
        p_win = cal_prob_win_on_out(community, hole, num_oponent)
        return p_win
    else:
        p_win = cal_prob_win(community, hole, num_oponent)
        return p_win

def make_cache(community, hole):
    for i in range(52):
        card = Card.from_index(i)
        if i in range(52):
            continue
        CACHE[i] = cal_prob_gt_cards(community+[card], hole)

def cal_prob_win_on_out(community, hole,num_oponent):
    p_win = 0
    temp = 0
    p_gt = 0
    left_cards_count = 50 - len(community)
    for i in range(52):
        card = Card.from_index(i)
        if i in community:
            continue
        if i in CACHE:
            p_gt = CACHE[i]
        else:
            p_gt = cal_prob_gt_cards(community+[card], hole)
        p_win += (1 - p_gt)**num_oponent
    p_win = p_win/left_cards_count
    return p_win

def cal_prob_win(community,hole, num_oponent):
    p_gt = cal_prob_gt_cards(community, hole)
    p_win = (1 - p_gt)**num_oponent
    return p_win

def cal_prob_gt_cards(community,hole):
    score = cal_score(community+hole)
    return cal_prob_gt_score(community,score)

def cal_prob_gt_score(community,score):
    gt_count = 0
    sum_count = 0
    for i in range(52):
        for j in range(52):
            card_a = Card.from_index(i)
            card_b = Card.from_index(j)
            if card_a in community or card_b in community:
                continue
            expect_score = cal_score(community+[card_a,card_b])
            if expect_score > score:
                gt_count += 1
            sum_count += 1
    return gt_count/sum_count

class Hand():
    def __init__(self, cards):
        self.cards = cards
        num_cards = len(cards)
        if 5 <= num_cards and num_cards <= 7:
            self.score = cal_score(cards)
        else:
            print(cards)
            print(num_cards)
            print("cards number error")
            raise Exception
        self.lev = self.score >> 26
        if num_cards < 7:
            self.cal_outs()

    def cal_outs(self,least_lev=None):
        gt_outs = {1:0,
                2:0,
                3:0,
                4:0,
                5:0,
                6:0,
                7:0,
                8:0}
        num_outs = 0
        if least_lev:
            pass
        else:
            least_lev = self.lev
        for card in deck():
            if card in self.cards:
                continue
            new_cards = self.cards[:]
            new_cards.append(card)
            new_cards_score = cal_score(new_cards)
            new_cards_lev = new_cards_score >> 26
            if new_cards_lev > self.lev:
                for i in range(self.lev+1,new_cards_lev+1):
                    gt_outs[i] += 1
        self.outs = gt_outs
        return gt_outs

    def cal_prob(self,lev=0):
        if not lev:
            lev = self.lev + 1
        if self.num_cards == 5:
            self.prob = cal_prob_after_turn(self.outs[lev])
            return self.prob
        elif self.num_cards == 6:
            self.prob = cal_prob_on_river(self.outs[lev])
            return self.prob
        else:
            return None

    def __repr__(self):
        s = "<Hand:"
        for c in self.cards:
            s = s + repr(c) + ","
        s = s + ">"
        return s

def straight_out(cards):
    for card in deck():
        if card in cards:
            continue
        ncards = cards[:]
        ncards.append(card)
        score = cal_score(ncards)
        type_lev = score >> 26
        if type_lev > 2:
            print(ncards)
        del ncards

class test():
    pass

if __name__ == "__main__":
    flop = [Card('8s'),Card('9s'),Card('Ts')]
    hole = [Card('2d'),Card('Qc')]
    game = test()
    game.community = flop
    player = test()
    player.cards = hole
    game.num_active_players = 2
    print(prob_best_after_flop(game,player))
    game.community.append(Card('2h'))
    print(prob_best_after_turn(game,player))
    game.community.append(Card('3d'))
    print(prob_best(game,player))
    for c in game.community:
        print(c.index)
    for c in hole:
        print(c.index)
