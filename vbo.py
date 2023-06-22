import numpy as np
import pywavefront

import config


class VBO:
    def __init__(self, ctx):
        self.ctx = ctx
        self.vbos = {}
        self.vbos['cube'] = CubeVBO(ctx)
        self.vbos['skybox'] = SkyBoxVBO(ctx)
        self.add_single_vvbo('podium','podium')

        for i,_ in config.global_variables['cars'].items():
            self.get_car_vbos(i)
        self.get_world_vbos()

    def get_car_vbos(self, car_name):
        objs = pywavefront.Wavefront(f'objects/{car_name}.obj', cache=True, parse=True)
        self.add_vvbo('CarBody', car_name, objs)
        self.add_zvvbo('FrontWheels', car_name + '_front', objs)
        self.add_zvvbo('BackWheels', car_name + '_back', objs)

    def get_world_vbos(self):
        objs = pywavefront.Wavefront(f'objects/track.obj', cache=True, parse=True)
        world_vvbos = {'Road': 'track', 'Markings': 'markings', 'Rail': 'rail', 'End': 'finish', 'Tree': 'tree',
                       'Rock': 'rock'}
        for k, i in world_vvbos.items():
            self.add_vvbo(k, i, objs)

    def add_single_vvbo(self, vbo_name, obj_name):
        obj = pywavefront.Wavefront(f'objects/{obj_name}.obj', cache=True, parse=True)
        vertex_data = obj.materials.popitem()[1].vertices
        vertex_data = np.array(vertex_data, dtype='f4')
        self.vbos[vbo_name] = VertexedVBO(self.ctx, vertex_data)

    def add_vvbo(self, mat_name, vbo_name, obj):
        vertex_data = obj.materials[mat_name].vertices
        vertex_data = np.array(vertex_data, dtype='f4')
        self.vbos[vbo_name] = VertexedVBO(self.ctx, vertex_data)

    def add_zvvbo(self, mat_name, vbo_name, obj):
        vertex_data = obj.materials[mat_name].vertices
        vertex_data = np.array(vertex_data, dtype='f4')
        self.vbos[vbo_name] = ZCenteredVertexedVBO(self.ctx, vertex_data)

    def destroy(self):
        [vbo.destroy() for vbo in self.vbos.values()]


class BaseVBO:
    def __init__(self, ctx):
        self.ctx = ctx
        self.vbo = self.get_vbo()
        self.format: str = None
        self.attrib: list = None

    def get_vertex_data(self): ...

    def get_vbo(self):
        vertex_data = self.get_vertex_data()
        vbo = self.ctx.buffer(vertex_data)
        return vbo

    def destroy(self):
        self.vbo.release()


class RectangleVBO(BaseVBO):
    def __init__(self, ctx, size=(1, 1)):
        self.ctx = ctx
        self.size = size

        self.format: str = '2f 2f'
        self.attrib: list = ['in_position', 'in_texCoord_0']
        self.vbo = self.get_vbo()

    def get_vertex_data(self):
        w, h = self.size
        vertices = [(-w / 2, -h / 2), (w / 2, h / 2),
                    (-w / 2, h / 2), (-w / 2, -h / 2),
                    (w / 2, -h / 2), (w / 2, h / 2)]
        texCoords = [(0, 0), (1, 1), (0, 1), (0, 0), (1, 0), (1, 1)]

        vertices = np.array(vertices, dtype='f4')
        texCoords = np.array(texCoords, dtype='f4')

        data = np.hstack((vertices, texCoords))
        return data

    def get_vbo(self):
        vertex_data = self.get_vertex_data()
        vbo = self.ctx.buffer(vertex_data)
        return vbo

    def destroy(self):
        self.vbo.release()


class VertexedVBO(BaseVBO):
    def __init__(self, app, vertex_data):
        self.vertex_data = vertex_data
        super().__init__(app)
        self.format = '2f 3f 3f'
        self.attrib = ['in_texCoord_0', 'in_normal', 'in_position']

    def get_vertex_data(self):
        return self.vertex_data


class ZCenteredVertexedVBO(BaseVBO):
    def __init__(self, app, vertex_data):
        self.offset_z = None
        self.offset_y = None
        self.vertex_data = vertex_data
        super().__init__(app)
        self.format = '2f 3f 3f'
        self.attrib = ['in_texCoord_0', 'in_normal', 'in_position']

    def get_vertex_data(self):
        min = self.vertex_data[7]
        max = self.vertex_data[7]
        for i in range(16, len(self.vertex_data), 8):
            if min > self.vertex_data[i - 1]:
                min = self.vertex_data[i - 1]
            elif max < self.vertex_data[i - 1]:
                max = self.vertex_data[i - 1]
        offset = (max + min) / 2
        for i in range(8, len(self.vertex_data) + 1, 8):
            self.vertex_data[i - 1] -= offset
        self.offset_z = offset

        min = self.vertex_data[6]
        max = self.vertex_data[6]
        for i in range(16, len(self.vertex_data), 8):
            if min > self.vertex_data[i - 2]:
                min = self.vertex_data[i - 2]
            elif max < self.vertex_data[i - 2]:
                max = self.vertex_data[i - 2]
        offset = (max + min) / 2
        for i in range(8, len(self.vertex_data) + 1, 8):
            self.vertex_data[i - 2] -= offset
        self.offset_y = offset

        return self.vertex_data


class CubeVBO(BaseVBO):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.format = '2f 3f 3f'
        self.attrib = ['in_texCoord_0', 'in_normal', 'in_position']

    @staticmethod
    def get_data(vertices, indices):
        data = [vertices[ind] for triangle in indices for ind in triangle]
        return np.array(data, dtype='f4')

    def get_vertex_data(self):
        vertices = [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
                    (-1, 1, -1), (-1, -1, -1), (1, -1, -1), (1, 1, -1)]

        indices = [(0, 2, 3), (0, 1, 2),
                   (1, 7, 2), (1, 6, 7),
                   (6, 5, 4), (4, 7, 6),
                   (3, 4, 5), (3, 5, 0),
                   (3, 7, 4), (3, 2, 7),
                   (0, 6, 1), (0, 5, 6)]

        vertex_data = self.get_data(vertices, indices)
        tex_coord = [(0, 0), (1, 0), (1, 1), (0, 1)]
        tex_coord_indices = [(0, 2, 3), (0, 1, 2),
                             (0, 2, 3), (0, 1, 2),
                             (0, 1, 2), (2, 3, 0),
                             (2, 3, 0), (2, 0, 1),
                             (0, 2, 3), (0, 1, 2),
                             (3, 1, 2), (3, 0, 1), ]

        tex_coord_data = self.get_data(tex_coord, tex_coord_indices)

        normals = [(0, 0, 1) * 6,
                   (1, 0, 0) * 6,
                   (0, 0, -1) * 6,
                   (-1, 0, 0) * 6,
                   (0, 1, 0) * 6,
                   (0, -1, 0) * 6]
        normals = np.array(normals, dtype='f4').reshape(36, 3)

        vertex_data = np.hstack([normals, vertex_data])
        vertex_data = np.hstack([tex_coord_data, vertex_data])
        return vertex_data


class SkyBoxVBO(BaseVBO):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.format = '3f'
        self.attrib = ['in_position']

    def get_vertex_data(self):
        z = 0.9999
        vertices = [(-1, -1, z), (1, 1, z), (-1, 1, z),
                    (-1, -1, z), (1, -1, z), (1, 1, z)]
        vertex_data = np.array(vertices, dtype='f4')
        return vertex_data
