# pyright: strict
import pyxel

class View:
    def __init__(self, head_x: int, head_y: int, block_l: int):
        self.head_x = head_x
        self.head_y = head_y
        self.block_l = block_l
        self.game_x = 15 * block_l
        self.game_y = 13 * block_l
        self.y_origin = head_y
        self.y_end = self.y_origin + self.game_y

    def draw_background(self):
        self.bg()
        self.header()
        self.floor()

    def bg(self):
        pyxel.cls(0)

    def header(self):
        pyxel.rect(0, 0, self.head_x, self.head_y, 12)
        for i in range(0, self.head_x):
            for j in range(0, self.head_y):
                if i == 1 or j == 1 or i == self.head_x - 2 or j == self.head_y - 2:
                    pyxel.pset(i, j, 3)
                if i == 0 or j == 0 or i == self.head_x - 1 or j == self.head_y - 1:
                    pyxel.pset(i, j, 7)
    
    def floor(self):
        pyxel.rect(0, self.y_origin, self.game_x, self.game_y, 3)

    def walls(self, wall_coords: set[tuple[int, int]]):
        for x, y in wall_coords:
            pyxel.blt(x, y, 0, 0, 0, self.block_l, self.block_l)

    def hard_blocks(self, hard_block_coords: set[tuple[int, int]]):
        for x, y in hard_block_coords:
            pyxel.blt(x, y, 0, 0, 0, self.block_l, self.block_l)

    def soft_blocks(self, soft_block_coords: set[tuple[int, int]]):
        for x, y in soft_block_coords:
            pyxel.blt(x, y, 0, 16, 0, self.block_l, self.block_l)

    def sprites(self, sprite_coords: dict[int, list[int]]):
        for i in sprite_coords:  
            x, y = sprite_coords[i]
            pyxel.blt(x, y, 1, i * 16, 0, self.block_l, self.block_l, 3) #modify coordinates dito if hindi 10x10 sprite

    # functions for bombs
    def bomb(self, bombs: set[tuple[int, int]]) -> None:
        for x, y in bombs:
            pyxel.blt(x, y, 0, 32, 0, self.block_l, self.block_l, 3)

    def explosions(self, explosions: set[tuple[int, int]]) -> None:
        for x, y in explosions:
            pyxel.blt(x, y, 0, 48, 0, self.block_l, self.block_l, 3)

    # timer, change/ayusin pa
    def draw_timer(self, remaining_seconds: int) -> None:
        mm: int = remaining_seconds // 60
        ss: int = remaining_seconds % 60
        pyxel.text(5, self.head_y // 2 - 2, f"{mm:02}:{ss:02}", 7)

    # placeholder, not centered, basta makita lang na game over
    def draw_game_over(self, text: str) -> None:
        self.game_over_text = Game_Over_Text()
        if text != "draw":
            pyxel.text(self.game_x // 2 - 27, self.head_y // 2 - 2, self.game_over_text.winner(text), 7)
        else:
            pyxel.text(self.game_x // 2 - 23, self.head_y // 2 - 2, self.game_over_text.its_a_draw(), 7)

    def draw_transition(self, round_results: str, round_number: int, round_wins: dict[int, int]):
        pyxel.cls(3)
        self.header()
        pyxel.text(self.game_x // 2 - 33, self.head_y // 2 - 2, f"Round {round_number} completed", 7)
        pyxel.text(5, self.head_y + 7, round_results, 7)
        pyxel.text(5, self.head_y + 20, "Current points:", 15)
        for p, wins in round_wins.items():
            pyxel.text(10, self.head_y + 30 + p * 10, f"Player {p + 1}: {wins} win{"" if wins == 1 else "s"}", 15)

    def draw_countdown(self, time: int):
        if time <= 30:
            pyxel.text(self.game_x // 2 - 5, self.head_y // 2 - 2, "GO!", 7)
        elif time <= 60:
            pyxel.text(self.game_x // 2 - 14, self.head_y // 2 - 2, "GET SET", 10)
        else:
            pyxel.text(self.game_x // 2 - 12, self.head_y // 2 - 2, "READY", 8)

    def draw_sprite_scores(self, round_wins: dict[int, int]):
        for p, wins in round_wins.items():
            pyxel.rect(53 + p * 25, self.head_y // 2 - 3, 7, 7, 5)
            pyxel.blt(40 + p * 25, self.head_y // 2 - 4, 1, p * 16, 0, self.block_l, self.block_l, 3)
            pyxel.text(55 + p * 25, self.head_y // 2 - 2, str(wins), 7)
    
    def powerups(self, powerups: dict[tuple[int, int], str]) -> None:
        SPRITES = {
            # kind: (img, u, v, w, h)
            "fire":  (2, 0, 0,  10, 10),  
            "speed":  (2, 16, 0, 10, 10),   
            "bomb": (2, 32, 0, 10, 10),   
        }

        for (x, y), kind in powerups.items():
            img, u, v, w, h = SPRITES[kind]

            # pangcenter pero aadjust pa sprite anlaki pala niya
            draw_x = x + (self.block_l - w) // 2
            draw_y = y + (self.block_l - h) // 2

            pyxel.blt(draw_x, draw_y, img, u, v, w, h, 3)        
    
    def bot_paths(self, paths: dict[int, list[tuple[int, int]]], block_l: int):
        for p, path in paths.items():
            for x, y in path:
                if p == 1:
                    pyxel.pset(x, y, 11)
                if p == 2:
                    pyxel.pset(x, y + (block_l - 1), 8)
                if p == 3:
                    pyxel.pset(x + (block_l - 1), y + (block_l - 1), 2)

    def bot_type(self, player_locs: dict[int, list[int]], bot_types: dict[int, str]):
        for p, (x, y) in player_locs.items():
            if p in bot_types:
                typ = bot_types[p]
                pyxel.text(x - 8, y - 8, typ, 7)

    def bot_state(self, player_locs: dict[int, list[int]], bot_states: dict[int, str]):
        for p, (x, y) in player_locs.items():
            if p in bot_states:
                state = bot_states[p]
                pyxel.text(x - 8, y + 12, state, 15)
    
    def bot_danger(self, bot_locs: dict[int, list[int]], bot_rads: dict[int, int]):
        for p, (x, y) in bot_locs.items():
            if p in bot_rads:
                k = bot_rads[p]
                if k <= 0:
                    continue

                r = k * self.block_l
                cx = x + self.block_l // 2
                cy = y + self.block_l // 2

                pyxel.circb(cx, cy, r, 1)

class Game_Over_Text:
    @staticmethod
    def its_a_draw() -> str:
        return "It's a draw!"

    @staticmethod
    def winner(p: str) -> str:
        return f"Player {p} wins!"



