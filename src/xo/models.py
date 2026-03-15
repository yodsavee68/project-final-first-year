from dataclasses import dataclass
from typing import List, Optional, Tuple

from xo.constants import BOARD_SIZE, SIZE_SMALL, SIZE_MEDIUM, SIZE_LARGE


@dataclass
class Piece:
    owner: int
    size: int


class PlayerInventory:
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.pieces = {SIZE_LARGE: 1, SIZE_MEDIUM: 2, SIZE_SMALL: 3}

    def has_piece(self, size: int) -> bool:
        return self.pieces.get(size, 0) > 0

    def use_piece(self, size: int) -> bool:
        if self.has_piece(size):
            self.pieces[size] -= 1
            return True
        return False

    def unuse_piece(self, size: int):
        self.pieces[size] += 1

    def copy(self):
        new_inv = PlayerInventory(self.player_id)
        new_inv.pieces = dict(self.pieces)
        return new_inv


class Board:
    def __init__(self):
        self.grid: List[List[List[Piece]]] = [
            [[] for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)
        ]

    def get_top_piece(self, row: int, col: int) -> Optional[Piece]:
        if self.grid[row][col]:
            return self.grid[row][col][-1]
        return None

    def is_valid_move(
        self, row: int, col: int, piece_size: int, owner: int, can_eat: bool = True
    ) -> bool:
        if row < 0 or row >= BOARD_SIZE or col < 0 or col >= BOARD_SIZE:
            return False
        top = self.get_top_piece(row, col)
        if top is None:
            return True
        if top.owner == owner:
            return False
        if can_eat:
            return piece_size > top.size
        return False

    def place_piece(
        self, row: int, col: int, piece: Piece, validate: bool = True
    ) -> bool:
        if not validate or self.is_valid_move(row, col, piece.size, piece.owner):
            self.grid[row][col].append(piece)
            return True
        return False

    def remove_top_piece(self, row: int, col: int):
        if self.grid[row][col]:
            self.grid[row][col].pop()

    def check_win(self) -> Optional[Tuple[int, str]]:
        def owner(r, c):
            p = self.get_top_piece(r, c)
            return p.owner if p else 0

        # Rows
        for i in range(BOARD_SIZE):
            if owner(i, 0) != 0 and owner(i, 0) == owner(i, 1) == owner(i, 2):
                return (owner(i, 0), f"ชนะแนวนอน (แถว {i + 1})")

        # Cols
        for j in range(BOARD_SIZE):
            if owner(0, j) != 0 and owner(0, j) == owner(1, j) == owner(2, j):
                return (owner(0, j), f"ชนะแนวตั้ง (คอลัมน์ {j + 1})")

        # Diagonals
        if owner(0, 0) != 0 and owner(0, 0) == owner(1, 1) == owner(2, 2):
            return (owner(0, 0), "ชนะแนวทแยง (ซ้ายบนลงขวาล่าง)")
        if owner(0, 2) != 0 and owner(0, 2) == owner(1, 1) == owner(2, 0):
            return (owner(0, 2), "ชนะแนวทแยง (ขวาบนลงซ้ายล่าง)")

        return None

    def get_valid_moves(
        self, player_inventory: PlayerInventory, can_eat: bool = True
    ) -> List[tuple]:
        """Returns a list of (size, row, col, from_row, from_col) describing valid moves for the given player.
        from_row and from_col are None if the piece comes from inventory.
        """
        moves = []
        # 1. Moves from inventory
        for size in [SIZE_SMALL, SIZE_MEDIUM, SIZE_LARGE]:
            if player_inventory.has_piece(size):
                for r in range(BOARD_SIZE):
                    for c in range(BOARD_SIZE):
                        if self.is_valid_move(
                            r, c, size, player_inventory.player_id, can_eat
                        ):
                            moves.append((size, r, c, None, None))

        # 2. Moves from board
        for fr in range(BOARD_SIZE):
            for fc in range(BOARD_SIZE):
                top = self.get_top_piece(fr, fc)
                if (
                    top and top.owner == player_inventory.player_id
                ):  # player owns the piece
                    # Temporarily remove to check valid drops without self-overlap blocking
                    self.remove_top_piece(fr, fc)
                    for r in range(BOARD_SIZE):
                        for c in range(BOARD_SIZE):
                            if (r != fr or c != fc) and self.is_valid_move(
                                r, c, top.size, player_inventory.player_id, can_eat
                            ):
                                moves.append((top.size, r, c, fr, fc))
                    # Put it back
                    self.grid[fr][fc].append(top)

        return moves

    def deepcopy(self):
        new_board = Board()
        new_board.grid = [
            [[Piece(p.owner, p.size) for p in stack] for stack in row]
            for row in self.grid
        ]
        return new_board
