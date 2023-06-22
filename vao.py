import config
from vbo import VBO
from shader_program import ShaderProgram


class VAO:
    def __init__(self, ctx):
        self.ctx = ctx
        self.vbo = VBO(ctx)
        self.program = ShaderProgram(ctx)
        self.vaos = {}
        base_vaos = ['cube', 'track', 'markings', 'rail', 'finish', 'tree', 'rock', 'podium']
        for i in base_vaos:
            self.add_vao(i, 'default')

        for i, _ in config.global_variables['cars'].items():
            self.get_car(i)
        self.vaos.update(self.get_shadow_vaos())

        self.add_vao('skybox', 'skybox')

    def get_shadow_vaos(self):
        shadow_vaos = {}
        for key, _ in self.vaos.items():
            shadow_vaos[key + '_shadow'] = self.get_vao(program=self.program.programs['shadow'], vbo=self.vbo.vbos[key])
        return shadow_vaos

    def get_car(self, name):
        self.add_vao(name, 'default')
        self.add_vao(name + '_front', 'default_wheels')
        self.add_vao(name + '_back', 'default_wheels')

    def add_vao(self, name, shader, bonus=''):
        self.vaos[name] = self.get_vao(
            program=self.program.programs[shader],
            vbo=self.vbo.vbos[name + bonus]
        )

    def get_vao(self, program, vbo):
        vao = self.ctx.vertex_array(program, [(vbo.vbo, vbo.format, *vbo.attrib)], skip_errors=True)
        return vao

    def destroy(self):
        self.vbo.destroy()
        self.program.destroy()
