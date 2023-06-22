from scene_renderer import SceneRenderer
from bootloader import *


class SceneManager:
    def __init__(self, app):
        self.app = app
        self.current_scene = None
        self.scene_renderer = None
        self.scenes = {}
        self.on_init()

    def on_init(self):
        self.scene_renderer = SceneRenderer(self)
        self.scenes['RaceScene'] = RaceScene(self)
        self.scenes['RecordScene'] = RecordScene(self)
        self.scenes['TestScene'] = TestScene(self)
        self.scenes['MainMenuScene'] = MainMenuScene(self)
        self.scenes['GarageScene'] = GarageScene(self)
        self.scenes['ExitScene'] = ExitScene(self)
        self.scenes['OptionsScene'] = OptionsScene(self)
        self.switch_scene('MainMenuScene')

    def switch_scene(self, name):
        print(f'Switching to scene - {name}')
        self.current_scene = self.scenes[name]
        self.current_scene.tick = 0
        self.current_scene.objects.clear()
        self.current_scene.load()
        self.scene_renderer.update_scene()

    def resume_scene(self, name):
        print(f'Resuming scene - {name}')
        self.current_scene = self.scenes[name]
        self.scene_renderer.update_scene()

    def render(self):
        self.scene_renderer.render()

    def destroy(self):
        self.scene_renderer.destroy()
