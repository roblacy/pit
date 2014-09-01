"""Pit game engine

Right now this is the "count to 1000" game so I could play around with
threads and notifications. The next step is to copy Pit functionality over from
the synchronous version.

TODO:
- write actual Pit game engine and player
  - Offer and BindingOffer as only types of offer actions:
    - Offer is non-binding and made to everyone/no one
    - BindingOffer is binding, made to specific player, involves specific cards
  - BindingOffer can be rejected or ignored, rejecting is polite but not required
    and original player can/should withdraw it after some time has gone by

MESSAGES:
new game
new round (cards dealt)
done - terminate threads etc.

"""
import multiprocessing
import random
import threading
import time


class Message(object):
    name = 'this is my name'


class Player(object):
    """A Pit player.

    This class provides method definitions that define the interface.
    """
    def __init__(self, name):
        self.name = name

    def set_up(self, conn, queue):
        """Set up player a connection to the game engine.

        This method is called in a new Process and provides the connection to
        receive updates from the game engine and the queue to put new actions
        that the game engine will process.
        """


class BasicPlayer(Player):
    """
    """
    def set_up(self, conn, queue):
        """
        """
        self.conn = conn
        self.queue = queue

        self.done = threading.Event()
        self.game_over = threading.Event()
        self.queue.put([self.name, 'all set'])
        self.listen()

    def new_game(self):
        """Resets state at the start of a new game.
        """
        self.game_over.clear()
        game_loop = threading.Thread(target=self.game_loop, args=())
        game_loop.daemon = True
        game_loop.start()

    def game_loop(self):
        """Main game loop, examines game state and puts actions on the queue.

        This is meant to be run once per game.
        """
        self.queue.put([self.name, 'ready'])
        num = 1
        while not self.game_over.is_set():
            self.queue.put([self.name, num])
            num += 1

            # this will block, allowing the current thread to release the cpu
            # without this, sometimes the thread never ends
            self.game_over.wait(.0001)
        self.queue.put([self.name, 'game complete'])

    def listen(self):
        """Listens for messages from the game engine and update internal state.
        """
        while not self.done.is_set():
            message = self.conn.recv()
            if message == 'new game':
                self.new_game()
            elif message == 'game over':
                self.game_over.set()
            elif message == 'done':
                self.done.set()


class GameEngine(object):
    """This is the Pit game engine. More details to come...
    """
    def play(self, players, games=1):
        """Will play some number of games with the given set of players
        """
        self.players = players
        self.set_up()
        self.wait_for_players('all set')
        for game in range(games):
            self.game_over = False
            self.one_game()
        self.tear_down()

    def set_up(self):
        """Sets up players, game state, etc."""
        self.action_queue = multiprocessing.Queue()
        self.player_data = {}
        for player in self.players:
            parent_conn, child_conn = multiprocessing.Pipe()
            proc = multiprocessing.Process(
                target=self.set_up_player, args=(player, child_conn))
            self.player_data[player] = {
                'conn': parent_conn,
                'proc': proc,
                'locked_cards': [],
                'score': 0,
            }
            proc.start()

    def set_up_player(self, player, conn):
        """Starts a new process for a player"""
        player.set_up(conn, self.action_queue)

    def one_game(self):
        """Plays one full game"""
        self.scores = {}
        for player in self.players:
            self.scores[player.name] = 0
            self.player_data[player]['conn'].send('new game')

        self.wait_for_players('ready')

        while not self.game_over:
            action = self.action_queue.get()
            self.process_action(action)
        self.end_game()

    def process_action(self, action):
        """Processes player actions, updates state, checks if anyone won.
        """
        name, score = action
        self.scores[name] = score
        if score == 1000:
            lowest = min(self.scores.values())
            print 'lowest score was {0}'.format(lowest)
            self.game_over = True

    def end_game(self):
        """Runs through steps to end a game, notifies players.
        """
        for player in self.players:
            self.player_data[player]['conn'].send('game over')
        self.wait_for_players('game complete')

    def tear_down(self):
        """Steps to close down player processes & threads.
        """
        for player in self.players:
            self.player_data[player]['conn'].send('done')
            self.player_data[player]['proc'].join()

    def wait_for_players(self, expected_message):
        """Loops and reads queue until message is received from all players.

        Discards any message from queue that is not the expected one.
        """
        received = set()
        while len(received) < len(self.players):
            name, message = self.action_queue.get()
            if message == expected_message:
                received.add(name)