pit
===

This is a game engine for the Pit commodity-trading card game. The core code here is the game engine, which approximates the rules and gameplay of the card game. The idea is for you/anyone to write players and pit them against each other.

There are two version of the game engine:

Synchronous version
-------------------
- pit/sync/gameengine.py
- game engine runs a single game loop, fetching & processing player actions one at a time

Async version
-------------
- pit/async/gameengine.py
- players are spanwed as processes, each with its own pipe and queue for communication back to the game engine
- my current sample/debugging players (SimplePlayer) are *extremely* inefficient, taking several minutes (and hundreds of thousands of decisions) to complete a single game to 500.

links
-----
[Pit Wikipedia page]

[Rules]

[Boardgame Geek page]

(if you are intersted in buyin the game, I recommend "Deluxe Pit" which comes the a bell :-)

