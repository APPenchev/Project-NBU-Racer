from abc import abstractmethod

from camera import Camera
from light import Light
from model import *
import random


class BasicScene:
    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.app = scene_manager.app
        self.objects = []
        self.tick = 0
        self.light = Light()
        self.camera = Camera(self.app)
        self.skybox = None


    def add_object(self, obj):
        self.objects.append(obj)

    @abstractmethod
    def load(self):
       pass

    @abstractmethod
    def custom_update(self):
        pass


    def update(self):
        self.tick += 1
        self.custom_update()
