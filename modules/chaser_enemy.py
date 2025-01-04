# modules/chaser_enemy.py

from modules.enemy import Enemy

class ChaserEnemy(Enemy):
    """
    An enemy that ALWAYS chases the player with A* every move (no random moves).
    """

    def __init__(self, x, y, maze):
        super().__init__(x, y, maze)
        # Could set different speed or color if desired

    def update_path(self, target_x, target_y):
        # Always recalc path to the player
        self.path = self.a_star_search(self.x, self.y, target_x, target_y)
        self.path_index = 0

    def move_towards_player(self):
        if self.path and self.path_index < len(self.path):
            next_step = self.path[self.path_index]
            self.x, self.y = next_step
            self.path_index += 1
