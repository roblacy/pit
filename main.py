from pit import gameengine


if __name__ == '__main__':
    ge = gameengine.GameEngine()
    players = [
        gameengine.BasicPlayer('bob'),
        gameengine.BasicPlayer('sue'),
        gameengine.BasicPlayer('ted'),
        gameengine.BasicPlayer('joe'),
        gameengine.BasicPlayer('kim'),
        gameengine.BasicPlayer('deb'),
    ]
    ge.play(players, games=10)

