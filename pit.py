"""Pit Game Engine

The game is broken into distinct cycles during which each player gets the chance
to perform one action (making an offer, responding to a prior offer, etc.). The
player actions for each cycle are randomized and then executed one at at time.
Therefore, in each cycle, all player actions are based on information known at
the end of the previous cycle, but the order of execution is random, so if two
players attempt to do the same thing (e.g. respond to an offer or ring the
trading bell), luck will determine who does it first.

TODO LIST:
- change structure, players folder, tests folder, pit.py -> gameengine.py
- make a basic player and start testing
OPTIONAL TODOS:
- error-checking of things like player hands, legal actions etc.
- error-checking that cards are locked up when player issues a response
- withdraw offer method?
    - not sure if needed, can always ignore responses to an offer
- withdraw response method?
    - not sure if needed, probably nice, but game should be functional without it
    - if doing this, need to deal with issue of confirm & withdraw happening on
      same cycle - probably make the withdrawal pending until the cycle ends with
      no confirms, then remove it
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
BULL_PENALTY = 20
BEAR = 'bear'
BEAR_PENALTY = 20


class Action(object):
    def __init__(self, player):
        self.player = player
        self.cycle = -1 # to be set by game engine


class Offer(Action):
    def __init__(self, player, quantity):
        super(Offer, self).__init__(player)
        self.quantity = quantity


class Response(Action):
    """Response to an offer.

    A response is binding - a player issuing one should not make any other
    offers or responses with these cards until this response is confirmed,
    withdrawn, or expired.
    """
    def __init__(self, player, target, quantity, offer=None):
        super(Offer, self).__init__(player)
        self.target = target
        self.quantity = quantity
        self.offer = offer


class Confirmation(Action):
    def __init__(self, player, response):
        super(Offer, self).__init__(player)
        self.response = response


class BellRing(Action):
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

    def response_made(self, response):
        """A player has responded to your prior offer"""

    def response_expired(self, response):
        """Your response to a specific player expired without being accepted"""

    def trade_confirmation(self, confirmation):
        """Two players (possibly you are one of them) have made a trade"""

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
        self.update_scores()

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
        response.cycle = self.game_state['cycle']
        self.game_state['responses'].append(response)
        response.target.response_made(response)

    def confirm(self, confirmation):
        """Confirm a trade between two players"""
        if confirmation.response.offer:
            self.game_state['offers'].remove(confirmation.response.offer)
        self.game_state['responses'].remove(confirmation.response)
        for player in self.game_state['players']:
            player.trade_confirmation(confirmation)

    def ring_bell(self, bell_ring):
        """Ring the closing bell"""
        for player in self.players:
            player.closing_bell()
        if self.has_winning_hand(bell_ring.player):
            self.game_state['in_play'] = False
            for player in self.players:
                player.closing_bell_confirmed(bell_ring.player)

    ACTION_METHODS = {
        Offer: self.add_offer,
        Response: self.send_response,
        Confirmation: self.confirm,
        BellRing: self.ring_bell,
    }

    def has_winning_hand(self, player):
        """Returns True iff player has a valid winning hand

        To have a winning hand, the player must have 9 cards consisting of only
        a single commodity and (optionally) the bull card. Player must not have
        the bear card at all.
        """
        cards = self.game_state[player]['cards']
        if BEAR in cards:
            return False
        largest_group = cards.count(max(set(cards), key=cards.count))
        return largest_group == 9 or largest_group == 8 and BULL in cards

    def update_scores(self):
        """Updates player scores at end of a round, sets winner if any."""
        for player in self.players:
            score = 0
            cards = self.game_state[player]['cards']
            if self.has_winning_hand(player):
                commodity = max(set(cards), key=cards.count)
                score += COMMODITIES[commodity]
                if BULL in cards and BEAR in cards:
                    score *= 2
            else:
                if BULL in cards:
                    score -= BULL_PENALTY
                if BEAR in cards:
                    score -= BEAR_PENALTY
            self.game_state[player]['score'] += score
            if self.game_state[player]['score'] >= WINNING_SCORE:
                self.winner = player

    def clean_actions(self):
        """Remove any expired offers or responses"""
        expired_offers = list(filter(
            self.expired_offer, self.game_state['offers']))
        self.game_state['offers'] = list(itertools.ifilterfalse(
            self.expired_offer, self.game_state['offers']))

        for offer in expired_offers:
            offer.player.offer_expired(offer)

        expired_responses = list(filter(
            self.expired_response, self.game_state['responses']))
        self.game_state['responses'] = list(itertools.ifilterfalse(
            self.expired_response, self.game_state['responses']))

        for response in expired_responses:
            response.player.response_expired(response)

    def expired_offer(self, offer):
        """True iff this offer is expired

        An offer added in cycle 0 gets to live through cycle <OFFER_CYCLES>
        """
        return self.game_state['cycle'] - offer.cycle > OFFER_CYCLES

    def expired_response(self, response):
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
