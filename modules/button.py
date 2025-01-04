# modules/button.py

import ctypes
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from modules.utils import render_text, midpoint_line

class Button:
    """
    Represents a clickable button in the Pixel Adventure Maze game.
    """

    def __init__(self, label, x, y, width, height, action):
        self.label = label
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.action = action

    def render(self):
        # Fill button with points
        glColor3f(0.2, 0.2, 0.2)
        x_min = int(self.x)
        x_max = int(self.x + self.width)
        y_min = int(self.y - self.height)
        y_max = int(self.y)

        glBegin(GL_POINTS)
        for px in range(x_min, x_max):
            for py in range(y_min, y_max):
                glVertex2f(px, py)
        glEnd()

        # Border with midpoint_line
        glColor3f(1.0, 1.0, 1.0)
        top_line = midpoint_line(x_min, y_max, x_max, y_max)
        bottom_line = midpoint_line(x_min, y_min, x_max, y_min)
        left_line = midpoint_line(x_min, y_min, x_min, y_max)
        right_line = midpoint_line(x_max, y_min, x_max, y_max)

        glBegin(GL_POINTS)
        for pt in (top_line + bottom_line + left_line + right_line):
            glVertex2f(pt[0], pt[1])
        glEnd()

        # Label
        label_bytes = self.label.encode('utf-8')
        label_buffer = ctypes.create_string_buffer(label_bytes)
        label_ptr = ctypes.cast(label_buffer, ctypes.POINTER(ctypes.c_ubyte))
        label_w = glutBitmapLength(GLUT_BITMAP_HELVETICA_18, label_ptr)
        label_x = self.x + (self.width - label_w) / 2
        label_y = self.y - self.height/2 - 5
        render_text(label_x, label_y, self.label, GLUT_BITMAP_HELVETICA_18, (1,1,1))

    def is_clicked(self, cx, cy):
        return (self.x <= cx <= self.x + self.width) and (self.y - self.height <= cy <= self.y)
