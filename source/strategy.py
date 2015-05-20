#!/usr/bin/python
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
from holdme import Card,deck,score5 as score5,score7

RANKS = '23456789TJQKA'
SUITS = 'CHSD'

HOLE_CARDS = {1:['AA','KK','QQ','JJ','AKs'],
        2:['TT','AQs','AJs','KQs','AKo'],
        3:['99','ATs','KJs','QJs','JTs','AQo'],
        4:['88','KTs','QTs','J9s','T9s','98s','AJo','KQo'],
        5:['77','A9s','A8s','A7s','A6s','A5s','A4s','A3s','A2s','Q9s','T8s','97s','87s','76s','KJo','QJo','JTo'],
        6:['66','55','K9s','J8s','86s','75s','54s','ATo','KTo','QTo'],
        7:['44','33','22','K8s','K7s','K6s','K5s','K4s','K3s','K2s','Q8s','T7s','64s','53s','43s','J9o','T9o','98o'],
        8:['J7s','96s','85s','74s','42s','32s','A9o','K9o','Q9o','J8o','T8o','87o','76o','65o','54o']}


PHIL = {1:['AA','KK','AKs','QQ','AK'],
        2:['JJ','TT','99'],
        3:['88','77','AQs','AQ',],
        4:['66','55','44','33','22','AJs','ATs','A9s','A8s'],
        5:['A7s','A6s','A5s','A4s','A3s','A2s','KQs','KQ'],
        6:['QJs','JTs','T9s','98s','87s','76s','65s']
        }

CACHE = {}

class HoleCards():
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

    def tier(self,table=PHIL):
        for i in table:
            if self.is_tier(i,table):
                return i
        return None

    def is_tier(self,i,table):
        if self.ranks in table[i] or self.ranks+self.suits in table[i]:
            return True
        return False


class Strategy():

    def __init__(self, game, player):
        self.game = game
        self.player = player
        if player.cards[0] and player.cards[1]:
            self.hole = HoleCards(player.cards[0],player.cards[1])
        else:
            print("Warning! the player must hold 2 cards")

    def act(self):
        pass

    def learn():
        pass

class PreFlopLoose(Strategy):
    play_tier = 3 #PLAYTIER
    raise_tier = 1 #RAISETIER

    def act(self):
        if not self.hole.tier():
            self.player.fold()
        elif self.hole.tier() <= self.raise_tier:
            self.player.raise_(2 * self.game.raise_bet)
        elif self.hole.tier() <= self.play_tier:
            self.player.call()
        else:
            self.player.fold()

class FlopLoose(Strategy):
    plable_lev = 1

    def __init__(self,game, player):
        Strategy.__init__(self, game, player)
        self.hand = Hand(self.game.flop+self.player.cards)
        self.pot_odds = self.player.pot_odds
        #self.prob = self.hand.cal_prob(self.plable_lev)
        #self.prob_win = prob_win(game.cards, player.cards, game.alive_oponents)

    def act(self):
        self.prob_win = prob_win(game.cards, player.cards, game.alive_oponents)
        if self.prob_win > self.pot_odds:
            #self.player.raise_(self.game.raise_bet)
            self.player.call()
            #or call
        else:
            self.player.fold()

class TurnLoose(Strategy):
    plable_lev = 1

    def __init__(self, game, player):
        Strategy.__init__(self, game, player)
        cards = self.game.flop + self.player.cards
        cards.append(self.game.turn)
        self.hand = Hand(cards)
        self.pot_odds = self.player.pot_odds
        self.prob = self.hand.cal_prob(self.plable_lev)

    def act(self):
        if self.prob > self.pot_odds:
            self.player.raise_(self.game.raise_bet)
            #or call
        else:
            self.player.fold()

class RiverLoose(Strategy):
    def act(self):
        self.player.check()



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

def score6(cards):
    best_score = 0
    for c in cards:
        cards5 = cards[:]
        cards5.remove(c)
        score = score5(cards5)
        if score > best_score:
            best_score = score
    return best_score

def cal_score(cards):
    if len(cards) == 5:
        return score5(cards)
    elif len(cards) ==6:
        return score6(cards)
    elif len(cards) == 7:
        return score7(cards)
    else:
        return None

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
        if i in cards:
            continue
        CACHE[i] = cal_prob_gt_cards(community+[card], hole)

def cal_prob_win_on_out(community, hole,num_oponent):
    p_win = 0
    temp = 0
    p_gt = 0
    left_cards_count = 50 - len(community)
    for i in range(52):
        card = Card.from_index(i)
        if i in cards:
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
            if card_a in cards or card_b in cards:
                continue
            expect_score = cal_score(cards+[card_a,card_b])
            if expect_score > score:
                gt_count += 1
            sum_count += 1
    return gt_count/sum_count

class Hand():
    def __init__(self, cards):
        self.cards = cards
        num_cards = len(cards)
        self.num_cards = num_cards
        if num_cards == 5:
            self.score = score5(cards)
        elif num_cards == 6:
            self.score = score6(cards)
        elif num_cards == 7:
            self.score = score7(cards)
        else:
            print(cards)
            print(num_cards)
            print("cards number error")
            raise Exception
        self.lev = self.score >> 26
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
        score = score5(ncards)
        type_lev = score >> 26
        if type_lev > 2:
            print(ncards)
        del ncards


if __name__ == "__main__":
    '''
    test = {1:set([]),
            2:set([]),
            3:set([]),
            4:set([]),
            5:set([]),
            6:set([])}
    for i in range(52):
        for j in range(i+1,52):
            card_a = Card.from_index(i)
            card_b = Card.from_index(j)
            hole = HoleCards(card_a,card_b)
            if hole.tier():
                test[hole.tier()].add(hole.ranks+hole.suits)

    print(test)

    for i in range(52):
        for j in range(i+1,52):
            for k in range(j+1,52):
                for l in range(k+1,52):
                    cards = [Card.from_index(i),
                            Card.from_index(j),
                            Card.from_index(k),
                            Card.from_index(l)]
                    if isInsideStraight(cards):
                        for c in cards:
                            print(c,end='')
                        print('\n')
    '''
    cards = [Card('TS'),Card('9s'),Card('8s'),Card('QC'),Card('2s')]
    hand = Hand(cards)
    print(hand)
    print(hand.cal_outs())
    flop = [Card('Ts'),Card('9s'),Card('8s')]
    hole = [Card('QC'),Card('2s')]
    hand = Hand(flop+hole)
    print(hand.cal_prob(2))
    print(cal_prob_gt_score(flop,hand.score))
    make_cache(flop,hole)
    print("now")
    print(prob_win(flop,hole,1,out=True))
    print(prob_win(flop,hole,2,out=True))

