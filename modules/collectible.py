# modules/collectible.py

from OpenGL.GL import *
from modules.utils import midpoint_circle

class Collectible:
    """
    A collectible gem, never in the border, using fancy circle design.
    """

    def __init__(self, x, y, collected=False):
        self.x = x
        self.y = y
        self.collected = collected

    def render(self, scale_x, scale_y, maze_cols, maze_rows, radius=5):
        if self.collected:
            return

        # Convert grid->OpenGL
        gl_cx = (self.x - maze_cols/2)*scale_x
        gl_cy = (maze_rows/2 - self.y)*scale_y

        # Circle points
        circle_pts = midpoint_circle(0, 0, radius)
        glColor3f(1.0, 1.0, 0.0)  # Yellow

        glBegin(GL_POINTS)
        for px, py in circle_pts:
            glVertex2f(gl_cx + px*scale_x/10, gl_cy + py*scale_y/10)
        glEnd()
