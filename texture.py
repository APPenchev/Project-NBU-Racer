import os

import pygame as pg
import moderngl as mgl
from PIL import Image


class Texture:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.textures = {}
        texture_dir = 'textures'
        texture_files = os.listdir(texture_dir)

        self.textures = {}
        for file_name in texture_files:
            if file_name.endswith('.png'):
                texture_name = os.path.splitext(file_name)[0]
                self.textures[texture_name] = self.get_texture_A(path=os.path.join(texture_dir, file_name))
            elif file_name.endswith('.jpg'):
                texture_name = os.path.splitext(file_name)[0]
                self.textures[texture_name] = self.get_texture(path=os.path.join(texture_dir, file_name))
        self.textures['skybox'] = self.get_texture_cube(path='textures/')
        self.textures['depth_texture'] = self.get_depth_texture()

    def get_depth_texture(self):
        depth_texture = self.ctx.depth_texture(self.app.WIN_SIZE)
        depth_texture.repeat_x = False
        depth_texture.repeat_y = False
        return depth_texture

    def get_texture_cube(self, path):
        faces = ['front', 'back', 'top', 'bottom'] + ['left', 'right'][::-1]
        textures = []
        for face in faces:
            texture = pg.image.load(path + f'{face}.png').convert()
            if face in ['right', 'left', 'front', 'back']:
                texture = pg.transform.flip(texture, flip_x=True, flip_y=False)
            else:
                texture = pg.transform.flip(texture, flip_x=False, flip_y=True)
            textures.append(texture)
        size = textures[0].get_size()
        texture_cube = self.ctx.texture_cube(size=size, components=3,
                                             data=None)
        for i in range(6):
            texture_data = pg.image.tostring(textures[i], 'RGB')
            texture_cube.write(face=i, data=texture_data)
        return texture_cube

    def get_texture(self, path):
        texture = pg.image.load(path).convert()
        texture = pg.transform.flip(texture, flip_x=False, flip_y=True)
        texture = self.ctx.texture(size=texture.get_size(), components=3,
                                   data=pg.image.tostring(texture, 'RGB'))
        texture.filter = (mgl.LINEAR_MIPMAP_LINEAR, mgl.LINEAR)
        texture.build_mipmaps()
        texture.anisotropy = 32.0
        return texture

    def get_texture_A(self, path):
        diffuse_texture_image = Image.open(path).transpose(Image.FLIP_TOP_BOTTOM).convert(
            "RGBA")

        texture = self.ctx.texture(diffuse_texture_image.size, 4, diffuse_texture_image.tobytes())
        texture.filter = (mgl.LINEAR_MIPMAP_LINEAR, mgl.LINEAR)
        texture.build_mipmaps()
        texture.anisotropy = 32.0
        return texture

    def destroy(self):
        [tex.release() for tex in self.textures.values()]
