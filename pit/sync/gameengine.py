"""Pit Game Engine

The game is broken into distinct cycles during which each player gets the chance
to perform one action (making an offer, responding to a prior offer, etc.). The
player actions for each cycle are randomized and then executed one at at time.
Therefore, in each cycle, all player actions are based on information known at
the end of the previous cycle, but the order of execution is random, so if two
players attempt to do the same thing (e.g. respond to an offer or ring the
trading bell), luck will determine who does it first.

SUGGESTIONS:
- at start of game provide players with starting info
 - number of players, which specific cards are being used
- at start of round, provide basic info
- get rid of game state and just send info to players and let them keep
  track of it themselves
- send full hand to player with each trade (as the gameengine views it)



TODO LIST:
- do suggestions above
- use new things added in the async version:
    - switch to Offer/Binding Offer terminology
    - use util.py methods
- get rid of Action subclasses like async version?
- Remove prior open offers when player performs any action?
- Have a trade take several cycles. Prob will increase strategy opportunity.
  - yes block users for couple cycles after a trade (simulates time to exchange cards)
  - also consider blocking users for 1 cycle after an offer or binding offer
- error-checking of things like player hands, legal actions etc.
- error-checking that cards are locked up when player issues a response
- withdraw offer method?
    - not sure if needed, can always ignore responses to an offer
- withdraw response method?
    - not sure if needed, probably nice, but game should be functional without it
    - if doing this, need to deal with issue of confirm & withdraw happening on
      same cycle - probably make the withdrawal pending until the cycle ends with
      no confirms, then remove it

ASYNC GAME ENGINE
- run each player and game engine in separate threads/processes
- shared queue of actions
- shared game state, maybe some callbacks as well (?)
- game engine just listens at one end of the queue and processes actions as they
  come in
- QUESTION: will players get fair CPU time? If not automatic, can it be ensured?

"""
import copy
import itertools
import random

from pit import config


# number of cycles before an offer expires
OFFER_CYCLES = 10
# number of cycles before a response expires
RESPONSE_CYCLES = 5


class Action(object):
    def __init__(self, player):
        self.player = player
        self.cycle = -1 # to be set by game engine

    def __unicode__(self):
        return 'Action'

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return unicode(self).encode('utf-8')


class Offer(Action):
    """An offer to trade a certain number of cards, made to anyone/everyone.
    """
    def __init__(self, player, quantity):
        super(Offer, self).__init__(player)
        if quantity > 4:
            raise Exception('Offers can only be up to four cards')
        self.quantity = quantity

    def __unicode__(self):
        return 'Offer in cycle {2} by {0} for {1}'.format(
            self.player, self.quantity, self.cycle)


class Response(Action):
    """Response to an offer.

    A response is binding - a player issuing one should not make any other
    offers or responses with these cards until this response is confirmed,
    withdrawn, or expired.
    """
    def __init__(self, offer, player, cards):
        """Game engine needs to know the cards so it can execute a trade. They
        will be removed before the response is sent to the target player.
        """
        super(Response, self).__init__(player)
        self.offer = offer
        self.cards = cards

    def __unicode__(self):
        return 'Response in cycle {2} by {0} to {1}'.format(
            self.player, self.offer, self.cycle)


class BellRing(Action):
    """The action of ringing the bell to indicate that you have won the round"""
    def __unicode__(self):
        return 'Bell Ring in cycle {1} by {0}'.format(self.player, self.cycle)


class Player(object):
    def __init__(self):
        self.name = 'Player {0}'.format(random.randint(1,9999))

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
        """A player has responded to your prior offer

        Should return list of cards if you accept the offer, else None.
        """

    def response_rejected(self, response):
        """Your response to a specific player was rejected"""

    def trade_confirmation(self, response):
        """Two players (possibly you are one of them) have made a trade"""

    def closing_bell(self, player):
        """A player has rung the closing bell"""

    def closing_bell_confirmed(self, player):
        """The game engine has confirmed that a player has won this round"""

    def __unicode__(self):
        return self.name

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return unicode(self).encode('utf-8')


class GameEngine(object):
    def play(self, players, games=1):
        """Primary entry method, plays a number of games of Pit"""
        self.players = players
        results = dict([(player, 0) for player in players])
        for game in range(games):
            dealer = random.randint(0,len(players)-1)
            winner = self.one_game(starting_dealer=dealer)
            results[winner] += 1
        return results

    def one_game(self, starting_dealer=0):
        """Play one game and returns winning player.
        """
        self.game_state = {}
        self.game_state['dealer'] = starting_dealer
        for player in self.players:
            self.game_state[player] = {'score': 0}
            player.new_game(self.game_state)

        self.winner = None
        while not self.winner:
            self.one_round()
            self.next_dealer()
        return self.winner

    def one_round(self):
        """Plays round, updates scores, sets self.winner if anyone won
        """
        self.game_state['cycle'] = 0
        self.game_state['in_play'] = True
        self.game_state['offers'] = []

        self.deal_cards()
        for player in self.players:
            player.new_round(self.game_state[player]['cards'])

        while self.game_state['in_play']:
            self.one_cycle()

        self.update_scores()

    def one_cycle(self):
        """One cycle gives each player the chance to perform an action"""
        actions = self.collect_actions()
        for action in actions:
            self.process_action(action)
            if not self.game_state['in_play']:
                return
        self.game_state['cycle'] += 1
        self.clean_actions()

    def collect_actions(self):
        """Collects and randomizes player actions, locking cards as needed"""
        actions = []
        self.locked_cards = {}
        for player in self.players:
            action = player.get_action()
            if action:
                action.cycle = self.game_state['cycle']
                actions.append(action)
                if isinstance(action, Response):
                    self.locked_cards[player] = action.cards
        random.shuffle(actions)
        return actions

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
        """Issue a response to player who made initial offer.

        The initial player immediately accepts or rejects the response, so by
        the end of this method the response is either rejected or the trade is
        confirmed.

        The response will be also rejected under any of these conditions:
        - same player made both offer and response
        - offer no longer present in game state list of offers
        - player making response no longer has these cards

        This also grabs the response's cards & removes them from the response.
        They are saved so they can be used if the trade ends up executing.
        """
        response.cycle = self.game_state['cycle']
        response_cards = response.cards
        response.cards = None

        if (response.offer in self.game_state['offers'] and
                response.player != response.offer.player and
                self.still_has_cards(response.player, response_cards)):
            confirm_cards = response.offer.player.response_made(response)
            if confirm_cards:
                self.confirm(response, response_cards, confirm_cards)
                return
        # player rejected response or offer was already removed
        response.player.response_rejected(response)

    def confirm(self, response, response_cards, confirm_cards):
        """Confirm a trade between two players"""
        self.game_state['offers'].remove(response.offer)

        for card in response_cards:
            self.game_state[response.player]['cards'].remove(card)
            self.game_state[response.offer.player]['cards'].append(card)
        for card in confirm_cards:
            self.game_state[response.offer.player]['cards'].remove(card)
            self.game_state[response.player]['cards'].append(card)

        for player in self.players:
            player.trade_confirmation(response)

    def ring_bell(self, bell_ring):
        """Ring the closing bell"""
        for player in self.players:
            player.closing_bell(bell_ring.player)
        if self.has_winning_hand(bell_ring.player):
            self.game_state['in_play'] = False
            for player in self.players:
                player.closing_bell_confirmed(bell_ring.player)

    ACTION_METHODS = {
        Offer: add_offer,
        Response: send_response,
        BellRing: ring_bell,
    }

    def still_has_cards(self, player, cards):
        """Returns True iff the given player still has the given cards"""
        player_cards = copy.copy(self.game_state[player]['cards'])
        for card in cards:
            if card not in player_cards:
                return False
            player_cards.remove(card)
        return True

    def has_winning_hand(self, player):
        """Returns True iff player has a valid winning hand

        To have a winning hand, the player must have 9 cards consisting of only
        a single commodity and (optionally) the bull card. Player must not have
        the bear card at all.
        """
        cards = self.game_state[player]['cards']
        if config.BEAR in cards:
            return False
        largest_group = cards.count(max(set(cards), key=cards.count))
        return largest_group == 9 or largest_group == 8 and config.BULL in cards

    def update_scores(self):
        """Updates player scores at end of a round, sets winner if any."""
        for player in self.players:
            score = 0
            cards = self.game_state[player]['cards']
            if self.has_winning_hand(player):
                commodity = max(set(cards), key=cards.count)
                score += config.COMMODITIES[commodity]
                if config.BULL in cards and cards.count(commodity) == config.COMMODITIES_PER_HAND:
                    score *= 2
            else:
                if config.BULL in cards:
                    score -= config.BULL_PENALTY
                if config.BEAR in cards:
                    score -= config.BEAR_PENALTY
            self.game_state[player]['score'] += score
            if self.game_state[player]['score'] >= config.WINNING_SCORE:
                self.winner = player

    def clean_actions(self):
        """Remove any expired offers"""
        expired_offers = list(filter(
            self.expired_offer, self.game_state['offers']))
        self.game_state['offers'] = list(itertools.ifilterfalse(
            self.expired_offer, self.game_state['offers']))
        for offer in expired_offers:
            offer.player.offer_expired(offer)

    def expired_offer(self, offer):
        """True iff this offer is expired

        An offer added in cycle 0 gets to live through cycle <OFFER_CYCLES>
        """
        return self.game_state['cycle'] - offer.cycle > OFFER_CYCLES

    def deal_cards(self):
        """Sets game_state cards to a new set of shuffled cards"""
        cards = [config.BULL, config.BEAR]
        for card in config.COMMODITIES.keys()[:len(self.players)]:
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

    def debug(self):
        """Helper to print game state and exit game"""
        print 'CYCLE {0}'.format(self.game_state['cycle'])
        for player in self.players:
            cards = copy.copy(self.game_state[player]['cards'])
            cards.sort()
            print 'PLAYER {0}: score={1} cards={2}'.format(
                unicode(player), self.game_state[player]['score'], cards)
        print 'OFFERS {0}'.format(self.game_state['offers'])
        print 'IN PLAY? {0}'.format(self.game_state['in_play'])
        print '---------------'
