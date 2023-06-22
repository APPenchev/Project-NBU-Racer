import glm
import pygame as pg

NEAR = 0.1
FAR = 1000



class Camera:
    def __init__(self, app, position=(0, 0, 0), yaw=0, pitch=0):
        self.app = app
        self.fov = 70
        self.aspect_ratio = app.WIN_SIZE[0] / app.WIN_SIZE[1]
        self.position = glm.vec3(position)
        self.forward = glm.vec3(0, 0, -1)
        self.side = glm.vec3(1, 0, 0)
        self.up = glm.vec3(0, 1, 0)
        self.yaw = yaw
        self.pitch = pitch
        self.update_rotation()
        self.m_view = self.get_view_matrix()
        self.m_proj = self.get_projection_matrix()

    def update(self):
        self.m_view = self.get_view_matrix()
        self.m_proj = self.get_projection_matrix()

    def update_rotation(self):
        yaw, pitch = glm.radians(self.yaw), glm.radians(self.pitch)

        self.forward.x = glm.cos(yaw) * glm.cos(pitch)
        self.forward.y = glm.sin(pitch)
        self.forward.z = glm.sin(yaw) * glm.cos(pitch)

        self.forward = glm.normalize(self.forward)
        self.side = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.side, self.forward))

    def get_projection_matrix(self):
        return glm.perspective(glm.radians(self.fov), self.aspect_ratio, NEAR, FAR)

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.position + self.forward, self.up)
