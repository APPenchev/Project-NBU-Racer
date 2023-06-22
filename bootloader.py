import math
import os
import time
from abc import abstractmethod

import glm
import pywavefront

from model import *
import random
from scene import BasicScene
from text_handler import generate_text_texture
from vbo import RectangleVBO
from vehicle import Vehicle
from custom_objects import *
import pygame as pg

SPEED = 0.005
TURN_SPEED = 0.01
CAR_POSITIONS = [(23, 0.1, 29), (20.8, 0.1, 33), (17.5, 0.1, 25.9), (15.2, 0.1, 29.9)]


class RaceScene(BasicScene):
    def __init__(self, scene_manager):
        super().__init__(scene_manager)

    def load(self):
        self.main_car = Vehicle(self, int(config.global_variables['chosen_car'][0]), pos=CAR_POSITIONS[0], rot=(0, 1.05, 0),
                                variant=config.global_variables['chosen_car'][1])
        self.speedometer = Speedometer(self, self.main_car)
        self.lap = Lap(self)
        self.ss = StartSequence(self)
        self.pause = Pause(self)
        self.game_starting = True
        self.game_ended = False
        self.times = {}
        self.road_squares = []
        self.visited = []
        self.replays = [[], [], []]
        self.enemy_controls = {}
        self.enemies = {}
        self.scripts = {}
        self.end_screen = False
        self.pause.hidden = True
        self.paused = False
        self.paused_time = 0

        self.camera.position = glm.vec3(self.main_car.pos + (self.main_car.forward * 30))
        self.camera.position.y += 15
        self.camera.yaw = 210
        self.camera.pitch = -50
        self.camera.fov = int(config.global_variables['fovs'][int(config.global_variables['fov'][0])])
        self.camera.update_rotation()
        self.camera.update()
        self.skybox = Skybox(self)

        self.add_object(
            ExtendedBaseModel(self, vao_name='cube', tex_id='grass', pos=(0, -0.01, 0), scale=(300, 0.001, 300),
                              tiling=200))
        self.add_object(ExtendedBaseModel(self, vao_name='track', tex_id='asphalt', pos=(0, 0.1, 0), tiling=10))
        self.add_object(ExtendedBaseModel(self, vao_name='markings', tex_id='markings'))
        self.add_object(ExtendedBaseModel(self, vao_name='rail', tex_id='rail'))
        self.add_object(ExtendedBaseModel(self, vao_name='finish', tex_id='finish'))
        self.add_object(ExtendedBaseModel(self, vao_name='tree', tex_id='tree'))
        self.add_object(ExtendedBaseModel(self, vao_name='rock', tex_id='rock'))

        replays = os.listdir('replays')

        for file_name in replays:
            with open(f'replays/{file_name}', 'r') as file:
                car = 0
                place = 0
                for i, line in enumerate(file):
                    if i == 0:
                        car = int(line)
                    elif i == 1:
                        place = int(line) - 1
                        self.replays[place].append({'Car': car})
                    elif '*' in line:
                        speed = line.split(' ')
                        self.replays[place][-1]['Speed'] = float(speed[1])
                        self.replays[place][-1]['File'] = file_name
                    else:
                        tick, action = line.split(' ')
                        tick = int(tick)
                        action = int(action)
                        if tick not in self.replays[place][-1]:
                            self.replays[place][-1][tick] = [action]
                        else:
                            self.replays[place][-1][tick].append(action)
        self.setup_cars()
        self.add_object(self.main_car)
        self.add_object(self.speedometer)
        self.add_object(self.lap)
        self.add_object(self.ss)
        self.add_object(self.pause)
        music_name = config.global_variables['car_themes'][config.global_variables['car_types'][int(config.global_variables['chosen_car'][0])]]
        pg.mixer.music.load(f"audio/{music_name}.mp3")
        pg.mixer.music.set_volume(
            int(config.global_variables['music_volumes'][int(config.global_variables['music_volume'][0])]) / 100)

        self.speedometer.hidden = True
        self.lap.hidden = True
        marks = []

        with open('objects/Track_path.txt', 'r') as file:
            for line in file:
                if line.startswith('v'):
                    _, x, y, z = line.split()
                    point = [float(x), float(y), float(z)]
                    marks.append(glm.vec3(point))

        for i in range(len(marks) - 1):
            corner1 = glm.vec3(-1, 0, -1)
            corner2 = glm.vec3(-1, 0, 1)
            corner3 = glm.vec3(1, 0, -1)
            corner4 = glm.vec3(1, 0, 1)

            m_model = glm.mat4(1.0)

            translation_matrix = glm.translate(glm.mat4(1.0), marks[i])
            m_model = m_model @ translation_matrix

            direction = glm.normalize(marks[i + 1] - marks[i])
            up_vector = glm.vec3(0, 1, 0)
            right_vector = glm.cross(up_vector, direction)
            rotation_matrix = glm.mat4(
                glm.vec4(right_vector, 0),
                glm.vec4(up_vector, 0),
                glm.vec4(-direction, 0),
                glm.vec4(0, 0, 0, 1)
            )
            m_model = m_model @ rotation_matrix

            scaling_matrix = glm.scale(glm.mat4(1.0), glm.vec3(5, 1, 3))
            m_model = m_model @ scaling_matrix

            corner1 = glm.vec3(m_model * glm.vec4(corner1, 1))
            corner2 = glm.vec3(m_model * glm.vec4(corner2, 1))
            corner3 = glm.vec3(m_model * glm.vec4(corner3, 1))
            corner4 = glm.vec3(m_model * glm.vec4(corner4, 1))
            self.road_squares.append([corner1, corner2, corner3, corner4])

        pg.mixer.music.play()

        self.start_time = time.time()
        self.starting_sequence()

    def setup_cars(self):
        for i in range(0, 3):
            self.scripts[i + 1] = random.choice(self.replays[i])
            car = Vehicle(self, int(self.scripts[i+1]['Car']), pos=CAR_POSITIONS[i + 1], rot=(0, 1.05, 0),
                          variant=f"{random.randint(1,int(config.global_variables['cars'][config.global_variables['car_types'][int(self.scripts[i+1]['Car'])]]))}")
            self.enemies[i + 1] = car
            self.add_object(car)
            self.enemy_controls[i + 1] = [False] * 4
            self.times[f'Player {i + 2}'] = float(self.scripts[i + 1]['Speed'])

    def starting_sequence(self):
        if self.tick % 82 == 0:
            self.ss.update_state()

        if self.tick < 150:
            self.camera.position += ((self.main_car.pos + self.main_car.forward * 2) - self.camera.position) * 0.02
            self.camera.pitch += (0 - self.camera.pitch) * 0.02
            self.camera.update_rotation()
        if self.tick == 160:
            self.camera.position = self.main_car.pos + self.main_car.forward * 2.5 + self.main_car.side * 1 + self.main_car.up * 0.5
        if 160 < self.tick < 300:
            self.camera.position += self.camera.side / 80

        if self.tick > 300:
            self.camera.position = self.main_car.pos - self.main_car.forward * 3
            self.camera.position.y = self.main_car.pos.y + 2
            self.camera.forward = glm.vec3(self.main_car.forward)
            self.camera.up = glm.vec3(self.main_car.up)
            self.camera.side = glm.vec3(self.main_car.side)

        if self.tick > 350:
            self.game_starting = False
            self.speedometer.hidden = False
            self.lap.hidden = False
            self.ss.hidden = True

    def custom_update(self):

        if self.game_starting:
            self.starting_sequence()
            return
        if self.paused:
            self.tick -= 1
            self.controls()
            return

        self.update_enemies()

        if not self.game_ended:
            self.controls()
            inside = False
            for e, i in enumerate(self.road_squares):
                if self.is_player_inside_squares(self.main_car.pos, i):
                    if e not in self.visited:
                        self.visited.append(e)
                    if e == 17:
                        self.check_lap()
                    inside = True

                    break
            if not inside:
                self.main_car.on_road = False
            else:
                self.main_car.on_road = True
        else:
            keys = pg.key.get_pressed()
            if keys[pg.K_SPACE]:
                pg.mixer.music.fadeout(1)
                self.scene_manager.switch_scene('MainMenuScene')
            self.main_car.hit_brake()
            if not self.end_screen:
                end_time = time.time() - self.paused_time
                self.times['You'] = end_time - self.start_time
                self.add_object(LeaderBoard(self, self.times))
                self.speedometer.hidden = True
                self.lap.hidden = True
                self.end_screen = True

        self.camera.position += ((self.main_car.pos - (self.main_car.forward * 3)) - self.camera.position) * 0.2
        self.camera.position.y = self.main_car.pos.y + 2
        self.camera.forward = glm.vec3(self.main_car.forward)
        self.camera.up = glm.vec3(self.main_car.up)
        self.camera.side = glm.vec3(self.main_car.side)

        self.main_car.update_pos()

    def update_enemies(self):

        for e, c in self.enemies.items():
            if self.tick in self.scripts[e]:
                if 0 in self.scripts[e][self.tick]:
                    self.enemy_controls[e][0] = not self.enemy_controls[e][0]
                if 1 in self.scripts[e][self.tick]:
                    self.enemy_controls[e][1] = not self.enemy_controls[e][1]
                if 2 in self.scripts[e][self.tick]:
                    self.enemy_controls[e][2] = not self.enemy_controls[e][2]
                if 3 in self.scripts[e][self.tick]:
                    self.enemy_controls[e][3] = not self.enemy_controls[e][3]
            if self.enemy_controls[e][0]:
                c.accelerate()
            if self.enemy_controls[e][1]:
                c.hit_brake()
            if self.enemy_controls[e][2]:
                c.rotate(True)
            if self.enemy_controls[e][3]:
                c.rotate(False)
            c.update_pos()


    def pause_scene(self):
        self.paused_clock = time.time()
        self.paused = True
        self.pause.hidden = False
        self.speedometer.hidden = True
        self.lap.hidden = True
        pg.mixer.music.pause()

    def unpause_scene(self):
        self.paused_time += time.time() - self.paused_clock
        self.paused = False
        self.pause.hidden = True
        self.speedometer.hidden = False
        self.lap.hidden = False
        pg.mixer.music.unpause()


    def controls(self):
        keys = pg.key.get_pressed()
        if not self.paused:
            if keys[pg.K_w]:
                self.main_car.accelerate()
            if keys[pg.K_s]:
                self.main_car.hit_brake()
            if keys[pg.K_a]:
                self.main_car.rotate(True)
            if keys[pg.K_d]:
                self.main_car.rotate(False)
            if keys[pg.K_ESCAPE]:
                self.pause_scene()
        else:
            if keys[pg.K_a]:
                self.pause.select(True)
            if keys[pg.K_d]:
                self.pause.select(False)
            if keys[pg.K_SPACE]:
                if self.pause.selected:
                    self.unpause_scene()
                else:
                    self.scene_manager.switch_scene('MainMenuScene')


    def check_lap(self):
        if len(self.visited) >= len(self.road_squares) * 80 / 100:
            self.lap.lap += 1
            self.visited.clear()
            if self.lap.lap == 3:
                self.game_ended = True

    @abstractmethod
    def is_player_inside_squares(self, player_pos, transformed_corners):
        corner1, corner2, corner3, corner4 = transformed_corners
        if (
                min(corner1.x, corner2.x, corner3.x, corner4.x) <= player_pos.x <= max(corner1.x, corner2.x, corner3.x,
                                                                                       corner4.x)
                and min(corner1.z, corner2.z, corner3.z, corner4.z) <= player_pos.z <= max(corner1.z, corner2.z,
                                                                                           corner3.z, corner4.z)
        ):
            return True
        return False


class RecordScene(BasicScene):
    def __init__(self, scene_manager):
        super().__init__(scene_manager)

    def load(self):
        self.car_pos = random.randint(1, 3)
        self.main_car = Vehicle(self, 1, pos=CAR_POSITIONS[self.car_pos], rot=(0, 1.05, 0))
        self.speedometer = Speedometer(self, self.main_car)
        self.lap = Lap(self)
        self.ss = StartSequence(self)
        self.game_starting = True
        self.free_cam = False
        self.game_ended = False
        self.movements = {}
        self.times = {}
        self.road_squares = []
        self.visited = []
        self.replays = os.listdir('replays/')
        self.keys = [False, False, False, False]
        self.recorded = False

        self.camera.position = glm.vec3(self.main_car.pos + (self.main_car.forward * 30))
        self.camera.position.y += 15

        self.camera.yaw = 210
        self.camera.pitch = -50
        self.camera.update_rotation()
        self.camera.update()
        self.skybox = Skybox(self)

        self.add_object(
            ExtendedBaseModel(self, vao_name='cube', tex_id='grass', pos=(0, -0.01, 0), scale=(300, 0.001, 300),
                              tiling=200))
        self.add_object(ExtendedBaseModel(self, vao_name='track', tex_id='asphalt', pos=(0, 0.1, 0), tiling=10))
        self.add_object(ExtendedBaseModel(self, vao_name='markings', tex_id='markings'))
        self.add_object(ExtendedBaseModel(self, vao_name='rail', tex_id='rail'))
        self.add_object(ExtendedBaseModel(self, vao_name='finish', tex_id='finish'))
        self.add_object(ExtendedBaseModel(self, vao_name='tree', tex_id='tree'))
        self.add_object(ExtendedBaseModel(self, vao_name='rock', tex_id='rock'))

        self.add_object(self.main_car)
        self.add_object(self.speedometer)
        self.add_object(self.lap)
        self.add_object(self.ss)
        # pg.mixer.music.load("audio/running_downwards_(bmw's_theme).mp3")

        self.start_time = time.time()

        self.speedometer.hidden = True
        self.lap.hidden = True

        objs = pywavefront.Wavefront(f'objects/track.obj', cache=True, parse=True)
        marks = []

        with open('objects/Track_path.txt', 'r') as file:
            for line in file:
                if line.startswith('v'):
                    _, x, y, z = line.split()
                    point = [float(x), float(y), float(z)]
                    marks.append(glm.vec3(point))

        with open(f'replays/record_{len(self.replays)}', 'a') as file:
            file.write(f"1\n{self.car_pos}\n")

        for i in range(len(marks) - 1):
            corner1 = glm.vec3(-1, 0, -1)
            corner2 = glm.vec3(-1, 0, 1)
            corner3 = glm.vec3(1, 0, -1)
            corner4 = glm.vec3(1, 0, 1)

            m_model = glm.mat4(1.0)

            translation_matrix = glm.translate(glm.mat4(1.0), marks[i])
            m_model = m_model @ translation_matrix

            direction = glm.normalize(marks[i + 1] - marks[i])
            up_vector = glm.vec3(0, 1, 0)
            right_vector = glm.cross(up_vector, direction)
            rotation_matrix = glm.mat4(
                glm.vec4(right_vector, 0),
                glm.vec4(up_vector, 0),
                glm.vec4(-direction, 0),
                glm.vec4(0, 0, 0, 1)
            )
            m_model = m_model @ rotation_matrix

            scaling_matrix = glm.scale(glm.mat4(1.0), glm.vec3(5, 1, 3))
            m_model = m_model @ scaling_matrix

            corner1 = glm.vec3(m_model * glm.vec4(corner1, 1))
            corner2 = glm.vec3(m_model * glm.vec4(corner2, 1))
            corner3 = glm.vec3(m_model * glm.vec4(corner3, 1))
            corner4 = glm.vec3(m_model * glm.vec4(corner4, 1))
            self.road_squares.append([corner1, corner2, corner3, corner4])

        self.starting_sequence()

    def starting_sequence(self):
        if self.tick % 82 == 0:
            self.ss.update_state()

        if self.tick < 150:
            self.camera.position += ((self.main_car.pos + self.main_car.forward * 2) - self.camera.position) * 0.02
            self.camera.pitch += (0 - self.camera.pitch) * 0.02
            self.camera.update_rotation()
        if self.tick == 160:
            self.camera.position = self.main_car.pos + self.main_car.forward * 2.5 + self.main_car.side * 1 + self.main_car.up * 0.5
        if 160 < self.tick < 300:
            self.camera.position += self.camera.side / 80

        if self.tick > 300:
            self.camera.position = self.main_car.pos - self.main_car.forward * 3
            self.camera.position.y = self.main_car.pos.y + 2
            self.camera.forward = glm.vec3(self.main_car.forward)
            self.camera.up = glm.vec3(self.main_car.up)
            self.camera.side = glm.vec3(self.main_car.side)

        if self.tick > 350:
            self.game_starting = False
            self.speedometer.hidden = False
            self.lap.hidden = False
            self.ss.hidden = True

    def custom_update(self):

        if self.game_starting:
            self.starting_sequence()
            return

        if not self.game_ended:
            self.controls()

            inside = False
            for e, i in enumerate(self.road_squares):
                if self.is_player_inside_squares(self.main_car.pos, i):
                    if e not in self.visited:
                        self.visited.append(e)
                    if e == 17:
                        self.check_lap()
                    inside = True

                    break
            if not inside:
                self.main_car.on_road = False
            else:
                self.main_car.on_road = True
        else:
            end_time = time.time()
            time_total = end_time - self.start_time
            self.times['You'] = time_total
            self.add_object(LeaderBoard(self, self.times))
            self.main_car.hit_brake()
            self.speedometer.hidden = True
            self.lap.hidden = True
            if not self.recorded:
                with open(f'replays/record_{len(self.replays)}', 'a') as file:
                    file.write(f"* {time_total}")
                self.recorded = True

        if not self.free_cam:
            self.camera.position += ((self.main_car.pos - (self.main_car.forward * 3)) - self.camera.position) * 0.2
            self.camera.position.y = self.main_car.pos.y + 2
            self.camera.forward = glm.vec3(self.main_car.forward)
            self.camera.up = glm.vec3(self.main_car.up)
            self.camera.side = glm.vec3(self.main_car.side)

        self.main_car.update_pos()

    def controls(self):
        keys = pg.key.get_pressed()
        if keys[pg.K_w]:
            self.main_car.accelerate()
            if not self.keys[0]:
                self.keys[0] = not self.keys[0]
                self.record_action('0')
        elif self.keys[0]:
            self.keys[0] = not self.keys[0]
            self.record_action('0')

        if keys[pg.K_s]:
            self.main_car.hit_brake()
            if not self.keys[1]:
                self.keys[1] = not self.keys[1]
                self.record_action('1')
        elif self.keys[1]:
            self.keys[1] = not self.keys[1]
            self.record_action('1')

        if keys[pg.K_a]:
            self.main_car.rotate(True)
            if not self.keys[2]:
                self.keys[2] = not self.keys[2]
                self.record_action('2')
        elif self.keys[2]:
            self.keys[2] = not self.keys[2]
            self.record_action('2')

        if keys[pg.K_d]:
            self.main_car.rotate(False)
            if not self.keys[3]:
                self.keys[3] = not self.keys[3]
                self.record_action('3')
        elif self.keys[3]:
            self.keys[3] = not self.keys[3]
            self.record_action('3')

        if keys[pg.K_o]:
            self.free_cam = not self.free_cam
            self.speedometer.hidden = not self.speedometer.hidden
            self.lap.hidden = not self.lap.hidden

        velocity = SPEED * self.app.delta_time
        velocity_r = TURN_SPEED * self.app.delta_time

        if keys[pg.K_RIGHT]:
            self.camera.yaw += 10 * velocity_r
            self.camera.update_rotation()
        if keys[pg.K_LEFT]:
            self.camera.yaw -= 10 * velocity_r
            self.camera.update_rotation()
        if keys[pg.K_UP]:
            self.camera.pitch += 10 * velocity_r
            self.camera.update_rotation()
        if keys[pg.K_DOWN]:
            self.camera.pitch -= 10 * velocity_r
            self.camera.update_rotation()

        if self.free_cam:
            if keys[pg.K_u]:
                self.camera.position += self.camera.forward * velocity
            if keys[pg.K_j]:
                self.camera.position -= self.camera.forward * velocity
            if keys[pg.K_h]:
                self.camera.position -= self.camera.side * velocity
            if keys[pg.K_k]:
                self.camera.position += self.camera.side * velocity

    def check_lap(self):
        if len(self.visited) >= len(self.road_squares) * 80 / 100:
            self.lap.lap += 1
            self.visited.clear()
            if self.lap.lap == 3:
                self.game_ended = True

    @staticmethod
    def is_player_inside_squares(player_pos, transformed_corners):
        corner1, corner2, corner3, corner4 = transformed_corners
        if (
                min(corner1.x, corner2.x, corner3.x, corner4.x) <= player_pos.x <= max(corner1.x, corner2.x, corner3.x,
                                                                                       corner4.x)
                and min(corner1.z, corner2.z, corner3.z, corner4.z) <= player_pos.z <= max(corner1.z, corner2.z,
                                                                                           corner3.z, corner4.z)
        ):
            return True
        return False

    def record_action(self, action):
        with open(f'replays/record_{len(self.replays)}', 'a') as file:
            file.write(f"{self.tick} {action}\n")


class MainMenuScene(BasicScene):
    def __init__(self, scene_manager):
        super().__init__(scene_manager)

    def load(self):
        self.cam_speed = 0.1
        self.camera.position = glm.vec3(0, 15, 0)
        self.camera.yaw = -90
        self.camera.pitch = -35
        self.camera.update()
        self.in_options = False

        self.add_object(
            ExtendedBaseModel(self, vao_name='cube', tex_id='grass', pos=(0, -0.01, 0), scale=(300, 0.001, 300),
                              tiling=200))
        self.add_object(ExtendedBaseModel(self, vao_name='track', tex_id='asphalt', pos=(0, 0.1, 0), tiling=10))
        self.add_object(ExtendedBaseModel(self, vao_name='markings', tex_id='markings'))
        self.add_object(ExtendedBaseModel(self, vao_name='rail', tex_id='rail'))
        self.add_object(ExtendedBaseModel(self, vao_name='finish', tex_id='finish'))
        self.add_object(ExtendedBaseModel(self, vao_name='tree', tex_id='tree'))
        self.add_object(ExtendedBaseModel(self, vao_name='rock', tex_id='rock'))
        self.skybox = Skybox(self)

        pg.mixer.music.load("audio/calm_before_the_storm_(main_menu).mp3")

        pg.mixer.music.play(loops=10)
        pg.mixer.music.set_volume(
            int(config.global_variables['music_volumes'][int(config.global_variables['music_volume'][0])]) / 100)
        self.main_menu_obj = MainMenu(self, self.scene_manager)
        self.options_menu_obj = OptionsMenu(self, self.scene_manager)
        self.add_object(self.main_menu_obj)
        self.add_object(self.options_menu_obj)
        self.options_menu_obj.hidden = True

        if config.global_variables['restarting'][0] == '1':
            self.scene_manager.switch_scene('OptionsScene')
            config.global_variables['restarting'][0] = '0'


    def controls(self):
        keys = pg.key.get_pressed()
        if not self.in_options:
            if keys[pg.K_w]:
                self.main_menu_obj.move(True)
            if keys[pg.K_s]:
                self.main_menu_obj.move(False)
            if keys[pg.K_SPACE]:
                self.main_menu_obj.select()

        else:
            if keys[pg.K_w]:
                self.options_menu_obj.move(True)
            if keys[pg.K_s]:
                self.options_menu_obj.move(False)
            if keys[pg.K_a]:
                self.options_menu_obj.switch(True)
            if keys[pg.K_d]:
                self.options_menu_obj.switch(False)
            if keys[pg.K_SPACE]:
                self.options_menu_obj.select()

    def custom_update(self):
        self.camera.yaw -= self.cam_speed
        self.camera.position += self.camera.side * self.cam_speed
        self.camera.update_rotation()
        self.camera.update()
        self.controls()
        self.main_menu_obj.update()
        self.options_menu_obj.update()

    def swap_options(self):
        self.in_options = not self.in_options
        self.main_menu_obj.hidden = not self.main_menu_obj.hidden
        self.options_menu_obj.hidden = not self.options_menu_obj.hidden
        self.reset_menus()

    def reset_menus(self):
        self.main_menu_obj.reset()
        self.options_menu_obj.reset()


class OptionsScene(BasicScene):
    def __init__(self, scene_manager):
        super().__init__(scene_manager)

    def load(self):
        self.scene_manager.scenes['MainMenuScene'].swap_options()
        self.scene_manager.resume_scene('MainMenuScene')


class GarageScene(BasicScene):
    def __init__(self, scene_manager):
        super().__init__(scene_manager)

    def load(self):
        self.car_selection = CarSelection(self, self.scene_manager)
        self.camera.position = glm.vec3(1, 1, -4.3)

        self.camera.yaw = 90
        self.camera.pitch = -10
        self.camera.update_rotation()
        self.camera.update()
        self.light.ambient = glm.vec3(0.3)
        self.light.position = glm.vec3(2, 3, -5)
        self.light.direction = self.car_selection.current_car.pos
        self.light.update()

        self.add_object(
            ExtendedBaseModelShadowless(self, 'podium', 'metal', tiling=1000, scale=(0.4, 0.1, 0.4), pos=(1, 0, -1)))
        self.add_object(self.car_selection)

    def custom_update(self):
        self.controls()
        self.car_selection.update()

    def controls(self):
        keys = pg.key.get_pressed()
        if keys[pg.K_w]:
            self.car_selection.switch_model(True)
        if keys[pg.K_s]:
            self.car_selection.switch_model(False)
        if keys[pg.K_a]:
            self.car_selection.switch_skin(True)
        if keys[pg.K_d]:
            self.car_selection.switch_skin(False)
        if keys[pg.K_SPACE]:
            self.car_selection.select()
        if keys[pg.K_ESCAPE]:
            self.scene_manager.scenes['MainMenuScene'].reset_menus()
            self.scene_manager.resume_scene('MainMenuScene')


class ExitScene(BasicScene):
    def __init__(self, scene_manager):
        super().__init__(scene_manager)

    def load(self):
        self.scene_manager.app.quit()


class TestScene(BasicScene):
    def __init__(self, scene_manager):
        super().__init__(scene_manager)

    def load(self):
        self.ss = StartSequence(self)
        self.add_object(self.ss)

    def custom_update(self):
        if self.tick % 50 == 0:
            self.ss.update_state()
        if self.tick == 500:
            self.scene_manager.switch_scene('RaceScene')
