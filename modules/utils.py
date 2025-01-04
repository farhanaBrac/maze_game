# modules/utils.py

from OpenGL.GL import *
from OpenGL.GLUT import *

def render_text(x, y, text, font, color=(1.0, 1.0, 1.0)):
    """
    Renders bitmap text at (x, y).
    """
    glColor3f(*color)
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))

def midpoint_circle(cx, cy, radius):
    """
    Midpoint Circle Algorithm: returns a list of (x,y) for circle perimeter.
    """
    points = []
    x = radius
    y = 0
    p = 1 - radius

    if radius > 0:
        points.append((cx, cy + radius))
        points.append((cx, cy - radius))
        points.append((cx + radius, cy))
        points.append((cx - radius, cy))

    while x > y:
        y += 1
        if p <= 0:
            p = p + 2*y + 1
        else:
            x -= 1
            p = p + 2*y - 2*x + 1

        if x < y:
            break

        points.extend([
            (cx + x, cy + y),
            (cx - x, cy + y),
            (cx + x, cy - y),
            (cx - x, cy - y),
            (cx + y, cy + x),
            (cx - y, cy + x),
            (cx + y, cy - x),
            (cx - y, cy - x)
        ])
    return points

def midpoint_line(x0, y0, x1, y1):
    """
    Midpoint Line Algorithm: returns a list of (x, y) for line from (x0,y0) to (x1,y1).
    """
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1

    if dy <= dx:
        err = dx / 2.0
        while x != x1:
            points.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            points.append((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    points.append((x, y))
    return points


