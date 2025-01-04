# modules/player.py

from OpenGL.GL import *
from modules.utils import midpoint_circle, midpoint_line

class Player:
    """
    A fancy player using multiple circles + a "visor" line, all in GL_POINTS.
    """

    def __init__(self, x=1, y=1):
        self.x = x
        self.y = y

    def render(self, scale_x, scale_y, maze_cols, maze_rows,
               radius=10, is_invisible=False):
        """
        If is_invisible is True, draw the player in gold color. Otherwise green.
        """
        gl_cx = (self.x - maze_cols/2)*scale_x
        gl_cy = (maze_rows/2 - self.y)*scale_y

        if is_invisible:
            # Outer circle gold, inner circle darker gold
            outer_color = (1.0, 0.84, 0.0)  # gold
            inner_color = (0.85, 0.7, 0.0)
        else:
            # Normal green
            outer_color = (0.0, 1.0, 0.0)
            inner_color = (0.0, 0.7, 0.0)

        # Outer circle
        outer_pts = midpoint_circle(0, 0, radius)
        glColor3f(*outer_color)
        glBegin(GL_POINTS)
        for px, py in outer_pts:
            glVertex2f(gl_cx + px*scale_x/10, gl_cy + py*scale_y/10)
        glEnd()

        # Inner circle
        inner_pts = midpoint_circle(0, 0, radius-2)
        glColor3f(*inner_color)
        glBegin(GL_POINTS)
        for px, py in inner_pts:
            glVertex2f(gl_cx + px*scale_x/10, gl_cy + py*scale_y/10)
        glEnd()

        # Visor line
        visor_left = (-radius+2, 0)
        visor_right = (radius-2, 0)
        visor_line = midpoint_line(visor_left[0], visor_left[1],
                                   visor_right[0], visor_right[1])
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_POINTS)
        for px, py in visor_line:
            glVertex2f(gl_cx + px*scale_x/10, gl_cy + py*scale_y/10)
        glEnd()
