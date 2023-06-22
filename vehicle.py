import config
from custom_objects import VehicleModel
import math
import glm


class Vehicle(VehicleModel):
    def __init__(self, scene, vao_car_id, pos=(0, 0, 0), rot=(0, 0, 0), variant='1'):
        super().__init__(scene, vao_car_id, pos, rot, variant)
        self.forward = glm.vec3(0, 0, -1)
        self.up = glm.vec3(0, 1, 0)
        self.side = glm.vec3(1, 0, 0)
        attrs = config.global_variables['car_attributes'][self.name].split('x')
        # How much can you turn the steering wheel
        self.max_rotational_angle = 1
        # How much the steering wheel is turned
        self.rotational_angle = 0
        # How fast the steering wheel turns every update
        self.rotational_speed = float(attrs[0])
        # How fast and in what direction is the car moving
        self.velocity = 0
        # How fast can the car accelerate
        self.acceleration = float(attrs[1])
        # How fast can the car decelerate
        self.brake_effectiveness = float(attrs[2])
        # How fast is the car at 100% gas
        self.top_speed = float(attrs[3])
        # How much speed the car loses every update
        self.friction = float(attrs[4])

        self.on_road = True

        self.friction_off_road = 0.98
        # GASSSSS!
        self.gas = 0
        self.update_rotation()
        self.update_rotation_v()

    def update_rotation_v(self):
        pitch, yaw, _ = self.rotation

        self.forward.z = glm.cos(yaw) * glm.cos(pitch)
        self.forward.y = glm.sin(pitch)
        self.forward.x = glm.sin(yaw) * glm.cos(pitch)

        self.forward = glm.normalize(self.forward)
        self.side = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.side, self.forward))

    def update_pos(self):
        if self.gas >= 1:
            self.gas -= 1
        if self.gas > 0:
            self.velocity += ((self.gas / 100) * self.top_speed)
        if self.on_road:
            self.velocity *= self.friction
        else:
            self.velocity *= self.friction_off_road

        if self.velocity >= 1:
            self.move_wheel_rotation(self.velocity / 2000)
        if math.fabs(self.rotational_angle) * self.rotational_speed >= 0.001 and self.velocity > 10:
            self.rotation.y += self.rotational_angle * self.rotational_speed * self.velocity / 500
            self.rotational_angle *= 0.99

        self.update_rotation_v()
        self.update_rotation()
        self.set_pos(self.pos + self.forward * self.velocity / 2000)

    def accelerate(self):
        if self.gas <= 100 - self.acceleration:
            self.gas += self.acceleration

    def hit_brake(self):
        if self.velocity - self.brake_effectiveness >= 0:
            self.velocity -= self.brake_effectiveness

    def rotate(self, side):
        if side:
            if self.rotational_angle <= self.max_rotational_angle - self.rotational_speed:
                self.rotational_angle += self.rotational_speed
        else:
            if self.rotational_angle >= -self.max_rotational_angle + self.rotational_speed:
                self.rotational_angle -= self.rotational_speed
