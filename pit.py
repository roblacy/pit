"""Pit Game Engine

The game is broken into distinct cycles during which each player gets the chance
to perform one action (making an offer, responding to a prior offer, etc.). The
player actions for each cycle are randomized and then executed one at at time.
Therefore, in each cycle, all player actions are based on information known at
the end of the previous cycle, but the order of execution is random, so if two
players attempt to do the same thing (e.g. respond to an offer or ring the
trading bell), luck will determine who does it first.
"""
import itertools
import random


WINNING_SCORE = 500

# number of cycles before an offer expires
OFFER_CYCLES = 10
# number of cycles before a response expires
RESPONSE_CYCLES = 5

COMMODITIES = {
    'wheat': 100,
    'barley': 85,
    'coffee': 80,
    'corn': 75,
    'sugar': 65,
    'oats': 60,
    'soybeans': 55,
    'oranges': 50,
}

BULL = 'bull'
BEAR = 'bear'


class Action(object):
    def __init__(self, player):
        self.player = player
        self.cycle = -1 # to be set by game engine


class Offer(Action):
    def __init__(self, player, quantity):
        super(Offer, self).__init__(player)
        self.quantity = quantity


class Response(Action):
    # when issuing a response you should lock those commodities up
    # and not make them part of any other offer or response
    # TODO error check this in the game engine
    def __init__(self, player, target, quantity):
        super(Offer, self).__init__(player)
        self.target = target
        self.quantity = quantity


class Confirmation(Action):
    def __init__(self, player, response):
        super(Offer, self).__init__(player)
        self.response = response


class RingBell(Action):
    pass


class Player(object):
    def get_name(self):
        """What is this player's name?"""

    def new_game(self, game_state):
        """New game started with fresh game state"""

    def new_round(self, cards):
        """New round of a game started, includes player's cards"""

    def opening_bell(self):
        """Opening bell rung, trades allowed now"""

    def get_action(self):
        """Return an action for the current cycle or None to pass"""

    def offer_made(self, offer):
        """A player has called out an offer for anyone to respond"""

    def offer_expired(self, offer):
        """Your prior offer has expired without executing"""

    def response_made(self, player, offer):
        """A player has responded to your prior offer"""

    def trade_confirmation(self, player1, player2, quantity, offer=None):
        """Two players (possibly you are one of them) have made a trade"""

    def response_expired(self, player, offer):
        """Your response to a specific player expired without being accepted"""

    def closing_bell(self, player):
        """A player has rung the closing bell"""

    def closing_bell_confirmed(self, player):
        """The game engine has confirmed that a player has won this round"""



class GameEngine(object):
    def one_game(self, players, starting_dealer=0):
        """Play one game with this list of players, returns winning player.
        """
        self.players = players
        self.game_state = dict((player, {'score': 0}) for player in players)
        self.game_state['dealer'] = starting_dealer
        for player in self.players:
            player.new_game(self.game_state)

        self.winner = None
        while not self.winner:
            self.one_round()
            self.next_dealer()

        print 'Player {name} has won'.format(self.winner.get_name())
        return self.winner

    def one_round(self):
        """Plays round, updates scores, sets self.winner if anyone won
        """
        self.deal_cards()
        for player in self.players:
            player.new_round(self.game_state[player]['cards'])

        self.game_state['cycle'] = 0
        self.game_state['in_play'] = True
        self.game_state['offers'] = []
        self.game_state['responses'] = []
        while self.game_state['in_play']:
            self.one_cycle()

        # TODO update scores, check if anyone won & set self.winner

    def one_cycle(self):
        """One cycle gives each player the chance to perform an action"""
        actions = []
        for player in self.players:
            action = player.get_action()
            if action:
                action.cycle = self.game_state['cycle']
                actions.append(action)
        random.shuffle(actions)
        for action in actions:
            self.process_action(action)
            if not self.game_state['in_play']:
                return
        self.game_state['cycle'] += 1
        self.clean_actions()

    def process_action(self, action):
        """One player makes one action"""
        self.ACTION_METHODS[type(action)](self, action)

    def add_offer(self, offer):
        """Add an offer to the game"""
        offer.cycle = self.game_state['cycle']
        self.game_state['offers'].append(offer)
        for player in self.players:
            player.offer_made(offer)

    def send_response(self, response):
        """Issue a response to an offer"""
        # TODO this method

    def confirm(self, confirmation):
        """Confirm a trade between two players"""
        # TODO this method

    def ring_bell(self, bell_ring):
        """Ring the closing bell"""
        # TODO this method
        # send out closing bell event
        # if player wins then:
        # - mark in_play False
        # - send out closing bell confirmed event



    ACTION_METHODS = {
        Offer: self.add_offer,
        Response: self.send_response,
        Confirmation: self.confirm,
        RingBell: self.ring_bell,
    }

    # TODO - I am here working on the individual action methods

    def clean_actions(self):
        """Remove any expired offers or responses"""

        # TODO need to get the offers & responses that expired and
        # send out expired events for all of them
        # so what I really want to do is split game_state['offers'] into
        # two mutually exlusive lists, keep one & send events for the other
        # then do the same for responses

        self.game_state['offers'] = list(itertools.ifilterfalse(
            self._expired_offer, self.game_state['offers']))
        self.game_state['responses'] = list(itertools.ifilterfalse(
            self._expired_response, self.game_state['responses']))

    def _expired_offer(self, offer):
        """True iff this offer is expired

        An offer added in cycle 0 gets to live through cycle <OFFER_CYCLES>
        """
        return self.game_state['cycle'] - offer.cycle > OFFER_CYCLES

    def _expired_response(self, response):
        """True iff this response is expired

        A response added in cycle 0 gets to live through cycle <RESPONSE_CYCLES>
        """
        return self.game_state['cycle'] - response.cycle > RESPONSE_CYCLES

    def deal_cards(self):
        """Sets game_state cards to a new set of shuffled cards"""
        cards = [BULL, BEAR]
        for card in COMMODITIES.keys()[:len(self.players)]:
            cards += [card]*9
        random.shuffle(cards)

        for index, player in enumerate(self.players):
            self.game_state[player]['cards'] = cards[index*9:index*9+9]
        extra1 = self.game_state['dealer'] + 1
        if extra1 >= len(self.players):
            extra1 -= len(self.players)
        extra2 = self.game_state['dealer'] +2
        if extra2 >= len(self.players):
            extra2 -= len(self.players)
        self.game_state[self.players[extra1]]['cards'].append(cards[-2])
        self.game_state[self.players[extra2]]['cards'].append(cards[-1])

    def next_dealer(self):
        """Advances dealer"""
        next = self.game_state['dealer'] + 1
        self.game_state['dealer'] = next if next < len(self.players) else 0

    def debug_and_exit(self):
        """Helper to print game state and exit game"""
        for player in self.players:
            print player
            print self.game_state[player]
            print ''
        import sys
        sys.exit(0)





engine = GameEngine()
players = [Player() for p in range(7)]
engine.one_game(players)
