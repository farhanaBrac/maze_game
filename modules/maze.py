# modules/maze.py

import random
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from modules.utils import midpoint_line

class Maze:
    """
    Represents the maze in the Pixel Adventure Maze game.
    Each cell in 'grid' is either 1 (wall) or 0 (path).
    """

    def __init__(self, rows, cols, extra_passages=2):
        """
        :param rows: Number of rows in the maze
        :param cols: Number of columns in the maze
        :param extra_passages: How many extra passages to carve after DFS
        """
        self.rows = rows
        self.cols = cols
        self.grid = [[1 for _ in range(cols)] for _ in range(rows)]
        self.scale_x = 0.0
        self.scale_y = 0.0

        # Primary generation via DFS
        self.generate_maze()

        # Carve additional paths for loops
        if extra_passages > 0:
            self.carve_extra_paths(extra_passages)

    def generate_maze(self):
        """
        Generates the maze using a Depth-First Search (DFS) approach.
        Creates a single connected path from start (1,1) to end (cols-2, rows-2).
        """
        stack = []
        start_x, start_y = 1, 1
        self.grid[start_y][start_x] = 0
        stack.append((start_x, start_y))

        while stack:
            current_x, current_y = stack[-1]
            directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]
            random.shuffle(directions)
            carved = False

            for dx, dy in directions:
                nx = current_x + dx
                ny = current_y + dy
                if 1 <= nx < self.cols - 1 and 1 <= ny < self.rows - 1 and self.grid[ny][nx] == 1:
                    # Carve path
                    self.grid[ny][nx] = 0
                    # Carve the wall in-between
                    mid_x = current_x + dx // 2
                    mid_y = current_y + dy // 2
                    self.grid[mid_y][mid_x] = 0

                    stack.append((nx, ny))
                    carved = True
                    break

            if not carved:
                stack.pop()

    def carve_extra_paths(self, num_extra):
        """
        Randomly carve out additional passages to create loops/alternative routes.
        """
        attempts = 0
        max_attempts = 500

        while num_extra > 0 and attempts < max_attempts:
            attempts += 1
            wx = random.randint(1, self.cols - 2)
            wy = random.randint(1, self.rows - 2)

            if self.grid[wy][wx] == 1:
                # Count open neighbors
                open_neighbors = 0
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx = wx + dx
                    ny = wy + dy
                    if 0 <= nx < self.cols and 0 <= ny < self.rows:
                        if self.grid[ny][nx] == 0:
                            open_neighbors += 1

                if open_neighbors >= 2:
                    self.grid[wy][wx] = 0
                    num_extra -= 1

    def render(self, scale_x, scale_y, reserved_ui_height=60.0):
        """
        Renders the maze walls using only GL_POINTS + the Midpoint Line Algorithm.
        """
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_POINTS)

        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == 1:
                    # Horizontal neighbor
                    if col < self.cols - 1 and self.grid[row][col + 1] == 1:
                        line_points = midpoint_line(col, row, col + 1, row)
                        for px, py in line_points:
                            glVertex2f((px - self.cols / 2) * scale_x,
                                       (self.rows / 2 - py) * scale_y)
                    # Vertical neighbor
                    if row < self.rows - 1 and self.grid[row + 1][col] == 1:
                        line_points = midpoint_line(col, row, col, row + 1)
                        for px, py in line_points:
                            glVertex2f((px - self.cols / 2) * scale_x,
                                       (self.rows / 2 - py) * scale_y)
        glEnd()
