import pygame
from typing import Tuple, Optional
from xo.models import Board, Piece, PlayerInventory
from xo.constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BG_COLOR,
    TEXT_COLOR,
    SUBTEXT_COLOR,
    COLOR_P1,
    COLOR_P2,
    COLOR_P1_DARK,
    COLOR_P2_DARK,
    COLOR_SUCCESS,
    COLOR_DANGER,
    SHADOW_COLOR,
    SIZE_LARGE,
    SIZE_MEDIUM,
    SIZE_SMALL,
    COLOR_P1_LIGHT,
    COLOR_P2_LIGHT,
    STATE_PLAYING_PVE,
    STATE_ENTER_USERNAME_HOST,
    STATE_ENTER_USERNAME_CLIENT,
    BOARD_SLOT_COLOR,
    BOARD_OFFSET_X,
    BOARD_OFFSET_Y,
    BOARD_SIZE,
    CELL_SIZE,
    BOARD_BG_COLOR,
    COLOR_WARNING,
    PLAYER_X,
    PLAYER_O,
    STATE_MENU,
)


class UIManager:
    def __init__(self, screen):
        self.screen = screen
        pygame.font.init()

        # Load Fonts (Try to use system fonts that look modern)
        import os

        # Custom explicit font mappings for Thai support
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        reg_font = os.path.join(assets_dir, "Sarabun-Regular.ttf")
        bold_font = os.path.join(assets_dir, "Sarabun-Bold.ttf")

        try:
            self.font_title = pygame.font.Font(bold_font, 64)
            self.font_l = pygame.font.Font(bold_font, 48)
            self.font_m = pygame.font.Font(reg_font, 28)
            self.font_s = pygame.font.Font(reg_font, 20)
            self.font_bold = pygame.font.Font(bold_font, 28)
        except Exception:
            # Fallback to standard fonts with Thai support (macOS/Windows)
            fallback_fonts = "segoeui,tahoma,thonburi,sukhumvitset,arial"
            self.font_title = pygame.font.SysFont(fallback_fonts, 64, bold=True)
            self.font_l = pygame.font.SysFont(fallback_fonts, 48, bold=True)
            self.font_m = pygame.font.SysFont(fallback_fonts, 28)
            self.font_s = pygame.font.SysFont(fallback_fonts, 20)
            self.font_bold = pygame.font.SysFont(fallback_fonts, 28, bold=True)

        # Pre-render assets can be done here if needed

    # --- HELPER FUNCTIONS ---
    def _draw_shadow(self, rect, radius=15, offset_y=4):
        """Draws a soft shadow under an element"""
        shadow_rect = rect.copy()
        shadow_rect.y += offset_y
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, SHADOW_COLOR, s.get_rect(), border_radius=radius)
        self.screen.blit(s, shadow_rect.topleft)

    def _draw_rounded_rect(
        self, rect, color, radius=15, border_width=0, border_color=None
    ):
        """Draws a modern rounded rectangle"""
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)
        if border_width > 0 and border_color:
            pygame.draw.rect(
                self.screen,
                border_color,
                rect,
                width=border_width,
                border_radius=radius,
            )

    def draw_text(self, text, font, color, x, y, center=True, shadow=False):
        if shadow:
            shadow_surf = font.render(text, True, (0, 0, 0, 20))
            shadow_rect = shadow_surf.get_rect()
            if center:
                shadow_rect.center = (x + 2, y + 2)
            else:
                shadow_rect.topleft = (x + 2, y + 2)
            self.screen.blit(shadow_surf, shadow_rect)

        surface = font.render(text, True, color)
        rect = surface.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surface, rect)

    def draw_button(self, rect, text, base_color, mouse_pos, icon=None):
        """Draws a highly interactive button"""
        is_hover = rect.collidepoint(mouse_pos)

        # Color Calculation based on hover
        if is_hover:
            # Lighten the color slightly
            r = min(255, base_color[0] + 20)
            g = min(255, base_color[1] + 20)
            b = min(255, base_color[2] + 20)
            color = (r, g, b)
            offset_y = 2  # Click feel (move down slightly if we had click state, but hover up is also good)
            shadow_offset = 2
        else:
            color = base_color
            offset_y = 0
            shadow_offset = 5

        # Draw Shadow
        shadow_rect = rect.copy()
        shadow_rect.y += shadow_offset
        pygame.draw.rect(self.screen, (200, 200, 210), shadow_rect, border_radius=12)

        # Draw Button Body
        draw_rect = rect.copy()
        draw_rect.y += offset_y
        self._draw_rounded_rect(draw_rect, color, radius=12)

        # Draw Text
        self.draw_text(
            text,
            self.font_m,
            (255, 255, 255),
            draw_rect.centerx,
            draw_rect.centery,
            shadow=True,
        )

        return is_hover

    # --- SCENE DRAWING ---

    def draw_menu(self, mouse_pos):
        self.screen.fill(BG_COLOR)

        # --- ย้ายมาวาดตรงนี้ (วาดพื้นหลังและของตกแต่งก่อน) ---
        # Decorative circles in background (optional aesthetic)
        # วาดก่อน เพื่อให้อยู่ข้างหลังตัวหนังสือ
        pygame.draw.circle(self.screen, COLOR_P1_LIGHT, (100, 100), 150)
        pygame.draw.circle(
            self.screen, COLOR_P2_LIGHT, (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 50), 200
        )
        # ------------------------------------------------

        # --- แล้วค่อยวาดตัวหนังสือทับลงไป ---
        # Title with accent
        self.draw_text(
            "GOBBLET XO",
            self.font_title,
            COLOR_P1_DARK,
            SCREEN_WIDTH // 2,
            120,
            shadow=True,
        )
        self.draw_text(
            "Tactical Tic-Tac-Toe", self.font_m, SUBTEXT_COLOR, SCREEN_WIDTH // 2, 170
        )

        # Buttons
        center_x = SCREEN_WIDTH // 2
        btn_width = 320
        btn_height = 65
        gap = 20
        start_y = 280

        btn_pve = pygame.Rect(center_x - btn_width // 2, start_y, btn_width, btn_height)
        btn_host = pygame.Rect(
            center_x - btn_width // 2, start_y + btn_height + gap, btn_width, btn_height
        )
        btn_join = pygame.Rect(
            center_x - btn_width // 2,
            start_y + (btn_height + gap) * 2,
            btn_width,
            btn_height,
        )

        self.draw_button(btn_pve, "เล่นกับ AI (Play vs AI)", COLOR_P1, mouse_pos)
        self.draw_button(btn_host, "สร้างห้อง (Host Game)", COLOR_SUCCESS, mouse_pos)
        self.draw_button(btn_join, "เข้าร่วมเกม (Join Game)", COLOR_P2, mouse_pos)

    def get_menu_click(self, mouse_pos) -> Optional[int]:
        center_x = SCREEN_WIDTH // 2
        btn_width = 320
        btn_height = 65
        gap = 20
        start_y = 280

        btn_pve = pygame.Rect(center_x - btn_width // 2, start_y, btn_width, btn_height)
        btn_host = pygame.Rect(
            center_x - btn_width // 2, start_y + btn_height + gap, btn_width, btn_height
        )
        btn_join = pygame.Rect(
            center_x - btn_width // 2,
            start_y + (btn_height + gap) * 2,
            btn_width,
            btn_height,
        )

        if btn_pve.collidepoint(mouse_pos):
            return STATE_PLAYING_PVE
        elif btn_host.collidepoint(mouse_pos):
            return STATE_ENTER_USERNAME_HOST
        elif btn_join.collidepoint(mouse_pos):
            return STATE_ENTER_USERNAME_CLIENT
        return None

    def draw_enter_username(
        self, title_text: str, username_text: str, is_active: bool, mouse_pos
    ):
        self.screen.fill(BG_COLOR)

        card_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, 150, 500, 350)
        self._draw_shadow(card_rect)
        self._draw_rounded_rect(card_rect, (255, 255, 255), radius=20)

        self.draw_text(title_text, self.font_l, TEXT_COLOR, SCREEN_WIDTH // 2, 200)
        self.draw_text(
            "กรุณาตั้งชื่อของคุณ:", self.font_s, SUBTEXT_COLOR, SCREEN_WIDTH // 2, 250
        )

        # Input Box
        input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, 280, 400, 60)
        border_color = COLOR_P1 if is_active else BOARD_SLOT_COLOR
        pygame.draw.rect(self.screen, (250, 250, 250), input_rect, border_radius=10)
        pygame.draw.rect(self.screen, border_color, input_rect, 3, border_radius=10)

        text_surface = self.font_m.render(username_text, True, TEXT_COLOR)
        self.screen.blit(text_surface, (input_rect.x + 20, input_rect.y + 10))

        # Cursor blink
        if is_active and (pygame.time.get_ticks() // 500) % 2 == 0:
            cursor_x = input_rect.x + 20 + text_surface.get_width()
            pygame.draw.line(
                self.screen,
                TEXT_COLOR,
                (cursor_x, input_rect.y + 10),
                (cursor_x, input_rect.y + 50),
                2,
            )

        btn_confirm = pygame.Rect(SCREEN_WIDTH // 2 - 180, 380, 170, 50)
        btn_back = pygame.Rect(SCREEN_WIDTH // 2 + 10, 380, 170, 50)

        self.draw_button(btn_confirm, "ยืนยัน (OK)", COLOR_SUCCESS, mouse_pos)
        self.draw_button(btn_back, "กลับ (Back)", SUBTEXT_COLOR, mouse_pos)

    def get_enter_username_click(self, mouse_pos):
        input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, 280, 400, 60)
        btn_confirm = pygame.Rect(SCREEN_WIDTH // 2 - 180, 380, 170, 50)
        btn_back = pygame.Rect(SCREEN_WIDTH // 2 + 10, 380, 170, 50)

        if btn_confirm.collidepoint(mouse_pos):
            return "confirm"
        elif btn_back.collidepoint(mouse_pos):
            return "back"
        elif input_rect.collidepoint(mouse_pos):
            return "box"
        return None

    def draw_board(
        self, board: Board, selected_pos=None, valid_moves=None, eat_moves=None
    ):
        # Draw Board Base (Mat)
        board_area = pygame.Rect(
            BOARD_OFFSET_X - 20,
            BOARD_OFFSET_Y - 20,
            BOARD_SIZE * CELL_SIZE + 40,
            BOARD_SIZE * CELL_SIZE + 40,
        )
        self._draw_shadow(board_area, radius=25)
        self._draw_rounded_rect(board_area, BOARD_BG_COLOR, radius=25)

        # Draw Cells (Slots)
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                x = BOARD_OFFSET_X + c * CELL_SIZE
                y = BOARD_OFFSET_Y + r * CELL_SIZE
                cell_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                # Draw Slot (Inset look)
                slot_margin = 8
                slot_rect = pygame.Rect(
                    x + slot_margin,
                    y + slot_margin,
                    CELL_SIZE - slot_margin * 2,
                    CELL_SIZE - slot_margin * 2,
                )
                pygame.draw.rect(
                    self.screen, BOARD_SLOT_COLOR, slot_rect, border_radius=15
                )

                # Highlight Selected Source
                if selected_pos == (r, c):
                    pygame.draw.rect(
                        self.screen,
                        COLOR_WARNING,
                        slot_rect,
                        4,
                        border_radius=15,
                    )

                # Draw Move Hints
                if valid_moves and (r, c) in valid_moves:
                    # Small dot for empty move
                    pygame.draw.circle(self.screen, COLOR_SUCCESS, cell_rect.center, 10)
                    pygame.draw.circle(
                        self.screen, (255, 255, 255), cell_rect.center, 12, 2
                    )

                if eat_moves and (r, c) in eat_moves:
                    # Cross or danger ring for eating
                    pygame.draw.rect(
                        self.screen, COLOR_DANGER, slot_rect, 4, border_radius=15
                    )

                # Draw Pieces
                stack = board.grid[r][c]
                if stack:
                    # Draw a hint of pieces underneath? (Optional, maybe just top)
                    top_piece = stack[-1]
                    self.draw_piece(top_piece, cell_rect.centerx, cell_rect.centery)

    def draw_piece(self, piece: Piece, x: int, y: int, is_inventory=False):
        """Draws a piece that looks like a hollow cup (Gobblet)"""
        if piece.owner == PLAYER_X:
            main_color = COLOR_P1
            dark_color = COLOR_P1_DARK
        else:
            main_color = COLOR_P2
            dark_color = COLOR_P2_DARK

        # Radius sizes
        if piece.size == SIZE_LARGE:
            radius = int(CELL_SIZE * 0.42)
        elif piece.size == SIZE_MEDIUM:
            radius = int(CELL_SIZE * 0.30)
        else:
            radius = int(CELL_SIZE * 0.18)

        # 1. Shadow
        if not is_inventory:  # Inventory pieces are static
            pygame.draw.circle(self.screen, SHADOW_COLOR, (x, y + 4), radius)

        # 2. Main Body
        pygame.draw.circle(self.screen, main_color, (x, y), radius)

        # 3. Rim/Thickness (Darker inner circle)
        thickness = 4 + piece.size * 2
        pygame.draw.circle(self.screen, dark_color, (x, y), radius - thickness)

        # 4. Hollow Center (White or Board Color to simulate hole)
        # If it's a cup, the inside bottom should be visible.
        # Let's just make it a slightly darker shade of main color to imply depth
        inner_color = (main_color[0] * 0.8, main_color[1] * 0.8, main_color[2] * 0.8)
        pygame.draw.circle(self.screen, inner_color, (x, y), radius - thickness - 2)

        # 5. Shine/Reflection
        shine_pos = (x - radius // 3, y - radius // 3)
        pygame.draw.circle(self.screen, (255, 255, 255, 100), shine_pos, radius // 4)

    def draw_inventory(
        self,
        inv1: PlayerInventory,
        inv2: PlayerInventory,
        current_turn: int,
        selected_size: Optional[int],
    ):
        # Draw Inventory Background Panels
        panel_width = 140
        p1_panel = pygame.Rect(10, 100, panel_width, SCREEN_HEIGHT - 200)
        p2_panel = pygame.Rect(
            SCREEN_WIDTH - panel_width - 10, 100, panel_width, SCREEN_HEIGHT - 200
        )

        # Highlight Active Player Panel
        if current_turn == PLAYER_X:
            self._draw_rounded_rect(
                p1_panel,
                (240, 245, 255),
                radius=20,
                border_width=2,
                border_color=COLOR_P1,
            )
            self._draw_rounded_rect(p2_panel, (250, 250, 250), radius=20)
        else:
            self._draw_rounded_rect(p1_panel, (250, 250, 250), radius=20)
            self._draw_rounded_rect(
                p2_panel,
                (255, 245, 245),
                radius=20,
                border_width=2,
                border_color=COLOR_P2,
            )

        # Labels
        self.draw_text(
            "Player X", self.font_bold, COLOR_P1_DARK, p1_panel.centerx, p1_panel.y - 30
        )
        self.draw_text(
            "Player O", self.font_bold, COLOR_P2_DARK, p2_panel.centerx, p2_panel.y - 30
        )

        # Helper to draw stack
        def draw_stacks(inv, start_x, start_y, is_active_player):
            sizes = [SIZE_LARGE, SIZE_MEDIUM, SIZE_SMALL]
            y_offset = 0
            for size in sizes:
                count = inv.pieces.get(size, 0)

                # Click Area
                area_rect = pygame.Rect(start_x - 50, start_y + y_offset - 50, 100, 100)

                # Selection Highlight
                if is_active_player and selected_size == size and count > 0:
                    pygame.draw.rect(
                        self.screen,
                        COLOR_WARNING,
                        area_rect,
                        3,
                        border_radius=15,
                    )

                # Draw placeholder if empty
                if count == 0:
                    pygame.draw.circle(
                        self.screen, (220, 220, 220), area_rect.center, 20
                    )
                else:
                    # Draw Piece
                    dummy_piece = Piece(inv.player_id, size)
                    self.draw_piece(
                        dummy_piece,
                        area_rect.centerx,
                        area_rect.centery,
                        is_inventory=True,
                    )

                    # Draw Badge Count
                    badge_pos = (area_rect.right - 20, area_rect.bottom - 20)
                    pygame.draw.circle(self.screen, TEXT_COLOR, badge_pos, 14)
                    self.draw_text(
                        str(count),
                        self.font_s,
                        (255, 255, 255),
                        badge_pos[0],
                        badge_pos[1],
                    )

                y_offset += 110

        draw_stacks(inv1, p1_panel.centerx, p1_panel.y + 70, current_turn == PLAYER_X)
        draw_stacks(inv2, p2_panel.centerx, p2_panel.y + 70, current_turn == PLAYER_O)

    def draw_game_over(self, winner: Optional[int], reason: str, mouse_pos):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # Modal Window
        modal_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 150, 500, 300
        )
        self._draw_rounded_rect(modal_rect, BG_COLOR, radius=20)
        pygame.draw.rect(self.screen, (255, 255, 255), modal_rect, 5, border_radius=20)

        if winner == PLAYER_X:
            title = "Player X ชนะ!"
            color = COLOR_P1_DARK
        elif winner == PLAYER_O:
            title = "Player O ชนะ!"
            color = COLOR_P2_DARK
        else:
            title = "เสมอ!"
            color = SUBTEXT_COLOR

        self.draw_text(
            title, self.font_title, color, modal_rect.centerx, modal_rect.y + 60
        )
        self.draw_text(
            reason, self.font_m, SUBTEXT_COLOR, modal_rect.centerx, modal_rect.y + 120
        )

        btn_menu = pygame.Rect(
            modal_rect.centerx - 100, modal_rect.bottom - 80, 200, 50
        )
        self.draw_button(btn_menu, "กลับสู่เมนู", SUBTEXT_COLOR, mouse_pos)

    def get_game_over_click(self, mouse_pos) -> Optional[int]:
        modal_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 150, 500, 300
        )
        btn_menu = pygame.Rect(
            modal_rect.centerx - 100, modal_rect.bottom - 80, 200, 50
        )
        if btn_menu.collidepoint(mouse_pos):
            return STATE_MENU
        return None

    # --- INPUT HANDLERS ---
    def get_board_click(self, mouse_pos) -> Optional[Tuple[int, int]]:
        x, y = mouse_pos
        if (
            BOARD_OFFSET_X <= x <= BOARD_OFFSET_X + BOARD_SIZE * CELL_SIZE
            and BOARD_OFFSET_Y <= y <= BOARD_OFFSET_Y + BOARD_SIZE * CELL_SIZE
        ):
            c = (x - BOARD_OFFSET_X) // CELL_SIZE
            r = (y - BOARD_OFFSET_Y) // CELL_SIZE
            return r, c
        return None

    def get_inventory_click(self, mouse_pos, player_id: int) -> Optional[int]:
        # Recalculate positions based on draw_inventory logic
        panel_width = 140
        if player_id == PLAYER_X:
            start_x = 10 + panel_width // 2
        else:
            start_x = SCREEN_WIDTH - 10 - panel_width // 2

        start_y = 100 + 70

        sizes = [SIZE_LARGE, SIZE_MEDIUM, SIZE_SMALL]
        y_offset = 0
        for size in sizes:
            area_rect = pygame.Rect(start_x - 50, start_y + y_offset - 50, 100, 100)
            if area_rect.collidepoint(mouse_pos):
                return size
            y_offset += 110
        return None

    # --- Lobby Functions (Simplified visual update) ---
    def draw_lobby_host(self, host_username, client_username, mouse_pos):
        self.screen.fill(BG_COLOR)
        self.draw_text(
            "ห้องรอเล่น (Host Lobby)", self.font_l, TEXT_COLOR, SCREEN_WIDTH // 2, 80
        )

        # Room Code / IP could go here

        # Player Slots
        slot_y = 180
        self._draw_rounded_rect(
            pygame.Rect(SCREEN_WIDTH // 2 - 300, slot_y, 600, 80),
            (255, 255, 255),
            radius=10,
        )
        self.draw_text(
            f"Host: {host_username}",
            self.font_m,
            COLOR_P1_DARK,
            SCREEN_WIDTH // 2,
            slot_y + 40,
        )

        slot_y += 100
        self._draw_rounded_rect(
            pygame.Rect(SCREEN_WIDTH // 2 - 300, slot_y, 600, 80),
            (255, 255, 255),
            radius=10,
        )
        if client_username:
            self.draw_text(
                f"ผู้ท้าชิง: {client_username}",
                self.font_m,
                COLOR_P2_DARK,
                SCREEN_WIDTH // 2,
                slot_y + 40,
            )

            # Action Buttons
            btn_start = pygame.Rect(SCREEN_WIDTH // 2 - 210, 400, 200, 60)
            btn_kick = pygame.Rect(SCREEN_WIDTH // 2 + 10, 400, 200, 60)
            self.draw_button(btn_start, "เริ่มเกม", COLOR_SUCCESS, mouse_pos)
            self.draw_button(btn_kick, "เตะออก", COLOR_DANGER, mouse_pos)
        else:
            self.draw_text(
                "กำลังรอผู้เข้าร่วม...",
                self.font_m,
                SUBTEXT_COLOR,
                SCREEN_WIDTH // 2,
                slot_y + 40,
            )

        btn_back = pygame.Rect(20, 20, 100, 40)
        self.draw_button(btn_back, "< Back", SUBTEXT_COLOR, mouse_pos)

    def get_lobby_host_click(self, mouse_pos, has_client):
        btn_back = pygame.Rect(20, 20, 100, 40)
        if btn_back.collidepoint(mouse_pos):
            return "back"

        if has_client:
            btn_start = pygame.Rect(SCREEN_WIDTH // 2 - 210, 400, 200, 60)
            btn_kick = pygame.Rect(SCREEN_WIDTH // 2 + 10, 400, 200, 60)
            if btn_start.collidepoint(mouse_pos):
                return "accept"
            if btn_kick.collidepoint(mouse_pos):
                return "reject"
        return None

    def draw_room_list(self, rooms: list, mouse_pos):
        self.screen.fill(BG_COLOR)
        self.draw_text(
            "รายชื่อห้อง (Room List)", self.font_l, TEXT_COLOR, SCREEN_WIDTH // 2, 80
        )

        start_y = 150
        for i, room in enumerate(rooms):
            if i >= 4:
                break

            rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, start_y, 500, 80)
            is_hover = rect.collidepoint(mouse_pos)

            # Draw Card
            color = (255, 255, 255) if not is_hover else (240, 248, 255)
            self._draw_shadow(rect, radius=10, offset_y=2)
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            if is_hover:
                pygame.draw.rect(self.screen, COLOR_P1, rect, 2, border_radius=10)

            # Info
            self.draw_text(
                f"{room['username']}'s Room",
                self.font_bold,
                TEXT_COLOR,
                rect.x + 30,
                rect.centery - 10,
                center=False,
            )
            self.draw_text(
                f"IP: {room['ip']}",
                self.font_s,
                SUBTEXT_COLOR,
                rect.x + 30,
                rect.centery + 15,
                center=False,
            )

            # Join Icon/Text
            self.draw_text(
                "Click to Join",
                self.font_s,
                COLOR_SUCCESS,
                rect.right - 100,
                rect.centery,
            )

            start_y += 100

        if not rooms:
            self.draw_text(
                "ไม่พบห้องที่เปิดอยู่...", self.font_m, SUBTEXT_COLOR, SCREEN_WIDTH // 2, 250
            )
            self.draw_text(
                "(โปรดตรวจสอบว่าอยู่ใน WiFi วงเดียวกัน)",
                self.font_s,
                SUBTEXT_COLOR,
                SCREEN_WIDTH // 2,
                290,
            )

        btn_back = pygame.Rect(SCREEN_WIDTH // 2 - 100, 520, 200, 50)
        self.draw_button(btn_back, "กลับเมนูหลัก", COLOR_DANGER, mouse_pos)

    def get_room_list_click(self, rooms: list, mouse_pos):
        btn_back = pygame.Rect(SCREEN_WIDTH // 2 - 100, 520, 200, 50)
        if btn_back.collidepoint(mouse_pos):
            return "back"

        start_y = 150
        for i, room in enumerate(rooms):
            if i >= 4:
                break
            rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, start_y, 500, 80)
            if rect.collidepoint(mouse_pos):
                return room
            start_y += 100
        return None

    def draw_lobby_client(self, host_username, status_text, mouse_pos):
        self.screen.fill(BG_COLOR)
        self._draw_rounded_rect(
            pygame.Rect(SCREEN_WIDTH // 2 - 250, 200, 500, 200),
            (255, 255, 255),
            radius=15,
        )

        self.draw_text("กำลังเชื่อมต่อ...", self.font_l, TEXT_COLOR, SCREEN_WIDTH // 2, 120)

        if host_username:
            self.draw_text(
                f"Connected to: {host_username}",
                self.font_m,
                COLOR_P1,
                SCREEN_WIDTH // 2,
                250,
            )

        self.draw_text(status_text, self.font_s, SUBTEXT_COLOR, SCREEN_WIDTH // 2, 300)

        btn_cancel = pygame.Rect(SCREEN_WIDTH // 2 - 100, 450, 200, 50)
        self.draw_button(btn_cancel, "ยกเลิก (Cancel)", COLOR_DANGER, mouse_pos)

    def get_lobby_client_click(self, mouse_pos):
        btn_cancel = pygame.Rect(SCREEN_WIDTH // 2 - 100, 450, 200, 50)
        if btn_cancel.collidepoint(mouse_pos):
            return "back"
        return None
