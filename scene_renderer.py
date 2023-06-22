from model import ExtendedBaseModel
import moderngl as mgl


class SceneRenderer:
    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.app = scene_manager.app
        self.ctx = self.app.ctx
        self.mesh = self.app.mesh
        self.scene = self.scene_manager.current_scene
        self.depth_texture = self.mesh.texture.textures['depth_texture']
        self.depth_fbo = self.ctx.framebuffer(depth_attachment=self.depth_texture)

    def render_shadow(self):
        self.depth_fbo.clear()
        self.depth_fbo.use()
        for obj in self.scene.objects:
            if isinstance(obj, ExtendedBaseModel):
                obj.render_shadow()

    def main_render(self):
        self.app.ctx.screen.use()
        if self.scene.skybox is not None:
            self.ctx.disable(mgl.DEPTH_TEST)
            self.scene.skybox.render()
            self.ctx.enable(mgl.DEPTH_TEST)
        for obj in self.scene.objects:
            obj.render()

    def render(self):

        self.scene.update()
        self.render_shadow()
        self.main_render()

    def update_scene(self):
        self.scene = self.scene_manager.current_scene

    def destroy(self):
        self.depth_fbo.release()
