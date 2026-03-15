import abc
from typing import Optional, Tuple
from xo.models import Board, PlayerInventory
from xo.ai import AIOpponent

class Player(abc.ABC):
    def __init__(self, player_id: int, username: str):
        self.player_id = player_id
        self.username = username

    @abc.abstractmethod
    def get_move(self, board: Board, inventory: PlayerInventory, opponent_inventory: PlayerInventory, can_eat: bool, opponent_can_eat: bool) -> Optional[Tuple[int, int, int, Optional[int], Optional[int]]]:
        """Returns (size, r, c, from_r, from_c) or None"""
        pass

class HumanPlayer(Player):
    def get_move(self, board: Board, inventory: PlayerInventory, opponent_inventory: PlayerInventory, can_eat: bool, opponent_can_eat: bool) -> Optional[Tuple[int, int, int, Optional[int], Optional[int]]]:
        # Human moves are handled via UI events in GameController
        # This is a placeholder for polymorphism
        return None

class AIPlayer(Player):
    def __init__(self, player_id: int, username: str = "AI"):
        super().__init__(player_id, username)
        self.ai_engine = AIOpponent(player_id)

    def get_move(self, board: Board, inventory: PlayerInventory, opponent_inventory: PlayerInventory, can_eat: bool, opponent_can_eat: bool) -> Optional[Tuple[int, int, int, Optional[int], Optional[int]]]:
        return self.ai_engine.get_best_move(board, inventory, opponent_inventory, can_eat, opponent_can_eat)
    
    def record_state(self, board: Board, inventory: PlayerInventory, opponent_inventory: PlayerInventory, can_eat: bool):
        self.ai_engine.record_state(board, inventory, opponent_inventory, can_eat)

    def learn_from_loss(self):
        self.ai_engine.learn_from_loss()

    def clear_history(self):
        self.ai_engine.clear_history()
