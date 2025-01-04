# modules/patrolling_enemy.py

from modules.enemy import Enemy
import time

class PatrollingEnemy(Enemy):
    """
    Moves along a fixed list of waypoints in a loop or back-and-forth,
    ignoring BFS chase logic.
    """

    def __init__(self, x, y, maze, waypoints=None, wait_time=0.0):
        super().__init__(x, y, maze)
        self.waypoints = waypoints if waypoints else []
        self.waypoint_index = 0
        self.direction_forward = True
        self.wait_time = wait_time
        self.last_reach_time = 0.0

    def update_path(self, px, py):
        # ignore BFS, do patrol
        self.do_patrol()

    def do_patrol(self):
        if not self.waypoints:
            return

        tx, ty = self.waypoints[self.waypoint_index]
        if self.x == tx and self.y == ty:
            # waiting
            if time.time() - self.last_reach_time < self.wait_time:
                return
            else:
                self.last_reach_time = time.time()
                if self.direction_forward:
                    self.waypoint_index += 1
                    if self.waypoint_index >= len(self.waypoints):
                        # loop
                        self.waypoint_index = 0
                else:
                    # ping-pong approach if you like
                    # or keep it looping
                    pass

        tx, ty = self.waypoints[self.waypoint_index]
        dx = tx - self.x
        dy = ty - self.y
        if dx != 0:
            dx = 1 if dx>0 else -1
        if dy != 0:
            dy = 1 if dy>0 else -1
        nx = self.x + dx
        ny = self.y + dy
        if 0<=nx<self.maze.cols and 0<=ny<self.maze.rows:
            if self.maze.grid[ny][nx] == 0:
                self.x = nx
                self.y = ny
