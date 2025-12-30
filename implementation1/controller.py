# pyright: strict
import pyxel
from .model import Model, Bots
from .view import View

class Bomberman:
    def __init__(self, model: Model, bots: Bots, view: View, settings: dict[str, int], fps: int=30):
        self.model = model
        self.view = view
        self.settings = settings
        self.soft_block_percent = self.settings["soft_block_percent"]
        self.powerup_percent = self.settings["powerup_percent"]
        self.timer_seconds = self.settings["timer_seconds"]
        self.human_player_number = self.settings["human_player_number"]
        self.total_player_number = self.settings["total_player_number"]
        self.bot_types = self.settings["bot_types"]
        self.rounds_to_win = self.settings["rounds_to_win"]  #phase 5a

        # phase 4
        self.bots = bots

        self.model.start_game_timer(self.timer_seconds)
        self.model.generate_walls()
        self.model.generate_hard_blocks()
        self.model.generate_walkable_coords()
        
        # self.model.generate_sprites(self.player_number)
        self.model.generate_sprites(self.total_player_number)
        
        # may type ignore kasi ang kulet ng pylance dinedetect sya as int
        self.bots.set_bots(self.total_player_number, self.human_player_number, self.bot_types) # type: ignore

        self.model.generate_soft_blocks(self.soft_block_percent)

        self.model.powerup_percent = self.powerup_percent

        self.model.setting_up(self.total_player_number, self.rounds_to_win) # phase 5a

    def update(self) -> None:
        # transition/countdown - phase 5d pero mali ata oops
        if self.model.round_transition_active:
            # ESC to skip transition
            if pyxel.btnp(pyxel.KEY_ESCAPE):
                if self.model.overall_game_over:
                    return
                self.model.round_transition_active = False
                self.model.round_end_frame = None
                self.model.round_winner = None
                if not self.model.overall_game_over:
                    self.model.reset_round(
                        self.soft_block_percent,
                        self.powerup_percent,
                        self.timer_seconds
                    )
                    self.model.start_countdown()
                    self.model.round_number += 1
            return
        
        if not self.model.countdown_finished:
            self.model.countdown()
            return
        
        elif not self.model.round_transition_active and pyxel.btnp(pyxel.KEY_ESCAPE):
            self.model.toggle_live_debug_mode()

        if self.model.overall_game_over:
            return
        
        # other way to link the keys so easier to add more players
        PLAYER_KEYS: dict[int, dict[str, int]] = {
            0: {
                "up": pyxel.KEY_UP,
                "down": pyxel.KEY_DOWN,
                "left": pyxel.KEY_LEFT,
                "right": pyxel.KEY_RIGHT,
                "bomb": pyxel.KEY_SPACE,
            },
            1: {
                "up": pyxel.KEY_W,
                "down": pyxel.KEY_S,
                "left": pyxel.KEY_A,
                "right": pyxel.KEY_D,
                "bomb": pyxel.KEY_X,  
            },
        }

        # loop over all active players
        for p in self.model.sprite_coords:
            if p in self.bots.bot_players:
                continue

            keys = PLAYER_KEYS[p]

            up = pyxel.btn(keys["up"])
            down = pyxel.btn(keys["down"])
            left = pyxel.btn(keys["left"])
            right = pyxel.btn(keys["right"])

            # para di magsnap if dalawang keys pressed
            diagonal = (up or down) and (left or right)
            self.model.set_diagonal(diagonal)

            if up:
                self.model.move_up(p)
            if down:
                self.model.move_down(p)
            if left:
                self.model.move_left(p)
            if right:
                self.model.move_right(p)

            # bomb
            if pyxel.btnp(keys["bomb"]):
                self.model.place_bomb(p)

        self.model.update_game_state()
        self.bots.update_bots()

        if self.model.game_over:
            self.model.handle_round_end(self.soft_block_percent, self.powerup_percent, self.timer_seconds)

        # self.bots._update_bots()


    def draw(self):
        # for  transition
        if self.model.round_transition_active:
            # draw the transition screen (no game objects)
            self.view.draw_transition(
                self.model.round_results_text, # winner
                self.model.round_number,  
                self.model.round_wins,          # scores
                # pachec
        )
            return  
        
        self.view.draw_background()
        self.view.walls(self.model.wall_coords)
        self.view.hard_blocks(self.model.hard_block_coords)
        self.view.soft_blocks(self.model.soft_block_coords)   

        self.view.bomb(self.model.all_bombs)
        self.view.explosions(self.model.explosions)
        
        if self.model.live_debug_mode:
            self.view.bot_type(self.model.sprite_coords, self.bots.bot_players)
            self.view.bot_state(self.model.sprite_coords, self.bots.bot_states)
            self.view.bot_danger(self.model.sprite_coords, self.bots.bot_danger_rads)
            self.view.bot_paths(self.bots.bot_paths, self.model.block_l)

        self.view.powerups(self.model.powerups)               
        self.view.sprites(self.model.sprite_coords)

        if not self.model.countdown_finished:
            self.view.draw_timer(self.timer_seconds)
            self.view.draw_countdown(self.model.countdown_time)
            return
        
        self.view.draw_sprite_scores(self.model.round_wins)

        if not self.model.game_over and self.model.countdown_finished:
            self.view.draw_timer(self.model.remaining_time())
            
        if self.model.game_over:
            self.view.draw_game_over(self.model.game_over_text)
