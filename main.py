import time

from pit import gameengine
from pit.player import base, basic



if __name__ == '__main__':
    start_time = time.time()
    ge = gameengine.GameEngine()
    players = [
        basic.SimplePlayer('joe'),
        basic.SimplePlayer('kim'),
        basic.SimplePlayer('deb'),
        basic.SimplePlayer('bob'),
        basic.SimplePlayer('sue'),
        basic.SimplePlayer('ted'),
        basic.SimplePlayer('han'),
        basic.SimplePlayer('jen'),
    ]
    ge.play(players, games=1)
    print 'TOTAL TIME: {0} seconds'.format(time.time() - start_time)
