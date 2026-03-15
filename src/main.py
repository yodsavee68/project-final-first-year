import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from xo.game import GameController

if __name__ == "__main__":
    game = GameController()
    game.run()
