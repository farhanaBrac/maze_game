# modules/powerup.py

from OpenGL.GL import *
from modules.utils import midpoint_circle

class PowerUp:
    """
    Represents a special power-up in the Pixel Adventure Maze game.
    Examples: speed boost, invincibility, etc.
    """

    def __init__(self, x, y, power_type="speed", collected=False):
        self.x = x
        self.y = y
        self.power_type = power_type  # e.g. "speed", "invincibility"
        self.collected = collected

    def render(self, scale_x, scale_y, maze_cols, maze_rows, radius=5):
        if self.collected:
            return

        gl_cx = (self.x - maze_cols / 2) * scale_x
        gl_cy = (maze_rows / 2 - self.y) * scale_y

        circle_points = midpoint_circle(0, 0, radius)

        # Pick color based on power_type
        if self.power_type == "speed":
            glColor3f(0.5, 0.8, 1.0)  # Light blue
        elif self.power_type == "invincibility":
            glColor3f(1.0, 0.8, 0.0)  # Golden
        else:
            glColor3f(1.0, 0.5, 0.5)  # Fallback color

        glBegin(GL_POINTS)
        for px, py in circle_points:
            glVertex2f(gl_cx + px * scale_x / 10, gl_cy + py * scale_y / 10)
        glEnd()
