"""Basic player(s) for the Pit game
"""
import random
import copy

import pit.gameengine as gameengine


class BasicPlayer(gameengine.Player):
    """A basic player for the Pit game engine.

    This player has no real strategy. It will always make a trade if one is
    available, regardless of which player is offering the trade, etc.

    TODO LIST
    - do not accept a response if cards already locked up in own response
    """
    def __init__(self, name):
        super(BasicPlayer, self).__init__()
        self.name = name

    def new_game(self, game_state):
        self.game_state = game_state

    def new_round(self, cards):
        """New round of a game started, includes player's cards"""
        self.cards = cards

    def get_action(self):
        """Returns action for this cycle

        1. if winning hand, ring the bell
        2. try to respond to an open offer
        3. make a new offer
        """
        self._group_cards()

        if self._has_winning_hand():
            return gameengine.BellRing(self)
        offers = copy.copy(self.game_state['offers'])
        random.shuffle(offers)
        for offer in offers:
            cards = self._get_response(offer)
            if cards:
                return gameengine.Response(offer, self, cards)
        # cannot respond to any open offers so generate a new one
        return self._make_offer()

    def response_made(self, response):
        """Confirms (if possible) or rejects a response to a previous offer

        Returns list of cards if offer is accepted, else None.
        """
        self._group_cards()
        return self._matching_cards(response.offer)

    def _has_winning_hand(self):
        """True if currently holding a winning hand"""
        if gameengine.BEAR in self.cards:
            return False
        count = self.cards.count(max(set(self.cards), key=self.cards.count))
        return count == 9 or (count == 8 and gameengine.BULL in self.cards)

    def _get_response(self, offer):
        """Returns list of cards if response can be made to this offer, or None
        """
        if offer.player == self:
            return None
        return self._matching_cards(offer)

    def _matching_cards(self, offer):
        """Helper returns cards matching quantity of this offer, if possible

        Randomly chooses cards to see if quantity matches for a trade. Also
        tries to add the bull/bear/both cards to make the quantity match.
        """
        bull = gameengine.BULL
        bear = gameengine.BEAR
        commodities = self.card_groups.keys()
        random.shuffle(commodities)
        for commodity in commodities:
            quantity = self.card_groups[commodity]
            if quantity == offer.quantity:
                return [commodity] * quantity
            elif commodity not in [bull, bear]:
                if bull in self.cards and offer.quantity == quantity+1:
                    return [commodity] * quantity + [bull]
                elif bear in self.cards and offer.quantity == quantity+1:
                    return [commodity] * quantity + [bear]
                elif (
                        bull in self.cards and
                        bear in self.cards and
                        offer.quantity == quantity+2):
                    return [commodity] * quantity + [bull, bear]
        return None

    def _make_offer(self):
        """Returns a new Offer

        Max of 4 cards can be part of an offer
        """
        existing_quantities = [
            offer.quantity for offer in self.game_state['offers']
            if offer.player == self
        ]
        quantities = self.card_groups.values()
        random.shuffle(quantities)
        for quantity in quantities:
            if quantity <= 4 and quantity not in existing_quantities:
                return gameengine.Offer(self, quantity)

    def _group_cards(self):
        """Breaks cards into groups keyed by type, count as values"""
        if self.cards != self.game_state[self]['cards']:
        self.card_groups = {}
        for card in set(self.cards):
            self.card_groups[card] = self.cards.count(card)
