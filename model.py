import random

import glm
import random


class BasicImage:
    def __init__(self, scene, vao, tex_id, pos=(0, 0), rot=(0, 0), scale=(1, 1, 1), texture=None):
        self.scene = scene
        self.app = scene.app
        self.vao = vao
        if texture is None:
            self.texture = self.app.mesh.texture.textures[tex_id]
        else:
            self.texture = texture
        self.pos = glm.vec2(pos)
        self.rotation = glm.vec2(rot)
        self.shader_program = self.vao.program
        self.scale = scale
        self.on_init()

    def on_init(self):
        self.shader_program['u_texture_0'] = 0
        self.texture.use(location=0)
        self.shader_program['u_resolution'].write(glm.vec2(self.app.WIN_SIZE))
        self.shader_program['u_rotation_angle'].write(self.rotation)
        self.shader_program['u_pos'].write(self.pos)

    def render(self):
        self.update()
        self.vao.render()

    def update(self):
        self.texture.use(location=0)
        self.shader_program['u_rotation_angle'].write(self.rotation)
        self.shader_program['u_pos'].write(self.pos)


class BaseModel:
    def __init__(self, scene, vao_name, tex_id, pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), tiling=1, texture=None):
        self.scene = scene
        self.app = scene.app
        self.pos = pos
        self.rotation = glm.vec3(rot)
        self.scale = scale
        if texture is None:
            self.texture = self.app.mesh.texture.textures[tex_id]
        else:
            self.texture = texture
        self.vao_name = vao_name
        self.vao = self.app.mesh.vao.vaos[vao_name]
        self.shader_program = self.vao.program
        self.tiling = tiling
        self.m_model = self.get_model_matrix()
        self.camera = self.scene.camera

    def get_model_matrix(self):
        m_model = glm.mat4()
        m_model = glm.translate(m_model, self.pos)
        m_model = glm.rotate(m_model, self.rotation.x, glm.vec3(1, 0, 0))
        m_model = glm.rotate(m_model, self.rotation.y, glm.vec3(0, 1, 0))
        m_model = glm.rotate(m_model, self.rotation.z, glm.vec3(0, 0, 1))
        m_model = glm.scale(m_model, self.scale)
        return m_model

    def render(self):
        self.update()
        self.vao.render()

    def update(self):
        ...


class ExtendedBaseModelShadowless(BaseModel):
    def __init__(self, scene, vao_name, tex_id, pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), tiling=1, texture=None):
        super().__init__(scene, vao_name, tex_id, pos, rot, scale, tiling, texture)
        self.on_init()

    def on_init(self):
        self.shader_program['u_texture_0'] = 0
        self.texture.use()

        self.shader_program['light.position'].write(self.scene.light.position)
        self.shader_program['light.ambient'].write(self.scene.light.ambient)
        self.shader_program['light.diffuse'].write(self.scene.light.diffuse)
        self.shader_program['light.specular'].write(self.scene.light.specular)

        self.shader_program['m_proj'].write(self.scene.camera.m_proj)
        self.shader_program['m_view'].write(self.scene.camera.m_view)
        self.shader_program['m_model'].write(self.m_model)

        self.shader_program['tiling'] = self.tiling

    def update(self):
        self.texture.use(location=0)
        self.shader_program['m_view'].write(self.scene.camera.m_view)
        self.shader_program['camPos'].write(self.scene.camera.position)
        self.shader_program['m_model'].write(self.get_model_matrix())
        self.shader_program['tiling'] = self.tiling


class StaticBaseModel(BaseModel):
    def __init__(self, scene, vao_name, tex_id, m_model, pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), tiling=1,
                 texture=None):
        super().__init__(scene, vao_name, tex_id, pos, rot, scale, tiling, texture)
        self.m_model = m_model
        self.on_init()

    def on_init(self):
        self.shader_program['u_texture_0'] = 0
        self.texture.use()

        self.shader_program['light.position'].write(self.scene.light.position)
        self.shader_program['light.ambient'].write(self.scene.light.ambient)
        self.shader_program['light.diffuse'].write(self.scene.light.diffuse)
        self.shader_program['light.specular'].write(self.scene.light.specular)

        self.shader_program['m_proj'].write(self.scene.camera.m_proj)
        self.shader_program['m_view'].write(self.scene.camera.m_view)
        self.shader_program['m_model'].write(self.m_model)

        self.shader_program['tiling'] = self.tiling

    def update(self):
        self.texture.use(location=0)
        self.shader_program['m_view'].write(self.scene.camera.m_view)
        self.shader_program['camPos'].write(self.scene.camera.position)
        self.shader_program['m_model'].write(self.m_model)
        self.shader_program['tiling'] = self.tiling


class ExtendedBaseModel(ExtendedBaseModelShadowless):
    def __init__(self, scene, vao_name, tex_id, pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), tiling=1, texture=None):
        super().__init__(scene, vao_name, tex_id, pos, rot, scale, tiling, texture)
        self.on_init()

    def on_init(self):
        super().on_init()
        self.shader_program['m_view_light'].write(self.scene.light.m_view_light)
        self.shader_program['u_resolution'].write(glm.vec2(self.app.WIN_SIZE))
        self.depth_texture = self.app.mesh.texture.textures['depth_texture']
        self.shader_program['shadowMap'] = 1
        self.depth_texture.use(location=1)
        self.shadow_vao = self.app.mesh.vao.vaos[self.vao_name + '_shadow']
        self.shadow_program = self.shadow_vao.program
        self.shadow_program['m_proj'].write(self.camera.m_proj)
        self.shadow_program['m_view_light'].write(self.scene.light.m_view_light)
        self.shadow_program['m_model'].write(self.m_model)

    def update(self):
        super().update()
        self.texture.use(location=0)
        self.shader_program['m_view_light'].write(self.scene.light.m_view_light)
        self.shader_program['light.position'].write(self.scene.light.position)

    def update_shadow(self):
        self.shadow_program['m_view_light'].write(self.scene.light.m_view_light)
        self.shadow_program['m_model'].write(self.m_model)

    def render_shadow(self):
        self.update_shadow()
        self.shadow_vao.render()


class ExtendedBaseModelBody(ExtendedBaseModel):
    def __init__(self, app, vao_name, tex_id, pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), tiling=1, texture=None):
        super().__init__(app, vao_name, tex_id, pos, rot, scale, tiling, texture)

    def get_model_matrix(self):
        m_model = glm.mat4()
        m_model = glm.translate(m_model, self.pos)
        m_model = glm.rotate(m_model, self.rotation.y, glm.vec3(0, 1, 0))
        m_model = glm.rotate(m_model, self.rotation.z, glm.vec3(0, 0, 1))
        m_model = glm.scale(m_model, self.scale)
        return m_model


class ExtendedBaseModelWheel(ExtendedBaseModelShadowless):
    def __init__(self, scene, vao_name, tex_id, pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), tiling=1, car=None,
                 texture=None):
        super().__init__(scene, vao_name, tex_id, pos, rot, scale, tiling, texture)
        self.m_offset = self.get_offset_matrix()
        self.car = car

    def get_model_matrix(self):
        m_model = glm.mat4()
        m_model = glm.rotate(m_model, self.rotation.x, glm.vec3(1, 0, 0))
        m_model = glm.scale(m_model, self.scale)
        return m_model

    def get_offset_matrix(self):
        m_offset = glm.mat4()
        offset = (
            0, self.app.mesh.vao.vbo.vbos[self.vao_name].offset_y, self.app.mesh.vao.vbo.vbos[self.vao_name].offset_z)
        m_offset = glm.translate(m_offset, offset)
        return m_offset

    def update(self):
        super().update()
        self.shader_program['m_offset'].write(self.m_offset)
        self.shader_program['m_car'].write(self.car.body.get_model_matrix())


class ImagePlusModel(BasicImage):
    def __init__(self, scene, vao, tex_id, pos=(0, 0), rot=(0, 0), scale=(1, 1, 1), texture=None, offset=(0, 0), tiling=1,
                 opacity=1):
        super().__init__(scene, vao, tex_id, pos, rot, scale, texture)
        self.offset = glm.vec2(offset)
        self.heat_max = 0.5
        self.heat = 0
        self.shake_power = 0
        self.opacity = opacity
        self.tiling = tiling

    def update(self):
        super().update()
        self.shader_program['u_shake'].write(self.get_shake())
        self.shader_program['u_heat'] = self.heat
        self.shader_program['u_transparency'] = self.opacity
        self.shader_program['u_offset'].write(self.offset)
        self.shader_program['u_tiling'] = self.tiling

    def set_heat(self, value):
        if value >= self.heat_max:
            self.heat = self.heat_max
        else:
            self.heat = value

    def get_shake(self):
        return glm.vec2(random.randint(0, self.shake_power), random.randint(0, self.shake_power))


class Skybox(ExtendedBaseModel):
    def __init__(self, scene, vao_name='skybox', tex_id='skybox', pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
                 tiling=1, texture=None):
        self.tex_id = tex_id
        super().__init__(scene, vao_name, tex_id, pos, rot, scale, tiling, texture)

    def on_init(self):
        self.texture = self.app.mesh.texture.textures[self.tex_id]
        self.shader_program['u_texture_skybox'] = 0
        self.texture.use()

    def update(self):
        m_view = glm.mat4(glm.mat3(self.camera.m_view))
        self.shader_program['m_invProjView'].write(glm.inverse(self.camera.m_proj * m_view))
