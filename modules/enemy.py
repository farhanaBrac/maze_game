# modules/enemy.py

import random
import heapq
from OpenGL.GL import *
from modules.utils import midpoint_circle

class Enemy:
    """
    Normal enemy with fancy design: multi-circle body + spikes
    Uses BFS or random moves.
    """

    def __init__(self, x, y, maze):
        self.x = x
        self.y = y
        self.maze = maze
        self.path = []
        self.path_index = 0
        self.speed = 1
        self.last_move_time = 0.0

    def a_star_search(self, sx, sy, gx, gy):
        frontier = []
        heapq.heappush(frontier, (0, (sx, sy)))
        came_from = {}
        cost_so_far = {}
        came_from[(sx, sy)] = None
        cost_so_far[(sx, sy)] = 0

        while frontier:
            _, current = heapq.heappop(frontier)
            cx, cy = current
            if cx == gx and cy == gy:
                break

            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = cx+dx, cy+dy
                if 0 <= nx < self.maze.cols and 0 <= ny < self.maze.rows:
                    if self.maze.grid[ny][nx] == 1:
                        continue
                    new_cost = cost_so_far[current] + 1
                    if (nx, ny) not in cost_so_far or new_cost < cost_so_far[(nx, ny)]:
                        cost_so_far[(nx, ny)] = new_cost
                        priority = new_cost + abs(gx - nx) + abs(gy - ny)
                        heapq.heappush(frontier, (priority, (nx, ny)))
                        came_from[(nx, ny)] = current

        # reconstruct
        path = []
        current = (gx, gy)
        while current != (sx, sy):
            if current not in came_from:
                return []
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    def update_path(self, px, py):
        # 50% BFS, 50% random
        if random.random() < 0.5:
            self.path = self.a_star_search(self.x, self.y, px, py)
            self.path_index = 0
        else:
            self.path = []
            self.random_move()

    def random_move(self):
        directions = [(-1,0),(1,0),(0,-1),(0,1)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx = self.x + dx
            ny = self.y + dy
            if 0<=nx<self.maze.cols and 0<=ny<self.maze.rows:
                if self.maze.grid[ny][nx] == 0:
                    self.x = nx
                    self.y = ny
                    break

    def move_towards_player(self):
        if self.path and self.path_index < len(self.path):
            nx, ny = self.path[self.path_index]
            self.x = nx
            self.y = ny
            self.path_index += 1

    def render(self, scale_x, scale_y, maze_cols, maze_rows, radius=8):
        # center in OpenGL
        gl_cx = (self.x - maze_cols/2)*scale_x
        gl_cy = (maze_rows/2 - self.y)*scale_y

        # main circle
        body_pts = midpoint_circle(0, 0, radius)
        glColor3f(1.0, 0.0, 0.0)  # Red
        glBegin(GL_POINTS)
        for px, py in body_pts:
            glVertex2f(gl_cx + px*scale_x/10, gl_cy + py*scale_y/10)
        glEnd()

        # spikes
        import math
        spike_angles = [i*45 for i in range(8)]
        glColor3f(1.0, 1.0, 0.0)  # Yellow
        glBegin(GL_POINTS)
        for angle_deg in spike_angles:
            rad = math.radians(angle_deg)
            ex = int(radius*math.cos(rad))
            ey = int(radius*math.sin(rad))
            # We'll do a small line from (0,0) to (ex,ey). Let's just do a circle for thickness
            spike_pts = self.line_with_thickness(0,0,ex,ey,1)
            for sx, sy in spike_pts:
                glVertex2f(gl_cx + sx*scale_x/10, gl_cy + sy*scale_y/10)
        glEnd()

        # smaller circle = "eye"
        eye_pts = midpoint_circle(0,0,radius//3)
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_POINTS)
        for px, py in eye_pts:
            glVertex2f(gl_cx + px*scale_x/10, gl_cy + py*scale_y/10)
        glEnd()

    def line_with_thickness(self, x0, y0, x1, y1, thickness=1):
        """
        For spike, we want a small circle around each line point for thickness, or simpler approach.
        But let's just do midpoint_line and then midpoint_circle for each point (thickness=1).
        """
        from modules.utils import midpoint_line, midpoint_circle
        line_pts = midpoint_line(x0,y0,x1,y1)
        thick_pts = []
        for (lx, ly) in line_pts:
            circ = midpoint_circle(lx, ly, thickness)
            thick_pts.extend(circ)
        return thick_pts
