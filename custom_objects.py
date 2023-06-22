import glm

import config
from model import ExtendedBaseModelBody, ExtendedBaseModelWheel, BasicImage, ImagePlusModel
from text_handler import generate_text_texture
from vbo import RectangleVBO
import pygame as pg
from collections import OrderedDict


class VehicleModel:
    def __init__(self, scene, vao_car_id, pos=(0, 0, 0), rot=(0, 0, 0), variant='1', scale=(1.2, 1.2, 1.2)):
        self.scene = scene
        self.app = scene.app
        self.id = vao_car_id
        self.name = config.global_variables['car_types'][self.id]
        self.pos = glm.vec3(pos)
        self.rotation = glm.vec3(rot)
        self.wheel_rotation = 0
        self.variant = variant
        self.body = ExtendedBaseModelBody(scene, self.name, self.name + '_' + self.variant, pos, rot,
                                          scale=scale, tiling=1)
        self.front_tires = ExtendedBaseModelWheel(scene, self.name + '_front', self.name + '_wheels', pos=(0, 0, 0),
                                                  rot=(0, 0, 0), scale=(1, 1, 1), car=self, tiling=1)
        self.back_tires = ExtendedBaseModelWheel(scene, self.name + '_back', self.name + '_wheels', pos=(0, 0, 0),
                                                 rot=(0, 0, 0), scale=(1, 1, 1), car=self, tiling=1)

    def render_shadow(self):
        self.body.render_shadow()

    def render(self):
        self.body.render()
        self.front_tires.render()
        self.back_tires.render()

    def move_wheel_rotation(self, rot):
        self.wheel_rotation = self.wheel_rotation + rot

    def update_rotation(self):
        rotation_w = glm.vec3(self.rotation)
        rotation_w.x += self.wheel_rotation
        self.body.rotation = self.rotation
        self.front_tires.rotation = rotation_w
        self.back_tires.rotation = rotation_w
        self.body.m_model = self.body.get_model_matrix()
        self.front_tires.m_model = self.front_tires.get_model_matrix()
        self.back_tires.m_model = self.back_tires.get_model_matrix()

    def set_pos(self, pos):
        self.pos = glm.vec3(pos)
        self.body.pos = pos
        self.front_tires.pos = pos
        self.back_tires.pos = pos


class Speedometer:
    def __init__(self, scene, car):
        self.scene = scene
        self.app = scene.app
        self.value = 250
        self.car = car
        self.hidden = False

        initial_size = [640, 360]
        current_size = self.app.WIN_SIZE

        scaling_factor = current_size[0] / initial_size[0]

        rec = RectangleVBO(self.app.ctx, size=(80 * scaling_factor, 80 * scaling_factor))
        speedometer_gadge_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                                          [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        rec = RectangleVBO(self.app.ctx, size=(120 * scaling_factor, 120 * scaling_factor))
        speedometer_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                                    [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        self.speedometer_gadge = ImagePlusModel(self, speedometer_gadge_vao, 'speedometer_gadge',
                                                pos=(51 * scaling_factor, 31 * scaling_factor))

        self.speedometer = ImagePlusModel(self, speedometer_vao, 'speedometer',
                                          pos=(65 * scaling_factor, 60 * scaling_factor))

    def render(self):
        if self.hidden:
            return
        self.set_velocity()
        self.speedometer_gadge.render()
        self.speedometer.render()

    def set_velocity(self):
        self.speedometer_gadge.rotation = glm.vec2(self.car.velocity / self.value - 2.2, 0)
        self.speedometer_gadge.set_heat(self.car.velocity / (self.value * 10))
        self.speedometer.set_heat(self.car.velocity / (self.value * 10))
        if self.car.velocity / self.value > 3:
            self.speedometer_gadge.shake_power = 4
            self.speedometer.shake_power = 2
        else:
            self.speedometer_gadge.shake_power = 0
            self.speedometer.shake_power = 0


class Lap:
    def __init__(self, scene):
        self.scene = scene
        self.app = scene.app
        self.lap = 0
        self.hidden = False

        initial_size = [640, 360]
        current_size = self.app.WIN_SIZE

        scaling_factor = current_size[0] / initial_size[0]

        rec = RectangleVBO(self.app.ctx, size=(130 * scaling_factor, 25 * scaling_factor))
        lap1n2_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['image'],
                                               [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        rec = RectangleVBO(self.app.ctx, size=(150 * scaling_factor, 22 * scaling_factor))
        final_lap_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['image'],
                                                  [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        self.lap1 = BasicImage(self, lap1n2_vao, 'lap_1',
                               pos=(70 * scaling_factor, 345 * scaling_factor))

        self.lap2 = BasicImage(self, lap1n2_vao, 'lap_2',
                               pos=(70 * scaling_factor, 345 * scaling_factor))

        self.lap3 = BasicImage(self, final_lap_vao, 'final_lap',
                               pos=(75 * scaling_factor, 345 * scaling_factor))

    def render(self):
        if self.hidden:
            return
        if self.lap == 0:
            self.lap1.render()
        elif self.lap == 1:
            self.lap2.render()
        else:
            self.lap3.render()


class LeaderBoard:
    def __init__(self, scene, times):
        self.scene = scene
        self.app = scene.app
        self.times = self.sort_dict_by_time(times)
        self.hidden = False
        self.tick = 0

        initial_size = [640, 360]
        current_size = self.app.WIN_SIZE
        scaling_factor = current_size[0] / initial_size[0]
        self.scaling_factor = scaling_factor

        font = pg.font.SysFont('HighSwift-Regular', int(24 * scaling_factor))
        font_small = pg.font.SysFont('HighSwift-Regular', int(16 * scaling_factor))

        dark_rec = RectangleVBO(self.app.ctx, size=self.app.WIN_SIZE)
        text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                             [(dark_rec.vbo, dark_rec.format, *dark_rec.attrib)], skip_errors=True)
        self.darker_obj = ImagePlusModel(self, text_vao, 'darkened',
                                         pos=(self.app.WIN_SIZE[0] / 2, self.app.WIN_SIZE[1] / 2), opacity=0.6)

        scores_text, size = generate_text_texture(self.app.ctx, "Leaderboard", font, color=(255, 140, 0))
        rec = RectangleVBO(self.app.ctx, size=size)
        big_text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['image'],
                                                 [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        self.scores_text_obj = BasicImage(self, big_text_vao, 'None', pos=(320 * scaling_factor, 340 * scaling_factor),
                                          texture=scores_text)

        scores_text, size = generate_text_texture(self.app.ctx, f"Press SPACE to continue", font_small,
                                                  color=(255, 255, 0))
        rec = RectangleVBO(self.app.ctx, size=size)
        big_text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['image'],
                                                 [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)
        self.press_enter_text_obj = BasicImage(self, big_text_vao, 'None',
                                               pos=(340 * scaling_factor, -200 * scaling_factor),
                                               texture=scores_text)

        small_size = 200 * scaling_factor, 30 * scaling_factor
        rec = RectangleVBO(self.app.ctx, size=small_size)
        small_text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['image'],
                                                   [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        self.scores_names_text_objs = {}
        self.scores_times_text_objs = {}
        pos = 250
        for player, (time, index) in self.times.items():
            if player == 'You':
                color = (255, 255, 255)
            else:
                color = (255, 255, 0)
            scores_text, _ = generate_text_texture(self.app.ctx, f"{index}. {player}", font_small,
                                                   color=color, size=small_size)
            self.scores_names_text_objs[index] = BasicImage(self, small_text_vao, 'None',
                                                            pos=(-1000 * scaling_factor, pos * scaling_factor),
                                                            texture=scores_text)
            scores_text, _ = generate_text_texture(self.app.ctx, f"{round(time, 3)}", font_small,
                                                   color=color, size=small_size)
            self.scores_times_text_objs[index] = BasicImage(self, small_text_vao, 'None',
                                                            pos=(-1000 * scaling_factor, pos * scaling_factor),
                                                            texture=scores_text)
            pos -= 30

    def update(self):
        self.tick += 1
        for index, image in self.scores_names_text_objs.items():
            if index <= self.tick / 40:
                image.pos.x += (150 * self.scaling_factor - image.pos.x) * 0.1
        for index, image in self.scores_times_text_objs.items():
            if index <= self.tick / 40:
                image.pos.x += (450 * self.scaling_factor - image.pos.x) * 0.1
        if self.tick > 200:
            self.press_enter_text_obj.pos.y += (10 * self.scaling_factor - self.press_enter_text_obj.pos.y) * 0.1

    def render(self):

        if self.hidden:
            return
        self.update()
        self.scores_text_obj.render()
        for k, i in self.scores_names_text_objs.items():
            i.render()
        for k, i in self.scores_times_text_objs.items():
            i.render()
        self.press_enter_text_obj.render()
        self.darker_obj.render()

    @staticmethod
    def sort_dict_by_time(times):
        sorted_dict = {k: v for k, v in sorted(times.items(), key=lambda item: item[1])}
        indexed_dict = {k: (v, i + 1) for i, (k, v) in enumerate(sorted_dict.items())}
        return indexed_dict


class StartSequence:
    def __init__(self, scene):
        self.scene = scene
        self.app = scene.app
        self.hidden = False
        self.state = 0

        initial_size = [640, 360]
        current_size = self.app.WIN_SIZE
        scaling_factor = current_size[0] / initial_size[0]

        font = pg.font.SysFont('HighSwift-Regular', int(70 * scaling_factor))
        font2 = pg.font.SysFont('HighSwift-Regular', int(60 * scaling_factor))

        color = (255, 140, 0)

        scores_text, size = generate_text_texture(self.app.ctx, '3', font,
                                                  color=color)

        rec = RectangleVBO(self.app.ctx, size=size)
        small_text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['image'],
                                                   [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        self.three_text_obj = BasicImage(self, small_text_vao, 'None', pos=(320 * scaling_factor, 180 * scaling_factor),
                                         texture=scores_text)

        scores_text, _ = generate_text_texture(self.app.ctx, '2', font, color=color)

        self.two_text_obj = BasicImage(self, small_text_vao, 'None', pos=(320 * scaling_factor, 180 * scaling_factor),
                                       texture=scores_text)
        scores_text, _ = generate_text_texture(self.app.ctx, '1', font, color=color)

        self.one_text_obj = BasicImage(self, small_text_vao, 'None', pos=(320 * scaling_factor, 180 * scaling_factor),
                                       texture=scores_text)

        scores_text, size = generate_text_texture(self.app.ctx, 'READY?', font2, color=color)
        rec = RectangleVBO(self.app.ctx, size=size)
        big_text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                                 [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        self.ready_text_obj = ImagePlusModel(self, big_text_vao, 'None',
                                             pos=(320 * scaling_factor, 180 * scaling_factor),
                                             texture=scores_text)

        scores_text, size = generate_text_texture(self.app.ctx, 'GO!', font2, color=color)
        rec = RectangleVBO(self.app.ctx, size=size)
        big_text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                                 [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        self.go_text_obj = ImagePlusModel(self, big_text_vao, 'None', pos=(320 * scaling_factor, 180 * scaling_factor),
                                          texture=scores_text)
        self.go_text_obj.shake_power = 7

    def update(self):
        pass

    def render(self):
        if self.hidden:
            return
        if self.state == 0:
            return
        elif self.state == 1:
            self.ready_text_obj.render()
        elif self.state == 2:
            self.three_text_obj.render()
        elif self.state == 3:
            self.two_text_obj.render()
        elif self.state == 4:
            self.one_text_obj.render()
        elif self.state == 5:
            self.go_text_obj.render()
        else:
            return

    def update_state(self):
        self.state += 1


class MainMenu:
    def __init__(self, scene, scene_manager):
        self.scene = scene
        self.scene_manager = scene_manager
        self.app = scene.app
        self.button_functions = {'Start Game': 'RaceScene', 'Choose Car': 'GarageScene', 'Options': 'OptionsScene',
                                 'Exit': 'ExitScene'}
        self.button_objs = []
        self.tick = 0
        self.selected = 0
        self.cooldown = 0
        self.hidden = False

        initial_size = [640, 360]
        current_size = self.app.WIN_SIZE
        scaling_factor = current_size[0] / initial_size[0]
        self.scaling_factor = scaling_factor

        dark_rec = RectangleVBO(self.app.ctx, size=self.app.WIN_SIZE)
        dark_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                             [(dark_rec.vbo, dark_rec.format, *dark_rec.attrib)], skip_errors=True)
        self.darker_obj = ImagePlusModel(self, dark_vao, 'darkened',
                                         pos=(self.app.WIN_SIZE[0] / 2, self.app.WIN_SIZE[1] / 2), opacity=0.6)

        rec = RectangleVBO(self.app.ctx, size=(300 * scaling_factor, 40 * scaling_factor))
        logo_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                             [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)
        self.nbu_logo_obj = ImagePlusModel(self, logo_vao, 'nbu_racer_logo',
                                           pos=(self.app.WIN_SIZE[0] / 2, 320 * scaling_factor))

        rec = RectangleVBO(self.app.ctx, size=(self.app.WIN_SIZE[0] * scaling_factor, 50 * scaling_factor))
        bg_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                           [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)
        self.red_background_obj = ImagePlusModel(self, bg_vao, 'red_background',
                                                 pos=(self.app.WIN_SIZE[0] / 2, 320 * scaling_factor))

        rec = RectangleVBO(self.app.ctx, size=(self.app.WIN_SIZE[0] * scaling_factor, 40 * scaling_factor))
        text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                             [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)
        self.orange_background_obj = ImagePlusModel(self, text_vao, 'orange_background',
                                                    pos=(self.app.WIN_SIZE[0] / 2, 3000 * scaling_factor), opacity=0.6)

        font = pg.font.SysFont('HighSwift-Regular', int(21 * scaling_factor))
        small_size = 400 * scaling_factor, 100 * scaling_factor
        rec = RectangleVBO(self.app.ctx, size=small_size)
        small_text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['image'],
                                                   [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        pos = 200
        for index, _ in self.button_functions.items():
            color = (255, 255, 0)
            scores_text, _ = generate_text_texture(self.app.ctx, index, font,
                                                   color=color, size=small_size)
            self.button_objs.append([BasicImage(self, small_text_vao, 'None',
                                                pos=(-1000 * scaling_factor, pos * scaling_factor),
                                                texture=scores_text), index])
            pos -= 50

    def update(self):
        self.tick += 1
        if self.cooldown > 0:
            self.cooldown -= 1
        for index in range(len(self.button_objs)):
            if index <= self.tick / 20:
                self.button_objs[index][0].pos.x += (250 * self.scaling_factor - self.button_objs[index][0].pos.x) * 0.1

        self.orange_background_obj.pos.y += (self.button_objs[self.selected][0].pos.y + (
                38 * self.scaling_factor) - self.orange_background_obj.pos.y) * 0.2

    def move(self, dir):
        if self.cooldown > 0:
            return
        if dir:
            self.selected = (self.selected - 1) % len(self.button_objs)
        else:
            self.selected = (self.selected + 1) % len(self.button_objs)
        self.cooldown = 20

    def select(self):
        if self.tick > 100:
            self.scene_manager.switch_scene(self.button_functions[self.button_objs[self.selected][1]])

    def render(self):
        if not self.hidden:
            self.nbu_logo_obj.render()
            self.red_background_obj.render()
            for i in self.button_objs:
                i[0].render()
            self.orange_background_obj.render()
            self.darker_obj.render()

    def reset(self):
        self.tick = 0
        for i in self.button_objs:
            i[0].pos.x = -1000


class OptionsMenu:
    def __init__(self, scene, scene_manager):
        self.scene = scene
        self.scene_manager = scene_manager
        self.app = scene.app
        self.button_objs = OrderedDict()
        self.button_keys = None
        self.value_objs = {}
        self.tick = 0
        self.selected = 0
        self.cooldown = 0
        self.hidden = False
        self.button_functions = {
            'Resolution': lambda: (config.global_variables.update({'resolution': [self.value_objs['Resolution'].selected]}),config.global_variables.update({'restarting': ['1']}), self.app.quit()),
            'Fov': lambda: (config.global_variables.update({'fov': [self.value_objs['Fov'].selected]})),
            'Music': lambda: (config.global_variables.update({'music_volume': [self.value_objs['Music'].selected]}),pg.mixer.music.set_volume(
            int(config.global_variables['music_volumes'][int(config.global_variables['music_volume'][0])])/100)),
        'Back': None
        }
        self.options_selected = {'Resolution':int(config.global_variables['resolution'][0]),
                                 'Fov':int(config.global_variables['fov'][0]),
                                 'Music':int(config.global_variables['music_volume'][0])}
        self.options = {'Resolution':config.global_variables['resolutions'],
                        'Fov':config.global_variables['fovs'],
                        'Music':config.global_variables['music_volumes']}
        initial_size = [640, 360]
        current_size = self.app.WIN_SIZE
        scaling_factor = current_size[0] / initial_size[0]
        self.scaling_factor = scaling_factor

        dark_rec = RectangleVBO(self.app.ctx, size=self.app.WIN_SIZE)
        dark_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                             [(dark_rec.vbo, dark_rec.format, *dark_rec.attrib)], skip_errors=True)
        self.darker_obj = ImagePlusModel(self, dark_vao, 'darkened',
                                         pos=(self.app.WIN_SIZE[0] / 2, self.app.WIN_SIZE[1] / 2), opacity=0.6)
        font = pg.font.SysFont('HighSwift-Regular', int(34 * scaling_factor))

        options_text, size = generate_text_texture(self.app.ctx, 'Options', font,
                                                   color=(255, 170, 0))
        rec = RectangleVBO(self.app.ctx, size=size)

        options_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['image'],
                                                [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)
        self.options_text_obj = BasicImage(self, options_vao, 'None',
                                           pos=(200 * scaling_factor, 320 * scaling_factor),
                                           texture=options_text)

        rec = RectangleVBO(self.app.ctx, size=(self.app.WIN_SIZE[0] * scaling_factor, 40 * scaling_factor))
        bg_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                           [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)
        self.red_background_obj = ImagePlusModel(self, bg_vao, 'red_background',
                                                 pos=(self.app.WIN_SIZE[0] / 2, 320 * scaling_factor))

        rec = RectangleVBO(self.app.ctx, size=(self.app.WIN_SIZE[0] * scaling_factor, 40 * scaling_factor))
        text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                             [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)
        self.orange_background_obj = ImagePlusModel(self, text_vao, 'orange_background',
                                                    pos=(self.app.WIN_SIZE[0] / 2, 3000 * scaling_factor), opacity=0.6)

        font = pg.font.SysFont('HighSwift-Regular', int(21 * scaling_factor))
        small_size = 400 * scaling_factor, 100 * scaling_factor
        rec = RectangleVBO(self.app.ctx, size=small_size)
        small_text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['image'],
                                                   [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        pos = 200
        for index, _ in self.button_functions.items():

            color = (255, 255, 0)
            scores_text, _ = generate_text_texture(self.app.ctx, index, font,
                                                   color=color, size=small_size)
            self.button_objs[index] = BasicImage(self, small_text_vao, 'None',
                                                 pos=(-1000 * scaling_factor, pos * scaling_factor),
                                                 texture=scores_text)
            if index == 'Back':
                break
            self.value_objs[index] = SelectedObject(self, small_text_vao, texts=self.options[index], selected=self.options_selected[index],
                                                    pos=(1000 * scaling_factor, pos * scaling_factor), size=small_size,
                                                    color=color, font=font)
            pos -= 50
        self.button_keys = list(self.button_objs.keys())

    def update(self):
        self.tick += 1
        if self.cooldown > 0:
            self.cooldown -= 1
        for index, (name, item) in enumerate(self.button_objs.items()):
            if index <= self.tick / 20:
                item.pos.x += (250 * self.scaling_factor - item.pos.x) * 0.1
        for index, (name, item) in enumerate(self.value_objs.items()):
            if index <= self.tick / 20:
                item.text_obj.pos.x += (550 * self.scaling_factor - item.text_obj.pos.x) * 0.1

        self.orange_background_obj.pos.y += (self.button_objs[self.button_keys[self.selected]].pos.y + (
                38 * self.scaling_factor) - self.orange_background_obj.pos.y) * 0.2

    def move(self, dir):
        if self.cooldown > 0:
            return
        if dir:
            self.selected = (self.selected - 1) % len(self.button_objs)
        else:
            self.selected = (self.selected + 1) % len(self.button_objs)
        self.cooldown = 20

    def select(self):
        if self.tick > 100:
            if self.button_keys[self.selected] == 'Back':
                self.scene_manager.switch_scene('OptionsScene')

    def switch(self,dir):
        if self.cooldown > 0:
            return
        if self.button_keys[self.selected] == 'Back':
            return
        self.value_objs[self.button_keys[self.selected]].move(dir)
        self.button_functions[self.button_keys[self.selected]]()
        self.cooldown = 20

    def render(self):
        if not self.hidden:
            self.options_text_obj.render()
            self.red_background_obj.render()
            for _, i in self.button_objs.items():
                i.render()
            for _, i in self.value_objs.items():
                i.render()
            self.orange_background_obj.render()
            self.darker_obj.render()

    def reset(self):
        self.tick = 0
        for _, i in self.button_objs.items():
            i.pos.x = -1000
        for _, i in self.value_objs.items():
            i.text_obj.pos.x = 1000 * self.scaling_factor


class CarSelection:
    def __init__(self, scene, scene_manager):
        self.scene = scene
        self.scene_manager = scene_manager
        self.app = scene.app
        self.tick = 0
        self.car_type = config.global_variables['car_types'][int(config.global_variables['chosen_car'][0])]
        self.selected_skin = int(config.global_variables['chosen_car'][1])
        self.selected_model = int(config.global_variables['chosen_car'][0])
        self.cooldown = 0
        self.car_rotation = 1
        self.current_car = None
        self.car_names = config.global_variables['car_names']

        initial_size = [640, 360]
        current_size = self.app.WIN_SIZE
        scaling_factor = current_size[0] / initial_size[0]
        self.scaling_factor = scaling_factor

        rec = RectangleVBO(self.app.ctx, size=(self.app.WIN_SIZE[0] * scaling_factor, 50 * scaling_factor))
        bg_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                           [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)
        self.red_background_obj = ImagePlusModel(self, bg_vao, 'red_background',
                                                 pos=(self.app.WIN_SIZE[0] / 2, 40 * scaling_factor), opacity=0.5)

        font = pg.font.SysFont('HighSwift-Regular', int(10 * self.scaling_factor))
        esc_text, size = generate_text_texture(self.app.ctx, 'ESC to go back', font,
                                               color=(255, 255, 255))
        rec = RectangleVBO(self.app.ctx, size=size)
        esc_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                            [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)
        self.esc_text_obj = ImagePlusModel(self, esc_vao, 'None',
                                           pos=(85 * self.scaling_factor, 345 * self.scaling_factor),
                                           texture=esc_text)

        self.change_car()

    def update(self):
        self.tick += 1
        if self.cooldown > 0:
            self.cooldown -= 1

        self.car_rotation += 0.01
        self.current_car.rotation.y = self.car_rotation
        self.current_car.update_rotation()

    def switch_skin(self, dir):
        if self.cooldown > 0:
            return
        num_skins = int(config.global_variables['cars'][self.car_type])
        if dir:
            self.selected_skin = ((self.selected_skin - 2) % num_skins) + 1
        else:
            self.selected_skin = (self.selected_skin % num_skins) + 1
        self.cooldown = 20
        self.change_car()

    def switch_model(self, dir):
        if self.cooldown > 0:
            return
        if dir:
            self.selected_model = (self.selected_model - 1) % len(config.global_variables['car_types'])
        else:
            self.selected_model = (self.selected_model + 1) % len(config.global_variables['car_types'])
        self.selected_skin = 1
        self.car_type = config.global_variables['car_types'][self.selected_model]

        self.cooldown = 20
        self.change_car()

    def change_car(self):
        font = pg.font.SysFont('HighSwift-Regular', int(15 * self.scaling_factor))
        font2 = pg.font.SysFont('HighSwift-Regular', int(10 * self.scaling_factor))
        color = (255, 140, 0)
        color2 = (255, 200, 0)
        if config.global_variables['chosen_car'][0] == f'{self.selected_model}' and config.global_variables['chosen_car'][
            1] == f'{self.selected_skin}':
            color = (255, 255, 255)
            color2 = (255, 255, 255)

        car_text, size = generate_text_texture(self.app.ctx, f'{self.car_type}', font,
                                               color=color)
        rec = RectangleVBO(self.app.ctx, size=size)
        top_text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                                 [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)
        self.top_text_obj = ImagePlusModel(self, top_text_vao, 'None',
                                           pos=(self.app.WIN_SIZE[0] / 2, 50 * self.scaling_factor), texture=car_text)

        car_text, size = generate_text_texture(self.app.ctx, self.car_names[f'{self.car_type}_{self.selected_skin}'], font2,
                                               color=color2)
        rec = RectangleVBO(self.app.ctx, size=size)
        top_text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                                 [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)
        self.bottom_text_obj = ImagePlusModel(self, top_text_vao, 'None',
                                              pos=(self.app.WIN_SIZE[0] / 2, 30 * self.scaling_factor),
                                              texture=car_text)

        self.current_car = VehicleModel(self.scene, self.selected_model, variant=f'{self.selected_skin}',
                                        scale=(0.7, 0.7, 0.7), pos=(1, 0.1, -2))

    def select(self):
        if self.tick > 100:
            config.global_variables['chosen_car'][0] = f'{self.selected_model}'
            config.global_variables['chosen_car'][1] = f'{self.selected_skin}'
            self.change_car()

    def render(self):
        self.current_car.render()
        self.top_text_obj.render()
        self.bottom_text_obj.render()
        self.esc_text_obj.render()
        self.red_background_obj.render()


class SelectedObject:
    def __init__(self, om, text_vao, texts, font, color, size, pos, selected):
        self.options_menu = om
        self.app = self.options_menu.app
        self.selected = selected
        self.texts = texts
        self.font = font
        self.color = color
        self.size = size
        self.text_vao = text_vao
        self.pos = pos
        scores_text, _ = generate_text_texture(self.app.ctx, texts[selected], font,
                                               color=color, size=size)
        self.text_obj = BasicImage(self, text_vao, 'None',
                                   pos=pos,
                                   texture=scores_text)
    def move(self,dir):
        if dir:
            self.selected = (self.selected - 1) % len(self.texts)
        else:
            self.selected = (self.selected + 1) % len(self.texts)
        scores_text, _ = generate_text_texture(self.app.ctx, self.texts[self.selected], self.font,
                                               color=self.color, size=self.size)
        self.text_obj = BasicImage(self, self.text_vao, 'None',
                                   pos=self.pos,
                                   texture=scores_text)

    def render(self):
        self.text_obj.render()

class Pause:
    def __init__(self, scene):
        self.scene = scene
        self.app = scene.app
        self.hidden = False
        self.selected = False

        initial_size = [640, 360]
        current_size = self.app.WIN_SIZE
        scaling_factor = current_size[0] / initial_size[0]
        self.scaling_factor = scaling_factor

        self.font = pg.font.SysFont('HighSwift-Regular', int(16 * scaling_factor))

        dark_rec = RectangleVBO(self.app.ctx, size=self.app.WIN_SIZE)
        text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                             [(dark_rec.vbo, dark_rec.format, *dark_rec.attrib)], skip_errors=True)
        self.darker_obj = ImagePlusModel(self, text_vao, 'darkened',
                                         pos=(self.app.WIN_SIZE[0] / 2, self.app.WIN_SIZE[1] / 2), opacity=0.6)

        scores_text, size = generate_text_texture(self.app.ctx, "Paused", self.font, color=(255, 255, 255))
        rec = RectangleVBO(self.app.ctx, size=size)
        vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['image'],
                                                 [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        self.pause_text_obj = BasicImage(self, vao, 'None', pos=(320 * scaling_factor, 340 * scaling_factor),
                                          texture=scores_text)

        scores_text, size = generate_text_texture(self.app.ctx, f"Exit to main menu?", self.font,
                                                  color=(255, 255, 0))
        rec = RectangleVBO(self.app.ctx, size=size)
        big_text_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['image'],
                                                 [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)
        self.exit_text_obj = BasicImage(self, big_text_vao, 'None',
                                               pos=(320 * scaling_factor, 250 * scaling_factor),
                                               texture=scores_text)
        rec = RectangleVBO(self.app.ctx, size=(self.app.WIN_SIZE[0] * scaling_factor, 30 * scaling_factor))
        bg_vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['imageplus'],
                                           [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)
        self.red_background_obj = ImagePlusModel(self, bg_vao, 'red_background',
                                                 pos=(self.app.WIN_SIZE[0] / 2, 200 * scaling_factor))
        self.select(self.selected)


    def select(self,side):
        self.selected = side
        selected_color = (255,255,255)
        color = (255,255,0)
        scores_text, size = generate_text_texture(self.app.ctx, "Continue", self.font, color=(selected_color if side else color))
        rec = RectangleVBO(self.app.ctx, size=size)
        vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['image'],
                                        [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        self.continue_obj = BasicImage(self, vao, 'None', pos=(240 * self.scaling_factor, 200 * self.scaling_factor),
                                         texture=scores_text)
        scores_text, size = generate_text_texture(self.app.ctx, "Exit", self.font, color=(selected_color if not side else color))
        rec = RectangleVBO(self.app.ctx, size=size)
        vao = self.app.ctx.vertex_array(self.app.mesh.vao.program.programs['image'],
                                        [(rec.vbo, rec.format, *rec.attrib)], skip_errors=True)

        self.exit_obj = BasicImage(self, vao, 'None', pos=(400 * self.scaling_factor, 200 * self.scaling_factor),
                                       texture=scores_text)

    def render(self):

        if self.hidden:
            return
        self.continue_obj.render()
        self.exit_obj.render()
        self.pause_text_obj.render()
        self.exit_text_obj.render()
        self.red_background_obj.render()
        self.darker_obj.render()

