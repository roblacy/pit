"""Basic player(s) for the Pit game
"""
import pit.gameengine as gameengine


class BasicPlayer(gameengine.Player):
    """A basic player for the Pit game engine.

    This player has no real strategy. It will always make a trade if one is
    available, regardless of which player is offering the trade, etc.
    """
