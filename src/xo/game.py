import pygame
import random
from typing import Optional
from xo.constants import (
    BG_COLOR,
    BLACK,
    BOARD_SIZE,
    FPS,
    PLAYER_O,
    PLAYER_X,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STATE_GAME_OVER,
    STATE_MENU,
    STATE_PLAYING_PVE,
    STATE_PLAYING_PVP_CLIENT,
    STATE_PLAYING_PVP_HOST,
    STATE_ENTER_USERNAME_HOST,
    STATE_ENTER_USERNAME_CLIENT,
    STATE_LOBBY_HOST,
    STATE_LOBBY_CLIENT,
    STATE_ROOM_LIST_CLIENT,
)
from xo.models import Board, PlayerInventory, Piece
from xo.ui import UIManager
from xo.network import NetworkManager, RoomBroadcaster, RoomListener


from core.Pygame import Pygame
from xo.players import Player, HumanPlayer, AIPlayer

class GameController(Pygame):
    def __init__(self):
        super().__init__(title="3x3 XO with Sizes", width=SCREEN_WIDTH, height=SCREEN_HEIGHT, fps=FPS)
        self.ui = UIManager(self.screen)

        self.state = STATE_MENU

        self.board = None
        self.inv_p1 = None
        self.inv_p2 = None
        self.current_turn = None
        self.selected_size = None
        self.selected_from_board = None  # (r, c)
        self.winner = None
        self.win_reason = ""
        self.game_over_timer = None
        self.can_eat = {PLAYER_X: True, PLAYER_O: True}

        self.player_x: Optional[Player] = None
        self.player_o: Optional[Player] = None
        
        self.network = None
        self.player_username = ""
        self.opponent_username = None
        self.username_input = ""
        self.is_username_active = False
        self.join_sent = False
        self.broadcaster = None
        self.listener = None
        self.ai_think_start = None

    def reset_game(self, pve=False, is_host=False, is_client=False, ip="127.0.0.1"):
        if self.network:
            self.network.close()
            self.network = None
        if self.broadcaster:
            self.broadcaster.stop()
            self.broadcaster = None
        if self.listener:
            self.listener.stop()
            self.listener = None

        self.board = Board()
        self.inv_p1 = PlayerInventory(PLAYER_X)
        self.inv_p2 = PlayerInventory(PLAYER_O)

        if pve:
            self.current_turn = random.choice([PLAYER_X, PLAYER_O])
            self.player_x = HumanPlayer(PLAYER_X, "Player X")
            self.player_o = AIPlayer(PLAYER_O, "AI")
        else:
            self.current_turn = PLAYER_X
            self.player_x = HumanPlayer(PLAYER_X, self.player_username)
            self.player_o = HumanPlayer(PLAYER_O, "Opponent") # Placeholder for PvP

        self.selected_size = None
        self.selected_from_board = None
        self.winner = None
        self.win_reason = ""
        self.game_over_timer = None
        self.can_eat = {PLAYER_X: True, PLAYER_O: True}
        self.ai_think_start = None

        if not pve:
            self.opponent_username = None
            self.join_sent = False
            if is_host:
                self.network = NetworkManager(is_host=True)
                self.broadcaster = RoomBroadcaster(self.player_username)
                self.broadcaster.start()
                self.state = STATE_LOBBY_HOST
            elif is_client:
                if ip != "127.0.0.1":
                    self.network = NetworkManager(is_host=False, ip=ip)
                    self.state = STATE_LOBBY_CLIENT
                else:
                    self.listener = RoomListener()
                    self.listener.start()
                    self.state = STATE_ROOM_LIST_CLIENT

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.network:
                    self.network.close()
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(mouse_pos)

            if event.type == pygame.KEYDOWN:
                if (
                    self.state
                    in (STATE_ENTER_USERNAME_HOST, STATE_ENTER_USERNAME_CLIENT)
                    and self.is_username_active
                ):
                    if event.key == pygame.K_BACKSPACE:
                        self.username_input = self.username_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        if self.username_input.strip() != "":
                            self.player_username = self.username_input.strip()
                            if self.state == STATE_ENTER_USERNAME_HOST:
                                self.reset_game(is_host=True)
                            else:
                                self.reset_game(is_client=True, ip="127.0.0.1")
                    else:
                        if len(self.username_input) < 15:
                            self.username_input += event.unicode

    def update(self):
        # Handle network sync
        if self.network and self.network.connected:
            if self.state == STATE_LOBBY_CLIENT and not self.join_sent:
                self.network.send({"type": "join", "username": self.player_username})
                self.join_sent = True

            data = self.network.get_data()
            while data is not None:
                if self.state == STATE_LOBBY_HOST:
                    if isinstance(data, dict) and data.get("type") == "join":
                        self.opponent_username = data.get("username", "Unknown")
                        if self.player_o:
                            self.player_o.username = self.opponent_username
                elif self.state == STATE_LOBBY_CLIENT:
                    if isinstance(data, dict):
                        if data.get("type") == "accept":
                            self.opponent_username = data.get("host_username", "Host")
                            if self.player_x:
                                self.player_x.username = self.opponent_username
                            self.state = STATE_PLAYING_PVP_CLIENT
                        elif data.get("type") == "reject":
                            self.network.close()
                            self.network = None
                            self.state = STATE_MENU
                else:
                    if isinstance(data, dict) and "board" in data:
                        self.board = data["board"]
                        self.inv_p1 = data["inv_p1"]
                        self.inv_p2 = data["inv_p2"]
                        self.current_turn = data["turn"]
                        if "can_eat" in data:
                            self.can_eat = data["can_eat"]
                        self.check_game_over()
                        if self.winner is not None or self.win_reason:
                            if self.game_over_timer is None:
                                self.game_over_timer = pygame.time.get_ticks()
                data = self.network.get_data()

        # Check if current player has no valid moves (prevent hanging)
        if (
            self.state
            in (STATE_PLAYING_PVE, STATE_PLAYING_PVP_HOST, STATE_PLAYING_PVP_CLIENT)
            and self.winner is None
        ):
            active_inv = self.inv_p1 if self.current_turn == PLAYER_X else self.inv_p2
            if not self.board.get_valid_moves(active_inv):
                # Only automatically skip/draw if it's not the AI's turn (AI handles its own skip)
                if not (
                    self.state == STATE_PLAYING_PVE and self.current_turn == PLAYER_O
                ):
                    other_inv = (
                        self.inv_p2 if self.current_turn == PLAYER_X else self.inv_p1
                    )
                    if not self.board.get_valid_moves(other_inv):
                        self.winner = None
                        self.win_reason = "ไม่มีใครเดินต่อได้"
                        self.game_over_timer = pygame.time.get_ticks()
                    else:
                        # Skip turn
                        self.current_turn = (
                            PLAYER_O if self.current_turn == PLAYER_X else PLAYER_X
                        )
                        if self.network and self.network.connected:
                            self.network.send(
                                {
                                    "board": self.board,
                                    "inv_p1": self.inv_p1,
                                    "inv_p2": self.inv_p2,
                                    "turn": self.current_turn,
                                    "can_eat": self.can_eat,
                                }
                            )

        # Handle AI (Polymorphism in action)
        if (
            self.state == STATE_PLAYING_PVE
            and self.current_turn == PLAYER_O
            and self.game_over_timer is None
            and isinstance(self.player_o, AIPlayer)
        ):
            if self.ai_think_start is None:
                self.ai_think_start = pygame.time.get_ticks()

            if pygame.time.get_ticks() - self.ai_think_start > 800:  # 800ms delay
                move = self.player_o.get_move(
                    self.board,
                    self.inv_p2,
                    self.inv_p1,
                    self.can_eat[PLAYER_O],
                    self.can_eat[PLAYER_X],
                )
                if move:
                    size, r, c, fr, fc = move

                    if fr is not None and fc is not None:
                        # Moving piece from board
                        self.board.remove_top_piece(fr, fc)
                    else:
                        # Using piece from inventory
                        self.inv_p2.use_piece(size)

                    top = self.board.get_top_piece(r, c)
                    is_eating = top is not None
                    if top:
                        self.board.remove_top_piece(r, c)
                        if top.owner == PLAYER_X:
                            self.inv_p1.unuse_piece(top.size)
                        else:
                            self.inv_p2.unuse_piece(top.size)

                    self.board.place_piece(r, c, Piece(PLAYER_O, size))

                    self.can_eat[PLAYER_O] = not is_eating

                    # Record state for learning
                    self.player_o.record_state(
                        self.board, self.inv_p2, self.inv_p1, self.can_eat[PLAYER_O]
                    )

                    self.current_turn = PLAYER_X
                    self.check_game_over()
                    if self.winner is not None or self.win_reason:
                        self.game_over_timer = pygame.time.get_ticks()
                else:
                    # pass turn if no moves
                    moves_p1 = self.board.get_valid_moves(self.inv_p1)
                    if not moves_p1:
                        self.winner = None
                        self.win_reason = "ไม่มีใครเดินต่อได้"
                        self.game_over_timer = pygame.time.get_ticks()
                    else:
                        self.current_turn = PLAYER_X
                self.ai_think_start = None

        # Handle the delay before state transition
        if self.game_over_timer is not None:
            if pygame.time.get_ticks() - self.game_over_timer > 3000:
                self.state = STATE_GAME_OVER
                self.game_over_timer = None

    def draw(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.state == STATE_MENU:
            self.ui.draw_menu(mouse_pos)
        elif self.state == STATE_ENTER_USERNAME_HOST:
            self.ui.draw_enter_username(
                "Host Game", self.username_input, self.is_username_active, mouse_pos
            )
        elif self.state == STATE_ENTER_USERNAME_CLIENT:
            self.ui.draw_enter_username(
                "Join Game", self.username_input, self.is_username_active, mouse_pos
            )
        elif self.state == STATE_ROOM_LIST_CLIENT:
            rooms = self.listener.get_rooms() if self.listener else []
            self.ui.draw_room_list(rooms, mouse_pos)
        elif self.state == STATE_LOBBY_HOST:
            self.ui.draw_lobby_host(
                self.player_username, self.opponent_username, mouse_pos
            )
        elif self.state == STATE_LOBBY_CLIENT:
            status = (
                "Connected, waiting for host..."
                if (self.network and self.network.connected)
                else "Connecting to Host..."
            )
            self.ui.draw_lobby_client(self.opponent_username, status, mouse_pos)
        elif self.state in (
            STATE_PLAYING_PVE,
            STATE_PLAYING_PVP_HOST,
            STATE_PLAYING_PVP_CLIENT,
            STATE_GAME_OVER,
        ):
            self.screen.fill(BG_COLOR)

            # Compute moves to highlight (only if not game over)
            valid_normal_cells = []
            valid_eat_cells = []
            if self.state != STATE_GAME_OVER and self.selected_size is not None:
                active_can_eat = self.can_eat[self.current_turn]
                if self.selected_from_board:
                    fr, fc = self.selected_from_board
                    moving_piece = self.board.get_top_piece(fr, fc)
                    self.board.remove_top_piece(fr, fc)
                    for r in range(BOARD_SIZE):
                        for c in range(BOARD_SIZE):
                            if (fr, fc) != (r, c) and self.board.is_valid_move(
                                r,
                                c,
                                self.selected_size,
                                self.current_turn,
                                active_can_eat,
                            ):
                                if self.board.get_top_piece(r, c) is not None:
                                    valid_eat_cells.append((r, c))
                                else:
                                    valid_normal_cells.append((r, c))
                    self.board.place_piece(fr, fc, moving_piece)
                else:
                    for r in range(BOARD_SIZE):
                        for c in range(BOARD_SIZE):
                            if self.board.is_valid_move(
                                r,
                                c,
                                self.selected_size,
                                self.current_turn,
                                active_can_eat,
                            ):
                                if self.board.get_top_piece(r, c) is not None:
                                    valid_eat_cells.append((r, c))
                                else:
                                    valid_normal_cells.append((r, c))

            self.ui.draw_board(
                self.board,
                self.selected_from_board,
                valid_moves=valid_normal_cells,
                eat_moves=valid_eat_cells,
            )
            self.ui.draw_inventory(
                self.inv_p1, self.inv_p2, self.current_turn, self.selected_size
            )

            # Turn status/Game over text
            if self.state == STATE_GAME_OVER:
                self.ui.draw_game_over(self.winner, self.win_reason, mouse_pos)
            elif self.state == STATE_PLAYING_PVP_HOST and not self.network.connected:
                self.ui.draw_text(
                    "Waiting for Client to connect...",
                    self.ui.font_m,
                    RED,
                    SCREEN_WIDTH // 2,
                    30,
                )
            elif (
                self.state == STATE_PLAYING_PVP_CLIENT
                and not self.network.connected
            ):
                self.ui.draw_text(
                    "Connecting to Host...",
                    self.ui.font_m,
                    RED,
                    SCREEN_WIDTH // 2,
                    30,
                )
            elif (
                self.state == STATE_PLAYING_PVP_HOST
                and self.current_turn == PLAYER_O
            ):
                status_msg = f"Waiting for {self.opponent_username or 'Client'}'s move..."
                self.ui.draw_text(
                    status_msg,
                    self.ui.font_m,
                    BLACK,
                    SCREEN_WIDTH // 2,
                    30,
                )
            elif (
                self.state == STATE_PLAYING_PVP_CLIENT
                and self.current_turn == PLAYER_X
            ):
                status_msg = f"Waiting for {self.opponent_username or 'Host'}'s move..."
                self.ui.draw_text(
                    status_msg,
                    self.ui.font_m,
                    BLACK,
                    SCREEN_WIDTH // 2,
                    30,
                )
            elif self.state == STATE_PLAYING_PVE and self.current_turn == PLAYER_O:
                self.ui.draw_text(
                    "AI is thinking...",
                    self.ui.font_m,
                    BLACK,
                    SCREEN_WIDTH // 2,
                    30,
                )

        pygame.display.flip()

    def handle_click(self, mouse_pos):
        if self.state == STATE_MENU:
            new_state = self.ui.get_menu_click(mouse_pos)
            if new_state:
                if new_state == STATE_PLAYING_PVE:
                    self.state = new_state
                    self.reset_game(pve=True)
                else:
                    self.state = new_state
                    self.username_input = ""
                    self.is_username_active = False

        elif self.state in (STATE_ENTER_USERNAME_HOST, STATE_ENTER_USERNAME_CLIENT):
            action = self.ui.get_enter_username_click(mouse_pos)
            if action == "box":
                self.is_username_active = True
            else:
                self.is_username_active = False

            if action == "back":
                self.state = STATE_MENU
            elif action == "confirm":
                if self.username_input.strip() != "":
                    self.player_username = self.username_input.strip()
                    if self.state == STATE_ENTER_USERNAME_HOST:
                        self.reset_game(is_host=True)
                    else:
                        self.reset_game(is_client=True, ip="127.0.0.1")

        elif self.state == STATE_ROOM_LIST_CLIENT:
            rooms = self.listener.get_rooms() if self.listener else []
            action = self.ui.get_room_list_click(rooms, mouse_pos)
            if action == "back":
                if self.listener:
                    self.listener.stop()
                    self.listener = None
                self.state = STATE_MENU
            elif isinstance(action, dict):
                # We clicked a room
                if self.listener:
                    self.listener.stop()
                    self.listener = None
                self.reset_game(is_client=True, ip=action["ip"])

        elif self.state == STATE_LOBBY_HOST:
            action = self.ui.get_lobby_host_click(
                mouse_pos, bool(self.opponent_username)
            )
            if action == "back":
                if self.network:
                    self.network.close()
                    self.network = None
                self.state = STATE_MENU
            elif action == "accept":
                if self.network and self.network.connected:
                    self.network.send(
                        {"type": "accept", "host_username": self.player_username}
                    )
                    if self.broadcaster:
                        self.broadcaster.stop()
                        self.broadcaster = None
                    self.state = STATE_PLAYING_PVP_HOST
            elif action == "reject":
                if self.network and self.network.connected:
                    self.network.send({"type": "reject"})
                self.opponent_username = None

        elif self.state == STATE_LOBBY_CLIENT:
            action = self.ui.get_lobby_client_click(mouse_pos)
            if action == "back":
                if self.network:
                    self.network.close()
                    self.network = None
                self.state = STATE_MENU

        elif self.state in (
            STATE_PLAYING_PVE,
            STATE_PLAYING_PVP_HOST,
            STATE_PLAYING_PVP_CLIENT,
        ):
            if self.game_over_timer is not None:
                return

            my_turn = False
            # Can only play if network is connected (or offline PVE)
            if self.state == STATE_PLAYING_PVE and self.current_turn == PLAYER_X:
                my_turn = True
            elif (
                self.state == STATE_PLAYING_PVP_HOST
                and self.current_turn == PLAYER_X
                and self.network
                and self.network.connected
            ):
                my_turn = True
            elif (
                self.state == STATE_PLAYING_PVP_CLIENT
                and self.current_turn == PLAYER_O
                and self.network
                and self.network.connected
            ):
                my_turn = True

            if my_turn:
                # 1. Click inventory to select size
                clicked_size = self.ui.get_inventory_click(mouse_pos, self.current_turn)
                if clicked_size is not None:
                    active_inv = (
                        self.inv_p1 if self.current_turn == PLAYER_X else self.inv_p2
                    )
                    if active_inv.has_piece(clicked_size):
                        self.selected_size = clicked_size
                        self.selected_from_board = None

                # 2. Click board
                else:
                    board_click = self.ui.get_board_click(mouse_pos)
                    if board_click:
                        r, c = board_click
                        active_inv = (
                            self.inv_p1
                            if self.current_turn == PLAYER_X
                            else self.inv_p2
                        )

                        # A. Select piece from board
                        top = self.board.get_top_piece(r, c)
                        if (
                            self.selected_size is None
                            and top
                            and top.owner == self.current_turn
                        ):
                            self.selected_size = top.size
                            self.selected_from_board = (r, c)

                        # B. Place piece
                        elif self.selected_size is not None:
                            # if we are moving a piece, we momentarily remove it to check validity
                            is_move = self.selected_from_board is not None
                            moving_piece = None

                            if is_move:
                                fr, fc = self.selected_from_board
                                if (fr, fc) == (r, c):
                                    # clicked same spot, deselect
                                    self.selected_size = None
                                    self.selected_from_board = None
                                    pass
                                else:
                                    moving_piece = self.board.get_top_piece(fr, fc)
                                    self.board.remove_top_piece(fr, fc)

                            active_can_eat = self.can_eat[self.current_turn]
                            if (
                                self.selected_size is not None
                                and self.board.is_valid_move(
                                    r,
                                    c,
                                    self.selected_size,
                                    self.current_turn,
                                    active_can_eat,
                                )
                            ):
                                # Handle eaten pieces
                                target_top = self.board.get_top_piece(r, c)
                                is_eating = target_top is not None
                                if target_top:
                                    self.board.remove_top_piece(r, c)
                                    if target_top.owner == PLAYER_X:
                                        self.inv_p1.unuse_piece(target_top.size)
                                    else:
                                        self.inv_p2.unuse_piece(target_top.size)

                                # Make move
                                piece = Piece(self.current_turn, self.selected_size)
                                self.board.place_piece(r, c, piece)

                                if not is_move:
                                    active_inv.use_piece(self.selected_size)

                                self.can_eat[self.current_turn] = not is_eating

                                self.selected_size = None
                                self.selected_from_board = None

                                self.current_turn = (
                                    PLAYER_O
                                    if self.current_turn == PLAYER_X
                                    else PLAYER_X
                                )

                                if self.network and self.network.connected:
                                    self.network.send(
                                        {
                                            "board": self.board,
                                            "inv_p1": self.inv_p1,
                                            "inv_p2": self.inv_p2,
                                            "turn": self.current_turn,
                                            "can_eat": self.can_eat,
                                        }
                                    )

                                self.check_game_over()
                                if self.winner is not None or self.win_reason:
                                    self.game_over_timer = pygame.time.get_ticks()
                            else:
                                # Invalid move
                                if is_move and moving_piece:
                                    self.board.place_piece(
                                        self.selected_from_board[0],
                                        self.selected_from_board[1],
                                        moving_piece,
                                    )
                                self.selected_size = None
                                self.selected_from_board = None

        elif self.state == STATE_GAME_OVER:
            action = self.ui.get_game_over_click(mouse_pos)
            if action == STATE_MENU:
                self.state = STATE_MENU

    def check_game_over(self):
        win_res = self.board.check_win()
        if win_res:
            self.winner, self.win_reason = win_res
            if isinstance(self.player_o, AIPlayer):
                if self.winner == PLAYER_X:
                    self.player_o.learn_from_loss()
                else:
                    self.player_o.clear_history()
            return

        moves_p1 = self.board.get_valid_moves(self.inv_p1)
        moves_p2 = self.board.get_valid_moves(self.inv_p2)
        if not moves_p1 and not moves_p2:
            self.winner = None
            self.win_reason = "ไม่มีใครเดินต่อได้"
            if isinstance(self.player_o, AIPlayer):
                self.player_o.clear_history()
