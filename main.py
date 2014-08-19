"""Runs a Pit game
"""
import gameengine
import player.basic as basic


engine = gameengine.GameEngine()
players = [basic.BasicPlayer() for p in range(7)]
engine.one_game(players)
