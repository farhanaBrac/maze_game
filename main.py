import sys
import time
import random
import json
import os

import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# Local modules
from modules.maze import Maze
from modules.collectible import Collectible
from modules.enemy import Enemy
from modules.patrolling_enemy import PatrollingEnemy
from modules.player import Player
from modules.powerup import PowerUp
from modules.button import Button
from modules.utils import render_text

MENU_STATE = 0
INSTRUCTIONS_STATE = 1
GAME_STATE = 2
GAME_OVER_STATE = 3
menu_options = ["Start Game", "Instructions", "Exit"]

def load_progress():
    """
    Loads highest level from savegame.json if it exists, else returns 1.
    """
    if os.path.exists("savegame.json"):
        try:
            with open("savegame.json","r") as f:
                data = json.load(f)
                return data.get("highest_level",1)
        except:
            return 1
    return 1

def save_progress(level):
    """
    Saves the highest level to savegame.json.
    """
    data = {"highest_level": level}
    with open("savegame.json","w") as f:
        json.dump(data,f)

class Game:
    def __init__(self, width=800, height=600, maze_rows=21, maze_cols=21):
        self.width = width
        self.height = height

        # Force odd dims
        self.maze_rows = maze_rows if maze_rows % 2 != 0 else maze_rows + 1
        self.maze_cols = maze_cols if maze_cols % 2 != 0 else maze_cols + 1

        self.reserved_ui_height = 60.0
        self.scale_x = self.width / self.maze_cols
        self.scale_y = (self.height - self.reserved_ui_height) / self.maze_rows

        if not glfw.init():
            print("Failed to init GLFW")
            sys.exit(-1)

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,2)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,1)

        self.window = glfw.create_window(self.width, self.height, "Pixel Adventure Maze", None, None)
        if not self.window:
            glfw.terminate()
            sys.exit(-1)

        glfw.make_context_current(self.window)
        self.init_gl()

        # Load saved progress
        self.current_level = load_progress()
        print(f"Starting from level: {self.current_level}")

        self.score = 0
        self.is_paused = False
        self.current_state = MENU_STATE
        self.selected_option = 0

        # Timed level
        self.level_time = 60.0
        self.last_time_update = time.time()

        # Maze: uses generate_maze() + optional extra paths for loops
        self.maze = Maze(self.maze_rows, self.maze_cols, extra_passages=2)
        self.maze.scale_x = self.scale_x
        self.maze.scale_y = self.scale_y

        # Player
        self.player = Player(x=1, y=1)

        # Entities
        self.enemies = []
        self.collectibles = []
        self.powerups = []

        # Exit position
        self.exit_x = self.maze.cols - 2
        self.exit_y = self.maze.rows - 2

        # Invisibility states
        self.is_invisible = False
        self.invisible_until = 0.0

        # Speed boost states
        self.speed_boost_active = False
        self.speed_boost_until = 0.0

        # Initialize spawns
        self.initialize_entities()

        # UI Buttons
        self.buttons = self.initialize_buttons()

        self.last_enemy_move_time = 0.0
        self.enemy_move_interval = 0.5

        # Register callbacks
        glfw.set_key_callback(self.window, self.key_callback)
        glfw.set_mouse_button_callback(self.window, self.mouse_button_callback)

    def init_gl(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(-self.width/2, self.width/2, -self.height/2, self.height/2)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def initialize_buttons(self):
        btns = []
        w = 80.0
        h = 30.0
        pad = 10.0
        button_y = self.height/2 - (self.reserved_ui_height/2) - pad

        pause_btn = Button("Pause",
                           x=-self.width/2 + pad,
                           y=button_y,
                           width=w,
                           height=h,
                           action=self.pause_game)
        btns.append(pause_btn)

        restart_btn = Button("Restart",
                             x=-self.width/2 + pad + (w+pad),
                             y=button_y,
                             width=w,
                             height=h,
                             action=self.restart_game)
        btns.append(restart_btn)

        exit_btn = Button("Exit",
                          x=-self.width/2 + pad + 2*(w+pad),
                          y=button_y,
                          width=w,
                          height=h,
                          action=self.exit_game)
        btns.append(exit_btn)

        return btns

    def random_path_cell(self):
        """
        Returns a (x, y) that is a valid path cell (grid[y][x]==0),
        in the interior (1..cols-2, 1..rows-2).
        """
        while True:
            x = random.randint(1, self.maze.cols - 2)
            y = random.randint(1, self.maze.rows - 2)
            if self.maze.grid[y][x] == 0:
                return (x, y)

    def initialize_entities(self):
        """
        Resets the level timer, spawns enemies, collectibles, power-ups, and exit.
        """
        self.level_time = 60.0
        self.last_time_update = time.time()

        # Reset player
        self.player.x = 1
        self.player.y = 1

        self.enemies = []
        self.collectibles = []
        self.powerups = []

        # Normal enemies on valid path cells
        num_normal_enemies = 1
        for _ in range(num_normal_enemies):
            x, y = self.random_path_cell()
            e = Enemy(x, y, self.maze)
            self.enemies.append(e)

        # Patrolling enemy with random route
        route = []
        route_size = 4
        for _ in range(route_size):
            rx, ry = self.random_path_cell()
            route.append((rx, ry))
        patroller = PatrollingEnemy(route[0][0], route[0][1],
                                    self.maze,
                                    waypoints=route,
                                    wait_time=1.0)
        self.enemies.append(patroller)

        # spawn some collectibles (avoid border, walls)
        self.spawn_collectibles(num=4)

        # spawn powerups on valid path
        px, py = self.random_path_cell()
        self.powerups.append(PowerUp(px, py, "speed"))
        px2, py2 = self.random_path_cell()
        self.powerups.append(PowerUp(px2, py2, "invincibility"))

        # place exit far from enemies
        self.place_exit_far_from_enemies()

    def place_exit_far_from_enemies(self):
        max_tries = 500
        dist_thresh = 8
        tries = 0

        while tries < max_tries:
            tries += 1
            ex = random.randint(1, self.maze.cols - 2)
            ey = random.randint(1, self.maze.rows - 2)
            if self.maze.grid[ey][ex] == 0:
                too_close = False
                for en in self.enemies:
                    dist = abs(en.x - ex) + abs(en.y - ey)
                    if dist < dist_thresh:
                        too_close = True
                        break
                if not too_close:
                    self.exit_x = ex
                    self.exit_y = ey
                    return

        # fallback
        self.exit_x = self.maze.cols - 2
        self.exit_y = self.maze.rows - 2

    def spawn_collectibles(self, num=4):
        spawned = 0
        while spawned < num:
            x, y = self.random_path_cell()
            # ensure no overlap
            already = any((c.x==x and c.y==y) for c in self.collectibles)
            if not already:
                self.collectibles.append(Collectible(x,y))
                spawned += 1

    # -------------- RENDERING --------------

    def render_main_menu(self):
        glClearColor(0,0,0,1)
        glClear(GL_COLOR_BUFFER_BIT)
        render_text(-200,150,"PIXEL ADVENTURE MAZE",GLUT_BITMAP_HELVETICA_18,(1,1,1))
        sy=50.0
        for idx,opt in enumerate(menu_options):
            color = (1,0,0) if idx==self.selected_option else (1,1,1)
            render_text(-50, sy-idx*40, opt, GLUT_BITMAP_HELVETICA_18, color)

    def render_instructions(self):
        glClearColor(0,0,0,1)
        glClear(GL_COLOR_BUFFER_BIT)
        render_text(-100,150,"INSTRUCTIONS",GLUT_BITMAP_HELVETICA_18,(1,1,1))
        lines = [
            "Arrow Keys: Move Player",
            "I: Invisibility for 3s (turns gold, can't be killed)",
            "P: Pause/Resume",
            "Fancy designs using GL_POINTS + midpoint algos only",
            "Collectibles/Enemies spawn on valid path cells only",
            "Patrolling Enemy route is also on path cells",
            "Save progress in savegame.json"
        ]
        yy=100
        for line in lines:
            render_text(-300, yy, line, GLUT_BITMAP_HELVETICA_18,(1,1,1))
            yy-=30

    def render_maze(self):
        self.maze.render(self.scale_x,self.scale_y)

    def render_player(self):
        # Pass is_invisible so the player is drawn gold if invisible
        self.player.render(self.scale_x,
                           self.scale_y,
                           self.maze.cols,
                           self.maze.rows,
                           radius=10,
                           is_invisible=self.is_invisible)

    def render_enemies(self):
        for en in self.enemies:
            en.render(self.scale_x,self.scale_y,self.maze.cols,self.maze.rows)

    def render_collectibles(self):
        for c in self.collectibles:
            c.render(self.scale_x,self.scale_y,self.maze.cols,self.maze.rows)

    def render_powerups(self):
        for p in self.powerups:
            p.render(self.scale_x,self.scale_y,self.maze.cols,self.maze.rows)

    def render_exit(self):
        gl_x = (self.exit_x - self.maze.cols/2)*self.scale_x
        gl_y = (self.maze.rows/2 - self.exit_y)*self.scale_y
        size=8
        left=int(gl_x-size)
        right=int(gl_x+size)
        bottom=int(gl_y-size)
        top=int(gl_y+size)
        glColor3f(0,0,1)
        glBegin(GL_POINTS)
        for px in range(left,right+1):
            for py in range(bottom,top+1):
                glVertex2f(px,py)
        glEnd()
        render_text(gl_x-15,gl_y+size+5,"Exit",GLUT_BITMAP_HELVETICA_12,(1,1,1))

    def render_score(self):
        glColor3f(1,1,1)
        s_text = f"Score: {self.score}"
        sx=-350
        sy=self.height/2 - (self.reserved_ui_height/2) - 20
        render_text(sx,sy,s_text,GLUT_BITMAP_HELVETICA_18,(1,1,1))

        time_text=f"Time: {int(self.level_time)}s"
        render_text(sx,sy-30,time_text,GLUT_BITMAP_HELVETICA_18,(1,1,1))

    def render_level(self):
        lvl_text=f"Level: {self.current_level}"
        lx=250
        ly=self.height/2 - (self.reserved_ui_height/2) -20
        render_text(lx,ly,lvl_text,GLUT_BITMAP_HELVETICA_18,(1,1,1))

    def render_buttons(self):
        for b in self.buttons:
            b.render()

    def render_paused_overlay(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
        left=-int(self.width/2)
        right=int(self.width/2)
        bottom=-int(self.height/2)
        top=int(self.height/2)
        glColor4f(0,0,0,0.5)
        glBegin(GL_POINTS)
        for px in range(left,right+1):
            for py in range(bottom,top+1):
                glVertex2f(px,py)
        glEnd()
        glDisable(GL_BLEND)
        render_text(-30,0,"Paused",GLUT_BITMAP_HELVETICA_18,(1,1,1))

    def render_game_over_screen(self):
        glClearColor(0,0,0,1)
        glClear(GL_COLOR_BUFFER_BIT)
        render_text(-100,100,"GAME OVER",GLUT_BITMAP_HELVETICA_18,(1,0,0))
        fin_sc=f"Final Score: {self.score}"
        render_text(-70,50,fin_sc,GLUT_BITMAP_HELVETICA_18,(1,1,1))
        ops=["Restart (R)","Exit (E)"]
        ox=-100
        oy=-50
        for op in ops:
            render_text(ox,oy,op,GLUT_BITMAP_HELVETICA_18,(1,1,1))
            oy-=30

    def render_game(self):
        glClearColor(0,0,0,1)
        glClear(GL_COLOR_BUFFER_BIT)
        glPushMatrix()
        glTranslatef(0, -self.reserved_ui_height/2, 0)
        self.render_maze()
        self.render_player()
        self.render_enemies()
        self.render_collectibles()
        self.render_powerups()
        self.render_exit()
        glPopMatrix()
        self.render_score()
        self.render_level()
        self.render_buttons()

        if self.is_paused:
            self.render_paused_overlay()

    def render(self):
        if self.current_state==MENU_STATE:
            self.render_main_menu()
        elif self.current_state==INSTRUCTIONS_STATE:
            self.render_instructions()
        elif self.current_state==GAME_STATE:
            self.render_game()
        elif self.current_state==GAME_OVER_STATE:
            self.render_game_over_screen()

    # -------------- LOGIC --------------

    def update_enemies(self):
        now=time.time()
        for en in self.enemies:
            if now - en.last_move_time>=en.speed:
                en.update_path(self.player.x,self.player.y)
                if hasattr(en,"move_towards_player"):
                    en.move_towards_player()
                en.last_move_time=now

            # If the player is NOT invisible, we can kill them
            if not self.is_invisible:
                if en.x== self.player.x and en.y== self.player.y:
                    self.current_state= GAME_OVER_STATE
                    print("Collision with enemy! Game Over.")

    def update_game_logic(self):
        if self.is_paused or self.current_state!=GAME_STATE:
            return
        now=time.time()
        delta= now- self.last_time_update
        self.last_time_update= now
        self.level_time-= delta
        if self.level_time<=0:
            print("Time ran out!")
            self.current_state=GAME_OVER_STATE
            return

        # End invisibility if time is up
        if self.is_invisible and now>= self.invisible_until:
            self.is_invisible= False
            print("Invisibility ended!")

        # speed boost check
        if self.speed_boost_active and now>= self.speed_boost_until:
            self.speed_boost_active= False
            print("Speed boost ended!")

        # update enemies
        if now-self.last_enemy_move_time>= self.enemy_move_interval:
            self.update_enemies()
            self.last_enemy_move_time= now

    def move_player(self,dx,dy):
        steps= 2 if self.speed_boost_active else 1
        for _ in range(steps):
            nx= self.player.x+ dx
            ny= self.player.y+ dy
            # Bound checks
            if nx<0 or nx>= self.maze.cols or ny<0 or ny>= self.maze.rows:
                return
            # Wall checks
            if self.maze.grid[ny][nx]== 1:
                return

            self.player.x= nx
            self.player.y= ny

            # Collect collectibles
            for c in self.collectibles:
                if not c.collected and c.x== self.player.x and c.y== self.player.y:
                    c.collected= True
                    self.score+= 10
                    print(f"Collected gem: ({c.x},{c.y}), Score={self.score}")

            # Collect powerups
            for p in self.powerups:
                if not p.collected and p.x==self.player.x and p.y==self.player.y:
                    p.collected= True
                    print(f"Power-up: {p.power_type}")
                    if p.power_type=="speed":
                        self.speed_boost_active= True
                        self.speed_boost_until= time.time()+5
                    elif p.power_type=="invincibility":
                        self.is_invincible= True
                        self.invisible_until= time.time()+5
                        print("Invincibility power-up! Invisible for 5s")

            # Check exit
            if self.player.x== self.exit_x and self.player.y== self.exit_y:
                self.current_level+=1
                print(f"Level complete! Now level {self.current_level}")
                save_progress(self.current_level)
                self.maze.generate_maze()
                self.maze.carve_extra_paths(2)
                self.initialize_entities()
                break

            # If not invisible, check collision with enemies
            if not self.is_invisible:
                for en in self.enemies:
                    if en.x== self.player.x and en.y== self.player.y:
                        self.current_state= GAME_OVER_STATE
                        print("Collision with enemy! Game Over.")
                        break

    # -------------- GAME STATES --------------

    def pause_game(self):
        self.is_paused= True
        print("Game Paused.")

    def resume_game(self):
        self.is_paused= False
        print("Game Resumed.")

    def restart_game(self):
        self.score= 0
        self.current_level= 1
        save_progress(self.current_level)
        self.maze.generate_maze()
        self.maze.carve_extra_paths(2)
        self.initialize_entities()
        self.current_state= GAME_STATE
        self.is_paused= False
        print("Game Restarted, progress set to level 1.")

    def exit_game(self):
        glfw.set_window_should_close(self.window,True)

    # -------------- INPUTS --------------

    def key_callback(self,window,key,scancode,action,mods):
        if action!=glfw.PRESS:
            return

        if self.current_state==MENU_STATE:
            if key==glfw.KEY_UP:
                self.selected_option=(self.selected_option-1)%len(menu_options)
            elif key==glfw.KEY_DOWN:
                self.selected_option=(self.selected_option+1)%len(menu_options)
            elif key in [glfw.KEY_ENTER,glfw.KEY_KP_ENTER]:
                selected=menu_options[self.selected_option]
                if selected=="Start Game":
                    self.load_progress_and_start()
                    self.current_state=GAME_STATE
                elif selected=="Instructions":
                    self.current_state=INSTRUCTIONS_STATE
                elif selected=="Exit":
                    glfw.set_window_should_close(self.window,True)

        elif self.current_state==INSTRUCTIONS_STATE:
            if key==glfw.KEY_B:
                self.current_state=MENU_STATE

        elif self.current_state==GAME_STATE:
            if key==glfw.KEY_P:
                if self.is_paused:
                    self.resume_game()
                else:
                    self.pause_game()
            elif not self.is_paused:
                # Movement
                if key==glfw.KEY_UP:
                    self.move_player(0,-1)
                elif key==glfw.KEY_DOWN:
                    self.move_player(0,1)
                elif key==glfw.KEY_LEFT:
                    self.move_player(-1,0)
                elif key==glfw.KEY_RIGHT:
                    self.move_player(1,0)
                # Invisibility by pressing I
                elif key==glfw.KEY_I:
                    self.is_invisible= True
                    self.invisible_until= time.time()+3
                    print("Invisibility activated for 3s!")

        elif self.current_state==GAME_OVER_STATE:
            if key==glfw.KEY_R:
                self.restart_game()
            elif key==glfw.KEY_E:
                glfw.set_window_should_close(self.window,True)

    def mouse_button_callback(self,window,button,action,mods):
        if action!=glfw.PRESS:
            return
        xpos,ypos=glfw.get_cursor_pos(window)
        gl_x=xpos/self.width*self.width - self.width/2
        gl_y=self.height/2 - ypos/self.height*self.height

        for b in self.buttons:
            if b.is_clicked(gl_x, gl_y):
                b.action()
                break

    def load_progress_and_start(self):
        lvl=load_progress()
        self.current_level=lvl
        print(f"Loaded progress, level={lvl}")
        self.maze.generate_maze()
        self.maze.carve_extra_paths(2)
        self.initialize_entities()

    def run(self):
        while not glfw.window_should_close(self.window):
            self.render()
            self.update_game_logic()
            glfw.swap_buffers(self.window)
            glfw.poll_events()
        glfw.terminate()

def main():
    glutInit(sys.argv)
    game=Game(800,600,21,21)
    game.run()

if __name__=="__main__":
    main()
