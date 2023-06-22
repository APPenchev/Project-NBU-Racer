import pygame as pg
import moderngl as mgl
import sys

import config
from model import *
from camera import Camera
from light import Light
from mesh import *
from bootloader import *
from scene_manager import SceneManager
from scene_renderer import SceneRenderer


class GraphicsEngine:
    def __init__(self, win_size=(1920, 1080)):
        pg.init()
        pg.display.set_caption("NBU Racer")
        self.WIN_SIZE = win_size
        pg.mixer.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK, pg.GL_CONTEXT_PROFILE_CORE)
        pg.mouse.set_visible(False)
        self.screen = pg.display.set_mode(self.WIN_SIZE, flags=pg.OPENGL | pg.DOUBLEBUF)

        self.ctx = mgl.create_context()
        self.ctx.enable(flags=mgl.DEPTH_TEST | mgl.CULL_FACE)
        self.ctx.enable(mgl.BLEND)
        self.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
        self.ctx.front_face = 'ccw'
        self.clock = pg.time.Clock()
        self.running = True

        self.delta_time = 0

        self.mesh = Mesh(self)

        self.scene_manager = SceneManager(self)

    def check_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()

    def quit(self):
        self.running = False



    def render(self):
        self.ctx.clear(color=(0, 0, 0))
        self.scene_manager.render()
        pg.display.flip()

    def run(self):
        while self.running:
            self.check_events()
            self.scene_manager.current_scene.camera.update()
            self.render()
            self.delta_time = self.clock.tick(60)
        self.mesh.destroy()
        self.scene_manager.destroy()
        config.save_options('options.txt')
        pg.quit()


if __name__ == "__main__":
    config.parse_options('options.txt')


    while True:
        resolution = config.global_variables['resolutions'][int(config.global_variables['resolution'][0])].split('x')
        app = GraphicsEngine(win_size=(int(resolution[0]), int(resolution[1])))
        app.run()
        if config.global_variables['restarting'][0] == '0':
            break
