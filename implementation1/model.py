# pyright: strict
import pyxel, random
from typing import Callable

class Model:
    def __init__(self, head_y: int, block_l: int, fps: int = 30):
        self.block_l: int = block_l
        self.game_x: int = 15 * block_l
        self.game_y: int = 13 * block_l
        self.y_origin: int = head_y
        self.y_end: int = self.y_origin + self.game_y
        self.wall_coords: set[tuple[int, int]] = set()
        self.hard_block_coords: set[tuple[int, int]] = set()
        self.soft_block_coords: set[tuple[int, int]] = set()
        self._live_debug_mode: bool = False

        # sprites
        self.sprite_coords: dict[int, list[int]] = dict()
        self.spawn_points = [
            (self.block_l, self.y_origin + self.block_l), # p = 0
            (self.game_x - self.block_l * 2, self.y_origin + self.block_l), # p = 1
            (self.block_l, self.y_end - self.block_l * 2), # p = 2
            (self.game_x - self.block_l * 2, self.y_end - self.block_l * 2),] # p = 3
        
        self._walkable_coords: set[tuple[int, int]] = set()

        # player movement related
        self._both_keys_pressed: bool = False

        # bomb        
        self.num_bombs_per_p: dict[int, int] = dict()
        self.bomb_owner: dict[tuple[int, int], int] = {}
        self._all_bombs: set[tuple[int, int]] = set()
        self.bomb_timer_per_b: dict[tuple[int, int], int] = dict()
        self.explosions: set[tuple[int, int]] = set()       
        self.explosion_timer: int = 0
        self.explosion_range: set[tuple[int, int]] = set()

        # for player powerups
        self.exp_range_per_p: dict[int, int] = {0: 1, 1: 1, 2: 1, 3: 1}
        self.max_bombs_per_p: dict[int, int] = {0: 1, 1: 1, 2: 1, 3: 1}
        self.move_spd_per_p: dict[int, int] = {0: 1, 1: 1, 2: 1, 3: 1}

        # powerups
        self.powerups: dict[tuple[int, int], str] = {}
        self.new_power_up_coords: set[tuple[int, int]] = set()
        self.powerup_percent: int = 0
        self._powerup_effects: dict[str, Callable[[int], None]] = {
            "fire": self._powerup_fire,
            "bomb": self._powerup_bomb,
            "speed": self._powerup_speed,
            }
        
        # for game over tracking
        self.start_frame: int = pyxel.frame_count  
        self.timer_seconds: int
        self.game_over: bool = False 
        self.game_over_time: int = 30
        self.game_over_text: str = ""       

        # phase 5a
        self.round_number = 1 # current round
        self.round_end_frame: int | None = None #end frame ng round
        self.overall_game_over = False 
        self.rounds_to_win: int = 0 #score needed to win
        self.round_wins: dict[int, int] = {} # store scores

        # phase 5d
        self.ROUND_DELAY = 90  # delay by 3 seconds since 30 fps
        self.round_start_frame: int | None = None  # when the round starts
        self.round_transition_active: bool = False  # transition screen active or not
        self.round_winner: int | None = None #winner ng round
        self.round_results_text: str = "" #pangdisplay dapat ng winner, for transition
        self.countdown_time: int = 0
        self.countdown_finished: bool = True

# PHASE 5 (di pa naka arrange)

    def setting_up(self, total_players: int, rounds_to_win: int):
        self.rounds_to_win = rounds_to_win
        self.round_wins = {p: 0 for p in range(total_players)}
        self.round_number = 1
        self.overall_game_over = False
        self.round_end_frame = None

    def start_countdown(self):
        self.countdown_time = self.ROUND_DELAY
        self.countdown_finished = False

    def countdown(self):
        self.countdown_time -= 1
        if self.countdown_time == 0:
            self.countdown_finished = True
            self.start_frame = pyxel.frame_count
        return

    def reset_round(self, soft_block_percent: int, powerup_percent: int, timer_seconds: int):
        # clear
        self.sprite_coords.clear()
        self.soft_block_coords.clear()
        self.powerups.clear()
        self.new_power_up_coords.clear()
        self._all_bombs.clear()
        self.bomb_timer_per_b.clear()
        self.bomb_owner.clear()
        self.explosions.clear()
        self.explosion_range.clear()

        # reset player stats
        for p in range(len(self.round_wins)):
            self.num_bombs_per_p[p] = 0
            self.exp_range_per_p[p] = 1
            self.max_bombs_per_p[p] = 1
            self.move_spd_per_p[p] = 1

        # regenerate map & sprites
        self.generate_sprites(len(self.round_wins))
        self.generate_soft_blocks(soft_block_percent)
        self.powerup_percent = powerup_percent

        # timers, recheck
        self.start_game_timer(timer_seconds)
        self.game_over = False
        self.game_over_text = ""
        self.game_over_time = 30

    def handle_round_end(self, soft_block_percent: int, powerup_percent: int, timer_seconds: int):
        # when is round over
        if self.round_end_frame is None:
            # start round end
            self.round_end_frame = pyxel.frame_count

            if self.game_over_text != "draw":
                self.round_winner = int(self.game_over_text) - 1
                self.round_wins[self.round_winner] += 1
                self.round_results_text = f"player {self.round_winner + 1} win"
            else:
                self.round_winner = None
                self.round_results_text = "tie"

            self.round_transition_active = True
            self.print_round_results() #printing in console
            for p, wins in self.round_wins.items():
                if wins == self.rounds_to_win:
                    self.overall_game_over = True
                    self.round_results_text = f"Game over! Player {p + 1} wins!"
                    
        elif pyxel.frame_count - self.round_end_frame >= self.ROUND_DELAY:
            # check if match over
            if self.round_winner is not None and self.round_wins[self.round_winner] >= self.rounds_to_win:
                self.overall_game_over = True
            else:
                # reset for next round
                self.round_number += 1
                self.round_end_frame = None
                self.round_transition_active = False
                self.round_winner = None
                if not self.overall_game_over:
                    self.reset_round(soft_block_percent, powerup_percent, timer_seconds)
                    self.round_start_frame = pyxel.frame_count


    # function lang na pangprint, can be removed, for checking
    def print_round_results(self):
        print(f"--- Round {self.round_number - 1} completed ---")
        print("Current points:")
        for p, wins in self.round_wins.items():
            print(f"Player {p + 1}: {wins} win(s)")


    """generation functions"""

    def generate_walls(self):
        for i in range(0, self.game_x, self.block_l):
            for j in range(self.y_origin, self.y_end, self.block_l):
                if (i == 0 or j == self.y_origin or i == self.game_x - self.block_l 
                or j == self.y_end - self.block_l):
                    self.wall_coords.add((i, j))

    def generate_hard_blocks(self):
        for i in range(self.block_l * 2, self.game_x - self.block_l, self.block_l * 2):
            for j in range(self.y_origin + self.block_l * 2, self.y_end - self.block_l, self.block_l * 2):
                self.hard_block_coords.add((i, j))

    def generate_sprites(self, player_number: int):
        self.player_number: int = player_number


        for p in range(player_number):
            self.sprite_coords[p] = list(self.spawn_points[p])
            self.num_bombs_per_p[p] = 0

    def generate_soft_blocks(self, spawn_percent: int): # should generate everywhere sa board except player spawn points, tabi ng spawn points, and hard blocks
        for i in range(self.block_l, self.game_x - self.block_l, self.block_l):
            for j in range(self.y_origin + self.block_l, self.y_end - self.block_l, self.block_l):
                if not ((i, j) in self.hard_block_coords
                or [i, j] in self.sprite_coords.values()
                or [i + self.block_l, j] in self.sprite_coords.values()
                or [i, j + self.block_l] in self.sprite_coords.values()
                or [i - self.block_l, j] in self.sprite_coords.values()
                or [i, j - self.block_l] in self.sprite_coords.values()):
                    
                    if random.randint(0, 99) < spawn_percent:
                        self.soft_block_coords.add((i, j))

    def generate_walkable_coords(self):
        for i in range(self.block_l, self.game_x - self.block_l, self.block_l):
            for j in range(self.y_origin + self.block_l, self.y_end - self.block_l, self.block_l):
                if not (i, j) in self.hard_block_coords:
                    self._walkable_coords.add((i, j)) # para may set lang ng lahat ng coords na pede lakaran


    """snap funtions"""

    def snap_x(self, x: int) -> int:
        return round(x / self.block_l) * self.block_l

    def snap_y(self, y: int) -> int:
        return round((y - self.y_origin) / self.block_l) * self.block_l + self.y_origin

    def snap_player_x(self, p: int):
        x = self.sprite_coords[p][0]
        px = self.snap_x(x)
        not_on_hard_block: bool = px in range(self.block_l, self.game_x - self.block_l, self.block_l * 2)
        if px != x and not_on_hard_block and not self._both_keys_pressed:
            self.sprite_coords[p][0] = px

    def snap_player_y(self, p: int):
        y = self.sprite_coords[p][1]
        py = self.snap_y(y)
        not_on_hard_block: bool = py in range(self.y_origin + self.block_l, self.y_end - self.block_l, self.block_l * 2)
        if py != y and not_on_hard_block and not self._both_keys_pressed:
            self.sprite_coords[p][1] = py

    def set_diagonal(self, value: bool) -> None:
        self._both_keys_pressed = value

    """player movement functions"""

    def move_up(self, p: int):
        y = self.sprite_coords[p][1]
        if y - self.block_l > self.y_origin:
            self.snap_player_x(p)
        for _ in range(self.move_spd_per_p[p]):
            if not self.will_not_collide(p, "up"):
                break
            self.sprite_coords[p][1] -= 1

    def move_down(self, p: int):
        y = self.sprite_coords[p][1]
        if y + self.block_l < self.y_end - self.block_l:
            self.snap_player_x(p)
        for _ in range(self.move_spd_per_p[p]):
            if not self.will_not_collide(p, "down"):
                break
            self.sprite_coords[p][1] += 1
        
    def move_left(self, p: int):
        x = self.sprite_coords[p][0]
        if x - self.block_l > 0:
            self.snap_player_y(p)
        for _ in range(self.move_spd_per_p[p]):
            if not self.will_not_collide(p, "left"):
                break
            self.sprite_coords[p][0] -= 1

    def move_right(self, p: int):
        x = self.sprite_coords[p][0]
        if x + self.block_l < self.game_x - self.block_l:
            self.snap_player_y(p)
        for _ in range(self.move_spd_per_p[p]):
            if not self.will_not_collide(p, "right"):
                break
            self.sprite_coords[p][0] += 1

    """player collision function"""

    def will_not_collide(self, p: int, direction: str):
        x, y = self.sprite_coords[p]

        if direction == "up":
            target = (x, y - self.block_l)
            return (
                y - self.block_l > self.y_origin # di tatama sa wall
                and x in range(self.block_l, self.game_x - self.block_l, self.block_l * 2) # di tatama sa hard blocks
                and target not in self.soft_block_coords # di tatama sa soft blocks
                and target not in self.bomb_timer_per_b.keys())  # bomb check

        if direction == "down":
            target = (x, y + self.block_l)
            return (
                y + self.block_l < self.y_end - self.block_l
                and x in range(self.block_l, self.game_x - self.block_l, self.block_l * 2)
                and target not in self.soft_block_coords
                and target not in self.bomb_timer_per_b.keys())

        if direction == "left":
            target = (x - self.block_l, y)
            return (
                x - self.block_l > 0
                and y in range(self.y_origin + self.block_l, self.y_end - self.block_l, self.block_l * 2)
                and target not in self.soft_block_coords
                and target not in self.bomb_timer_per_b.keys())

        if direction == "right":
            target = (x + self.block_l, y)
            return (
                x + self.block_l < self.game_x - self.block_l
                and y in range(self.y_origin + self.block_l, self.y_end - self.block_l, self.block_l * 2)
                and target not in self.soft_block_coords
                and target not in self.bomb_timer_per_b.keys())

    """bomb functions"""

    def place_bomb(self, p: int):        
        if self.num_bombs_per_p[p] == self.max_bombs_per_p[p]:
            return

        x, y = self.sprite_coords[p]
        px = self.snap_x(x)
        py = self.snap_y(y)

        if (px, py) in self._all_bombs:
            return

        # place bomb
        self._all_bombs.add((px, py))
        self.bomb_timer_per_b[(px, py)] = 90
        self.bomb_owner[(px, py)] = p
        self.num_bombs_per_p[p] += 1
        self.get_future_explosion_range((px, py))

    def update_bomb(self) -> None:
        exploded: list[tuple[int, int]] = []

        for coord, timer in self.bomb_timer_per_b.items():
            if timer <= 0:
                exploded.append(coord)

        for coord in exploded:
            self.explode(coord)

    """explosion functions"""

    def get_future_explosion_range(self, coords: tuple[int, int]) -> None:
        if coords not in self.bomb_owner:
            return 

        x, y = coords
        p = self.bomb_owner[coords]

        # center always explodes
        self.explosion_range.add((x, y))

        directions = [
            ( self.block_l, 0),
            (-self.block_l, 0),
            (0,  self.block_l),
            (0, -self.block_l),
        ]

        for dx, dy in directions:
            for i in range(1, self.exp_range_per_p[p] + 1):
                pos = (x + dx * i, y + dy * i)

                # stop at wall or hard block
                if pos in self.wall_coords or pos in self.hard_block_coords:
                    break

                self.explosion_range.add(pos)

                # stop after soft block
                if pos in self.soft_block_coords:
                    break
            
    def explode(self, coords: tuple[int, int]) -> None:
        if coords not in self._all_bombs:
            return

        x, y = coords

        # hiniwalay for ocp
        p = self.remove_bomb(coords)

        self.explosion_range.discard(coords) # wala na sa range dahil nag explode na
        self.explosions.add((x, y))  # center always explodes

        # directions: right, left, down, up
        directions = [
            ( self.block_l, 0),
            (-self.block_l, 0),
            (0,  self.block_l),
            (0, -self.block_l),
        ]

        for dx, dy in directions:
            for i in range(1, self.exp_range_per_p[p] + 1):
                pos = (x + dx * i, y + dy * i)

                # stop at hard block or wall
                if self.hit_hard_or_wall(pos):
                    break

                # explode this tile
                self.explosion_range.discard(pos)
                self.explosions.add(pos)

                # stop after soft block
                if self.hit_soft_block(pos):
                    break

        self.explosion_timer = pyxel.frame_count

    def remove_bomb(self, coords: tuple[int, int]) -> int:
        del self.bomb_timer_per_b[coords]
        p = self.bomb_owner.pop(coords)
        self.num_bombs_per_p[p] -= 1
        self._all_bombs.discard(coords)
        return p
    
    def hit_hard_or_wall(self, coords: tuple[int, int]) -> bool:
        return coords in self.hard_block_coords or coords in self.wall_coords
    
    def hit_soft_block(self, coords: tuple[int, int]) -> bool:
        if coords in self.soft_block_coords:
            self.new_power_up_coords.add(coords)
            self.soft_block_coords.remove(coords)
            return True
        else:
            return False

    def players_caught_in_explosion(self) -> None:
        dead_players: list[int] = []
        for p, (x, y) in self.sprite_coords.items():

            # nagdagdag ng snap para kahit touching lang sa explosion mamamatay pa rin
            px = self.snap_x(x)
            py = self.snap_y(y)
            
            if (px, py) in self.explosions:
                dead_players.append(p)

        for p in dead_players:
            # print(f"Player {p + 1} ded!")
            del self.sprite_coords[p]  # or mark as dead

    def update_explosions(self) -> None:
        if not self.explosions:
            return

        # hiniwalay ko lang function pero same lang
        self.players_caught_in_explosion()

        # if another bomb in explosion
        for coord in list(self._all_bombs):
            if coord in self.explosions:
                self.explode(coord)

        # may condition pa dapat dito para aalisin powerup if kasama sa explosion
        for coord in list(self.powerups):
            if coord in self.explosions:
                self.powerups.pop(coord)

        # remove explosions after 1 second 
        if pyxel.frame_count - self.explosion_timer >= 30:
            self.explosions.clear()

            # spawn lang ng powerups if nagclear na explosions
            self.spawn_powerups()

    """powerup functions"""
    
    def spawn_powerups(self) -> None:
        for pos in self.new_power_up_coords:
            if random.randint(0, 99) < self.powerup_percent:
                # snap
                gx = self.snap_x(pos[0])
                gy = self.snap_y(pos[1])
                kind = random.choice(list(self._powerup_effects.keys()))
                self.powerups[(gx, gy)] = kind
                # print("powerup coords:", (gx, gy), "powerup:", kind)
        self.new_power_up_coords = set() # nagspawn na lahat so clear the set
    
    def _powerup_fire(self, p: int) -> None:
        self.exp_range_per_p[p] += 1

    def _powerup_bomb(self, p: int) -> None:
        self.max_bombs_per_p[p] += 1

    def _powerup_speed(self, p: int) -> None:
        self.move_spd_per_p[p] += 1

    def pickup_powerups(self) -> None:
        for p, (x, y) in list(self.sprite_coords.items()):
            gx = self.snap_x(x)
            gy = self.snap_y(y)

            pos = (gx, gy)
            if pos not in self.powerups:
                continue

            kind = self.powerups.pop(pos)
            effect = self._powerup_effects[kind]
            effect(p)

    """timer functions"""

    def bomb_timer(self) -> None:
        for coord in list(self.bomb_timer_per_b):
            self.bomb_timer_per_b[coord] -= 1

    def start_game_timer(self, time: int) -> None:
        self.timer_seconds = time

    def remaining_time(self) -> int:
        elapsed_seconds: int = int((int(pyxel.frame_count) - self.start_frame) // 30)
        return max(self.timer_seconds - elapsed_seconds, 0)
    
    def start_game_over_timer(self) -> None:
        self.game_over_time -= 1

    """game state functions"""

    def check_game_over(self) -> None:
        if self.remaining_time() <= 0 or len(self.sprite_coords) == 0:
            self.game_over = True
            if len(self.sprite_coords) == 1 and self.player_number > 1:
                p: int = next(iter(self.sprite_coords)) + 1
                self.game_over_text = str(p)
            else:
                self.game_over_text = "draw"
        elif len(self.sprite_coords) == 1 and self.player_number > 1 and self.game_over_time != 0:
            self.start_game_over_timer()
        elif self.game_over_time == 0:
            self.game_over = True
            p: int = next(iter(self.sprite_coords)) + 1
            self.game_over_text = str(p)

    def update_game_state(self) -> None:
        self.update_explosions()
        self.update_bomb()
        self.bomb_timer()
        self.pickup_powerups()
        self.check_game_over()

    def toggle_live_debug_mode(self) -> None:
         self._live_debug_mode = True if self._live_debug_mode == False else False

    @property
    def live_debug_mode(self) -> bool:
        return self._live_debug_mode

    @property
    def walkable_coords(self) -> set[tuple[int, int]]:
        return self._walkable_coords
    
    @property
    def all_bombs(self) -> set[tuple[int, int]]:
        return self._all_bombs
        
""""PHASE 3"""

class Bots:

    BOT_TYPE_INTS: dict[str, tuple[float, int]] = {
        "hostile": (0.5, 25),
        "careful": (0.25, 100),
        "greedy": (1.0, 100),
        }
    
    BOT_TYPE_DANGER: dict[str, int] = {
        "hostile": 0,
        "careful": 4,
        "greedy": 2
        }
    
    def __init__(self, model: Model):
        self.model = model
        self.bot_players: dict[int, str] = {}
        self.bot_bomb_percent: int
        self.bot_move_percent: int
        self.bot_direction: dict[int, str] = {}
        self.bot_paths: dict[int, list[tuple[int, int]]] = {}
        self.bot_goal: dict[int, tuple[int, int]] = {}
        self.escaping_bots: dict[int, int] = {}
        self.prev_explosions: set[tuple[int, int]] = set()
        self.prev_bombs: set[tuple[int, int]] = set()
        self.bot_int_vals: dict[int, tuple[float, int]] = {}
        self.bot_states: dict[int, str] = {}
        self.bot_danger_rads: dict[int, int] = {}

    def set_bots(self, total_players: int, human_players: int, bot_types: list[str]) -> None:
        i = 0
        for p in range(human_players, total_players):
            self.bot_players[p] = bot_types[i]
            self.escaping_bots[p] = 0
            i += 1
        self.set_bot_type_int()

    def set_bot_type_int(self) -> None:
        for p, bot_type in self.bot_players.items():
            self.bot_int_vals[p] = self.BOT_TYPE_INTS[bot_type]
            self.bot_danger_rads[p] = self.BOT_TYPE_DANGER[bot_type]

    def make_bot_path(self, p: int, end: tuple[int, int]) -> list[tuple[int, int]]:
        dist: dict[tuple[int, int], int] = {}
        prev: dict[tuple[int, int], tuple[int, int] | None] = {}
        _sprite_coord = self.model.sprite_coords[p]
        x, y = self.model.snap_x(_sprite_coord[0]), self.model.snap_y(_sprite_coord[1])
        start = (x, y)

        coords = self.model.walkable_coords.copy()
        coords.difference_update(self.model.explosions)

        bomb_locs = self.model.all_bombs
        if start not in bomb_locs:
            coords.difference_update(bomb_locs)

        if self.escaping_bots[p] == 1:
            coords.difference_update(self.model.soft_block_coords)

        if start not in coords or end not in coords:
            return []

        for node in coords:
            dist[node] = 10**9
            prev[node] = None

        dist[start] = 0
        unvisited = coords

        step = self.model.block_l

        while unvisited:
            current = min(unvisited, key=lambda n: dist[n])
            unvisited.remove(current)

            if current == end:
                break

            cx, cy = current

            neighbors = [
                (cx + step, cy),
                (cx - step, cy),
                (cx, cy + step),
                (cx, cy - step),
            ]

            for nx, ny in neighbors:
                if (nx, ny) not in unvisited:
                    continue

                alt = dist[current] + 1
                if alt < dist[(nx, ny)]:
                    dist[(nx, ny)] = alt
                    prev[(nx, ny)] = current

        # reconstruct path
        path: list[tuple[int, int]] = []
        node = end
        while node is not None:
            path.append(node)
            node = prev[node]

        path.reverse()

        if path and path[0] == start:
            return path
        return []
    
    def move_bot_to(self, p: int, coord: tuple[int, int]) -> None:
        x, y = self.model.sprite_coords[p]
        nx, ny = coord

        speed = self.model.move_spd_per_p[p]

        # snap
        if abs(x - nx) <= speed and abs(y - ny) <= speed:
            self.model.sprite_coords[p] = [nx, ny]
            if self.bot_paths[p]:
                self.bot_paths[p].pop(0)
            return

        # move only if di tatama sa hard blocks or walls
        dx = nx - x
        dy = ny - y

        if abs(dx) > abs(dy):
            if dx < 0:
                self.model.move_left(p)
            elif dx > 0:
                self.model.move_right(p)
        else:
            if dy < 0:
                self.model.move_up(p)
            elif dy > 0:
                self.model.move_down(p)

    def wander(self, p: int):
        possible_goals = (
            self.model.walkable_coords.copy()
            - self.model.soft_block_coords
            - self.model.explosion_range
            - self.model.explosions
        )

        list_possible_goals = list(possible_goals)
        random.shuffle(list_possible_goals)

        for goal in list_possible_goals:
            new_bot_path = self.make_bot_path(p, goal)
            if not new_bot_path:
                continue
            else:
                self.bot_goal[p] = goal
                self.bot_paths[p] = new_bot_path
                self.bot_states[p] = "wander"
                return           

    def escape(self, p: int):
        self.escaping_bots[p] = 1
        # coord = self.model.sprite_coords[p]
        # x, y = self.model.snap_x(coord[0]), self.model.snap_y(coord[1])
        goals: list[tuple[int, int]] = []

        possible_goals = (
            self.model.walkable_coords.copy()
            - self.model.soft_block_coords
            - self.model.explosion_range
            - self.model.explosions
        )

        if not possible_goals:
            self.wander(p)
            return

        for pos in possible_goals:
        #     if (x - self.model.block_l * 8 <= pos[0] <= x + self.model.block_l * 8 
        #     and y - self.model.block_l * 8 <= pos[1] <= y + self.model.block_l * 8):
        #         goals.append(pos)
            goals.append(pos)

        random.shuffle(goals)

        for goal in goals:
            new_bot_path = self.make_bot_path(p, goal)
            if new_bot_path:
                print(f"{p} escape! {goal}")
                self.bot_goal[p] = goal
                self.bot_paths[p] = new_bot_path
                self.bot_states[p] = "escape"
                return

        self.wander(p)

    def get_powerup(self, p: int) -> None:
        # no powerup, wander state
        if p not in self.bot_paths or not self.bot_paths[p]:
            self.wander(p)
            return

        coord = self.model.sprite_coords[p]
        gx, gy = self.bot_goal[p]
        self.bot_states[p] = "get_powerup"

        # if bot has reached goal, magwawander na ulit
        if (self.model.snap_x(coord[0]), self.model.snap_y(coord[1])) == (gx, gy):
            self.wander(p)


    def attack(self, p: int) -> None:
        bot_type = self.bot_players[p]

        # goal and path MUST already be set by must_attack()
        if p not in self.bot_paths or not self.bot_paths[p]:
            self.wander(p)
            return

        coord = self.model.sprite_coords[p]
        x, y = self.model.snap_x(coord[0]), self.model.snap_y(coord[1])

        # bomb placement range R per bot type
        R = 2 if bot_type == "hostile" else 4 if bot_type == "careful" else 3

        for q, (qx, qy) in self.model.sprite_coords.items():
            if q == p:
                continue

            dist = abs(x - self.model.snap_x(qx)) + abs(y - self.model.snap_y(qy))
            if dist <= R * self.model.block_l:
                self.model.place_bomb(p)
                if (x, y) in self.model.all_bombs:
                    print(f"{p} attack: bomb placed")
                    self.escape(p)
                return

    def in_danger(self, coord: tuple[int, int], p: int | None = None):
        px, py = self.model.snap_x(coord[0]), self.model.snap_y(coord[1])

        if p is not None:
            bot_type = self.bot_players[p]

            if bot_type == "hostile":
                return (px, py) in self.model.all_bombs and (px, py) not in self.model.explosions
            
            # if not hostile
            coord_lis: list[tuple[int, int]] = []
            for i in range(px - self.model.block_l * self.BOT_TYPE_DANGER[bot_type], px + self.model.block_l * self.BOT_TYPE_DANGER[bot_type] + 1, self.model.block_l):
                for j in range(py - self.model.block_l * self.BOT_TYPE_DANGER[bot_type], py + self.model.block_l * self.BOT_TYPE_DANGER[bot_type] + 1, self.model.block_l):
                    if (i, j) in self.model.walkable_coords:
                        coord_lis.append((i, j))
            
            for coord in coord_lis:
                if coord in self.model.explosion_range or (px, py) in self.model.explosions:
                    print(f"{p} danger worked")
                    return True
                return False

        return (px, py) in self.model.explosion_range or (px, py) in self.model.explosions
    
    def danger_score(self, pos: tuple[int, int]) -> int:
        score = 0
        for bx, by in self.model.all_bombs:
            score += abs(pos[0] - bx) + abs(pos[1] - by)
        return score
    
    def bot_bomb_place(self, p: int, next_coord: tuple[int, int]):
        x, y = self.model.sprite_coords[p]
        if next_coord in self.model.soft_block_coords and (
            x - self.model.block_l <= next_coord[0] <= x + self.model.block_l
            or y - self.model.block_l <= next_coord[1] <= y + self.model.block_l):
                self.model.place_bomb(p)
                if (x, y) in self.model.all_bombs:
                    self.escape(p)
    
    def check_explosion_next_block(self, p: int, next_coord: tuple[int, int]):
        if (next_coord in self.model.explosions 
            or next_coord in self.model.all_bombs):
            if self.escaping_bots[p] == 1:
                self.escape(p)
            elif self.bot_states[p] == "get_powerup":
                self.get_powerup(p)
            elif self.bot_states[p] == "attack":
                self.attack(p)
            else:
                self.wander(p)
        return

    def must_obtain_powerup(self, p: int):
        if not self.model.powerups:
            return False

        bot_type = self.bot_players[p]
        coord = self.model.sprite_coords[p]
        start = (self.model.snap_x(coord[0]), self.model.snap_y(coord[1]))

        powerup_cells = list(self.model.powerups.keys())

        # hostile bots only 20% chance, fails 80%
        if bot_type == "hostile" and random.randint(0, 99) >= 20:
            return False

        # policy 1: closest powerup (greedy)
        if bot_type == "greedy":
            powerup_cells.sort(
                key=lambda c: abs(c[0] - start[0]) + abs(c[1] - start[1]) #erm manhattan computation not sure if tama
            )

            for cell in powerup_cells:
                path = self.make_bot_path(p, cell)
                
                if path:
                    self.bot_goal[p] = cell
                    self.bot_paths[p] = path
                    pu = self.model.powerups[cell]
                    print(f"{p} powerup: {pu} at {cell}")
                    return True

        # policy 2: reachable powerup within 4 cells (hostile/careful)
        else:
            nearby = [
                c for c in powerup_cells
                if abs(c[0] - start[0]) + abs(c[1] - start[1]) <= self.model.block_l * 4
            ]
            random.shuffle(nearby)

            for cell in nearby:
                path = self.make_bot_path(p, cell)
                if path:
                    self.bot_goal[p] = cell
                    self.bot_paths[p] = path
                    pu = self.model.powerups[cell]
                    print(f"{p} powerup: {pu} at {cell}")
                    return True

        return False

    def must_attack(self, p: int) -> bool:
        bot_type = self.bot_players[p]
        coord = self.model.sprite_coords[p]
        start = (self.model.snap_x(coord[0]), self.model.snap_y(coord[1]))

        players = [q for q in self.model.sprite_coords if q != p]
        if not players:
            return False

        # POLICY 1: reachable player within A cells (careful / greedy)
        if bot_type in ("careful", "greedy"):
            A = 3 if bot_type == "careful" else 6

            for q in players:
                qx, qy = self.model.sprite_coords[q]
                goal = (self.model.snap_x(qx), self.model.snap_y(qy))

                if abs(goal[0] - start[0]) + abs(goal[1] - start[1]) <= A * self.model.block_l:
                    path = self.make_bot_path(p, goal)
                    if path:
                        self.bot_goal[p] = goal
                        self.bot_paths[p] = path
                        print(f"{p} attack: player {q} at {goal}")
                        return True

        # POLICY 2: random player (hostile)
        else:
            shuffled = players[:]
            random.shuffle(shuffled)

            for q in shuffled:
                qx, qy = self.model.sprite_coords[q]
                goal = (self.model.snap_x(qx), self.model.snap_y(qy))
                path = self.make_bot_path(p, goal)
                if path:
                    self.bot_goal[p] = goal
                    self.bot_paths[p] = path
                    print(f"{p} attack: player {q} at {goal}")
                    return True

        return False

    def update_bots(self):
        for p in self.bot_players:
            if p not in self.model.sprite_coords:
                if p in self.bot_paths:
                    del self.bot_paths[p]
                continue

            x, y = self.model.sprite_coords[p]

            if self.reevaluate_condition(p, x, y):
                self.reevaluate(p, x, y)

            if p in self.bot_paths and self.bot_paths[p] != []:
                next_coord = self.bot_paths[p][0]

                self.bot_bomb_place(p, next_coord) # pag may nakaharang na soft block

                # para di sila dumeretso if may explosion sa next tile na pupuntahan nila
                # possible na tatanggalin kasi reevaluate should only happen at most once per tick
                # pero kasi pag nilalaro ko naaasar ako na dumederetso lang sila sa explosion HAHAHAH
                self.check_explosion_next_block(p, next_coord)

                self.move_bot_to(p, next_coord)

            """startup"""
            if (x, y) in self.model.spawn_points and (
                p not in self.bot_goal or p not in self.bot_paths):
                self.wander(p)

    def reevaluate_condition(self, p: int, x: int, y: int) -> bool:

        if not self.in_danger((x, y)) and self.escaping_bots[p] == 1:
            self.escaping_bots[p] = 0

        time, chance = self.bot_int_vals[p]

        if (pyxel.frame_count % round(30 * time) == 0 and
        random.randint(0, 99) < chance):
            
            # not sure if gagana, kasi bigla sila tumitigil, basta pinapawander state pag hindi nasa ibang state
            # nilipat ko lang sa di every frame para may onti silang pahinga HAHAHAHA
            if p not in self.bot_paths or self.bot_paths[p] == []:
                self.wander(p)

            five_cell_coords = [ (i, j)
                for i in range(x - self.model.block_l * 5,
                    x + self.model.block_l * 5 + 1,
                    self.model.block_l)
                for j in range(y - self.model.block_l * 5,
                    y + self.model.block_l * 5 + 1,
                    self.model.block_l)]
            
            explosion_ended = self.prev_explosions and not self.model.explosions

            new_bombs = self.model.all_bombs - self.prev_bombs
            new_bomb_near = any(bomb in five_cell_coords for bomb in new_bombs)

            """conditions bago magstart reevaluation according sa instructions"""
            if explosion_ended or new_bomb_near:

                if new_bomb_near:
                    print("new bomb near")

                if explosion_ended: # for debugging
                    print("explosion")

                return True
            
            return False
                    
        if pyxel.frame_count % 30 == 1: 
            self.prev_explosions = self.model.explosions.copy()
            self.prev_bombs = self.model.all_bombs.copy()
        
        return False

    def reevaluate(self, p: int, x: int, y: int):

        if self.bot_goal[p] == (x, y):
            print(f"{p} goal! {(x, y)}") # for debugging

        if self.in_danger((x, y), p) and self.escaping_bots[p] == 0:
            self.escape(p)
            return

        if self.must_obtain_powerup(p):
            self.get_powerup(p)
            return

        if self.must_attack(p):
            self.bot_states[p] = "attack"
            self.attack(p)
            return        

        self.wander(p)
        return






