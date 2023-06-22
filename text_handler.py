import pygame as pg
import moderngl as mgl


def generate_text_texture(ctx, text, font, color=(0, 0, 0), size=None):
    text_render = font.render(text, True, color)
    if size is None:
        size = font.size(text)
    surface = pg.Surface(size, flags=pg.SRCALPHA)
    surface.blit(text_render, (0, 0))
    surface = pg.transform.flip(surface, flip_x=False, flip_y=True)
    texture = ctx.texture(size=surface.get_size(), components=4, data=pg.image.tostring(surface, 'RGBA'))

    return texture, size
