"""Runs a synchronous Pit game using the Game Engine and Player from pit.sync
"""
import pit.sync.gameengine as gameengine
import pit.sync.player.basic as basic


engine = gameengine.GameEngine()

players = []
players.append(basic.BasicPlayer('bob'))
players.append(basic.BasicPlayer('joe'))
players.append(basic.BasicPlayer('sue'))
players.append(basic.BasicPlayer('tim'))
players.append(basic.BasicPlayer('ned'))
players.append(basic.BasicPlayer('deb'))
players.append(basic.BasicPlayer('pat'))

win_count = {}
for player in players:
    win_count[player] = 0
for game in range(100):
    if game % 10 == 0:
        print 'Playing game {0}'.format(game)
    winner = engine.one_game(players)
    win_count[winner] += 1
print win_count
