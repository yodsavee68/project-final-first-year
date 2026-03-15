import math
import time
import os
import json
from typing import Tuple, Optional

from xo.models import Board, PlayerInventory, Piece
from xo.constants import PLAYER_X, PLAYER_O, BOARD_SIZE


class TimeoutException(Exception):
    pass


class AIOpponent:
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.opponent_id = PLAYER_X if player_id == PLAYER_O else PLAYER_O
        self.transposition_table = {}
        self.losing_states = set()
        self.current_game_states = []
        self.learning_file = "ai_losing_patterns.json"
        self.load_losing_states()

    def load_losing_states(self):
        try:
            if os.path.exists(self.learning_file):
                with open(self.learning_file, "r") as f:
                    data = json.load(f)
                    self.losing_states = set(data.get("losing_states", []))
        except Exception as e:
            print(f"Error loading AI patterns: {e}")

    def save_losing_states(self):
        try:
            with open(self.learning_file, "w") as f:
                json.dump({"losing_states": list(self.losing_states)}, f)
        except Exception as e:
            print(f"Error saving AI patterns: {e}")

    def record_state(
        self,
        board: Board,
        my_inv: PlayerInventory,
        opp_inv: PlayerInventory,
        my_can_eat: bool,
    ):
        # Record the state from the perspective of the AI immediately after its move
        state_hash = self.get_board_hash(
            board, my_inv, opp_inv, False, my_can_eat, True
        )
        self.current_game_states.append(state_hash)

    def learn_from_loss(self):
        if self.current_game_states:
            last_state = self.current_game_states[-1]
            if last_state not in self.losing_states:
                self.losing_states.add(last_state)
                self.save_losing_states()
                print("AI added to memory! Must avoid this state to not lose.")

    def clear_history(self):
        self.current_game_states.clear()

    def get_board_hash(
        self,
        board: Board,
        my_inv: PlayerInventory,
        opp_inv: PlayerInventory,
        is_maximizing: bool,
        my_can_eat: bool,
        opp_can_eat: bool,
    ) -> str:
        board_state = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                stack = board.grid[r][c]
                if stack:
                    board_state.append(",".join(f"{p.owner}{p.size}" for p in stack))
                else:
                    board_state.append("0")

        my_p = f"{my_inv.pieces[3]}{my_inv.pieces[2]}{my_inv.pieces[1]}"
        opp_p = f"{opp_inv.pieces[3]}{opp_inv.pieces[2]}{opp_inv.pieces[1]}"

        return (
            "|".join(board_state)
            + f"|{my_p}|{opp_p}|{is_maximizing}|{my_can_eat}|{opp_can_eat}"
        )

    def get_best_move(
        self,
        board: Board,
        my_inv: PlayerInventory,
        opp_inv: PlayerInventory,
        my_can_eat: bool,
        opp_can_eat: bool,
    ) -> Optional[Tuple[int, int, int]]:
        self.transposition_table.clear()

        valid_moves = board.get_valid_moves(my_inv, my_can_eat)
        if not valid_moves:
            return None

        # Sort moves: try to place larger pieces first if possible to prune early
        def move_score(m):
            size, r, c, fr, fc = m
            score = size * 10
            if r == 1 and c == 1:
                score += 5
            if fr is not None:
                score -= 2
            return score

        valid_moves.sort(key=move_score, reverse=True)

        best_score = -math.inf
        global_best_move = None

        start_time = time.time()
        time_limit = 1.0  # 1 second target

        # Iterative Deepening
        for depth in range(1, 10):
            current_best_score = -math.inf
            current_best_move = None

            try:
                for move in valid_moves:
                    size, r, c, fr, fc = move

                    # --- MAKE MOVE START ---
                    moving_piece = None
                    if fr is not None and fc is not None:
                        moving_piece = board.get_top_piece(fr, fc)
                        board.grid[fr][fc].pop()
                    else:
                        my_inv.use_piece(size)

                    top = board.get_top_piece(r, c)
                    is_eating = top is not None
                    if top:
                        board.grid[r][c].pop()
                        if top.owner == self.player_id:
                            my_inv.unuse_piece(top.size)
                        else:
                            opp_inv.unuse_piece(top.size)

                    board.grid[r][c].append(Piece(self.player_id, size))
                    # --- MAKE MOVE END ---

                    try:
                        # Recursive Call
                        score = self.minimax(
                            board,
                            my_inv,
                            opp_inv,
                            depth - 1,
                            False,
                            -math.inf,
                            math.inf,
                            start_time,
                            time_limit,
                            not is_eating,
                            opp_can_eat,
                        )

                        if score > current_best_score:
                            current_best_score = score
                            current_best_move = move

                    finally:
                        # --- UNDO MOVE (Must always run) ---
                        board.grid[r][c].pop()
                        if top:
                            board.grid[r][c].append(top)
                            if top.owner == self.player_id:
                                my_inv.use_piece(top.size)
                            else:
                                opp_inv.use_piece(top.size)

                        if fr is not None and fc is not None:
                            board.grid[fr][fc].append(moving_piece)
                        else:
                            my_inv.unuse_piece(size)
                        # --- UNDO MOVE END ---

                # If loop completes without timeout
                global_best_move = current_best_move
                best_score = current_best_score

                # Reorder valid_moves so best_move is explored first in next depth
                if current_best_move in valid_moves:
                    valid_moves.remove(current_best_move)
                    valid_moves.insert(0, current_best_move)

                if best_score > 90000:
                    break

            except TimeoutException:
                # Time limit reached, stop searching deeper
                break

        if global_best_move is None and valid_moves:
            global_best_move = valid_moves[0]

        return global_best_move

    def minimax(
        self,
        board: Board,
        my_inv: PlayerInventory,
        opp_inv: PlayerInventory,
        depth: int,
        is_maximizing: bool,
        alpha: float,
        beta: float,
        start_time: float,
        time_limit: float,
        my_can_eat: bool,
        opp_can_eat: bool,
    ) -> float:
        if time.time() - start_time > time_limit:
            raise TimeoutException()

        win_res = board.check_win()
        winner = win_res[0] if win_res else None

        if winner == self.player_id:
            return 100000 + depth
        elif winner == self.opponent_id:
            return -100000 - depth
        elif depth == 0:
            return self.evaluate_board(board)

        state_hash = self.get_board_hash(
            board, my_inv, opp_inv, is_maximizing, my_can_eat, opp_can_eat
        )

        # Avoid known losing states
        if not is_maximizing and state_hash in self.losing_states:
            return -90000 - depth
        if state_hash in self.transposition_table:
            stored_depth, stored_score, flag = self.transposition_table[state_hash]
            if stored_depth >= depth:
                if flag == "EXACT":
                    return stored_score
                elif flag == "LOWERBOUND" and stored_score > alpha:
                    alpha = stored_score
                elif flag == "UPPERBOUND" and stored_score < beta:
                    beta = stored_score
                if alpha >= beta:
                    return stored_score

        if is_maximizing:
            alpha_orig = alpha
            max_eval = -math.inf
            moves = board.get_valid_moves(my_inv, my_can_eat)
            if not moves:
                score = self.evaluate_board(board)
                self.transposition_table[state_hash] = (depth, score, "EXACT")
                return score

            def move_score_max(m):
                s, r, c, fr, fc = m
                return (
                    s * 10
                    + (5 if r == 1 and c == 1 else 0)
                    - (2 if fr is not None else 0)
                )

            moves.sort(key=move_score_max, reverse=True)

            for move in moves:
                size, r, c, fr, fc = move

                # Make Move
                moving_piece = None
                if fr is not None and fc is not None:
                    moving_piece = board.get_top_piece(fr, fc)
                    board.grid[fr][fc].pop()
                else:
                    my_inv.use_piece(size)

                top = board.get_top_piece(r, c)
                is_eating = top is not None
                if top:
                    board.grid[r][c].pop()
                    if top.owner == self.player_id:
                        my_inv.unuse_piece(top.size)
                    else:
                        opp_inv.unuse_piece(top.size)

                board.grid[r][c].append(Piece(self.player_id, size))

                try:
                    eval_score = self.minimax(
                        board,
                        my_inv,
                        opp_inv,
                        depth - 1,
                        False,
                        alpha,
                        beta,
                        start_time,
                        time_limit,
                        not is_eating,
                        opp_can_eat,
                    )
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                finally:
                    # Undo Move (Always runs)
                    board.grid[r][c].pop()
                    if top:
                        board.grid[r][c].append(top)
                        if top.owner == self.player_id:
                            my_inv.use_piece(top.size)
                        else:
                            opp_inv.use_piece(top.size)

                    if fr is not None and fc is not None:
                        board.grid[fr][fc].append(moving_piece)
                    else:
                        my_inv.unuse_piece(size)

                if beta <= alpha:
                    break

            if max_eval <= alpha_orig:
                flag = "UPPERBOUND"
            elif max_eval >= beta:
                flag = "LOWERBOUND"
            else:
                flag = "EXACT"

            self.transposition_table[state_hash] = (depth, max_eval, flag)
            return max_eval
        else:
            beta_orig = beta
            min_eval = math.inf
            moves = board.get_valid_moves(opp_inv, opp_can_eat)
            if not moves:
                score = self.evaluate_board(board)
                self.transposition_table[state_hash] = (depth, score, "EXACT")
                return score

            def move_score_min(m):
                s, r, c, fr, fc = m
                return (
                    s * 10
                    + (5 if r == 1 and c == 1 else 0)
                    - (2 if fr is not None else 0)
                )

            moves.sort(key=move_score_min, reverse=True)

            for move in moves:
                size, r, c, fr, fc = move

                # Make Move
                moving_piece = None
                if fr is not None and fc is not None:
                    moving_piece = board.get_top_piece(fr, fc)
                    board.grid[fr][fc].pop()
                else:
                    opp_inv.use_piece(size)

                top = board.get_top_piece(r, c)
                is_eating = top is not None
                if top:
                    board.grid[r][c].pop()
                    if top.owner == self.player_id:
                        my_inv.unuse_piece(top.size)
                    else:
                        opp_inv.unuse_piece(top.size)

                board.grid[r][c].append(Piece(self.opponent_id, size))

                try:
                    eval_score = self.minimax(
                        board,
                        my_inv,
                        opp_inv,
                        depth - 1,
                        True,
                        alpha,
                        beta,
                        start_time,
                        time_limit,
                        my_can_eat,
                        not is_eating,
                    )
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                finally:
                    # Undo Move (Always runs)
                    board.grid[r][c].pop()
                    if top:
                        board.grid[r][c].append(top)
                        if top.owner == self.player_id:
                            my_inv.use_piece(top.size)
                        else:
                            opp_inv.use_piece(top.size)

                    if fr is not None and fc is not None:
                        board.grid[fr][fc].append(moving_piece)
                    else:
                        opp_inv.unuse_piece(size)

                if beta <= alpha:
                    break

            if min_eval <= alpha:
                flag = "UPPERBOUND"
            elif min_eval >= beta_orig:
                flag = "LOWERBOUND"
            else:
                flag = "EXACT"

            self.transposition_table[state_hash] = (depth, min_eval, flag)
            return min_eval

    def evaluate_board(self, board: Board) -> float:
        score = 0

        # 1. Piece Control
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                top = board.get_top_piece(r, c)
                if top:
                    multiplier = 1
                    if r == 1 and c == 1:
                        multiplier = 2.0
                    elif (r, c) in [(0, 0), (0, 2), (2, 0), (2, 2)]:
                        multiplier = 1.2

                    piece_score = (top.size**2) * 5 * multiplier

                    if top.owner == self.player_id:
                        score += piece_score
                    else:
                        score -= piece_score

        # 2. Threat analysis
        score += self._evaluate_lines(board, self.player_id) * 20
        score -= self._evaluate_lines(board, self.opponent_id) * 20

        return score

    def _evaluate_lines(self, board: Board, player: int) -> float:
        score = 0

        def count_line(p1, p2, p3):
            count = 0
            max_size = 0
            for p in [p1, p2, p3]:
                if p and p.owner == player:
                    count += 1
                    max_size = max(max_size, p.size)
            return count, max_size

        lines = [
            [(0, 0), (0, 1), (0, 2)],
            [(1, 0), (1, 1), (1, 2)],
            [(2, 0), (2, 1), (2, 2)],  # Rows
            [(0, 0), (1, 0), (2, 0)],
            [(0, 1), (1, 1), (2, 1)],
            [(0, 2), (1, 2), (2, 2)],  # Cols
            [(0, 0), (1, 1), (2, 2)],
            [(0, 2), (1, 1), (2, 0)],  # Diags
        ]

        for line in lines:
            p1 = board.get_top_piece(line[0][0], line[0][1])
            p2 = board.get_top_piece(line[1][0], line[1][1])
            p3 = board.get_top_piece(line[2][0], line[2][1])

            opp = self.opponent_id if player == self.player_id else self.player_id
            blocked = False
            for p in [p1, p2, p3]:
                if p and p.owner == opp:
                    blocked = True
                    break

            if not blocked:
                c, max_size = count_line(p1, p2, p3)
                if c == 2:
                    score += 15 + max_size * 5
                elif c == 1:
                    score += 2 + max_size * 2

        return score
