from pyrr import Matrix44
import moderngl as mgl

from util import *
from camera import Camera


vertex_shader = shader_from_path('basic_w_norm.vert')
fragment_shader = shader_from_path('basic_w_norm.frag')
grid_vertex_shader = shader_from_path('basic.vert')
grid_fragment_shader = shader_from_path('basic.frag')


class Scene:
    def __init__(self, ctx):
        self.ctx = ctx
        self.counter = 0
        self.camera = Camera()

        self.prog = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader,
        )
        self.mvp = self.prog['mvp']
        self.const_color = self.prog['const_color']

        self.grid_prog = self.ctx.program(
            vertex_shader=grid_vertex_shader,
            fragment_shader=grid_fragment_shader,
        )
        self.grid_mvp = self.grid_prog['mvp']
        self.grid_const_color = self.grid_prog['const_color']

        self.load_grid()

    def load_mesh(self, mesh):
        self.release_mesh()

        self.vbo = self.ctx.buffer(mesh['gldat'].astype('f4').tobytes())
        self.ibo = self.ctx.buffer(mesh['glindex'].astype('i4').tobytes())
        vao_content = [
            (self.vbo, '3f 3f', 'in_vert', 'in_norm')
        ]
        self.vao = self.ctx.vertex_array(self.prog, vao_content, self.ibo)
        self.model = Matrix44.from_translation((0, -1, 0)) * Matrix44.from_scale((0.1, 0.1, 0.1))
    
    def release_mesh(self):
        if hasattr(self, 'model'):
            self.vbo.release()
            self.ibo.release()
            self.vao.release()
            del self.model

    def load_grid(self):
        self.grid_vbo = self.ctx.buffer(grid(5, 10).astype('f4').tobytes())
        self.grid_vao = self.ctx.simple_vertex_array(self.grid_prog, self.grid_vbo, 'in_vert')
        self.grid_model = Matrix44.from_translation((0, -1, 0))
    
    def clear(self, color=(0.23, 0.23, 0.23)):
        self.ctx.clear(*color)
    
    def draw_grid(self, vp):
        mvp = vp * self.grid_model
        self.grid_mvp.write(mvp.astype('f4').tobytes())
        self.grid_const_color.value = (0.3, 0.3, 0.3)
        self.grid_vao.render(mgl.LINES)

    def draw_mesh(self, vp):
        if hasattr(self, 'model'):
            mvp = vp * self.model
            self.mvp.write(mvp.astype('f4').tobytes())
            self.const_color.value = (0.8, 0.8, 0.8)
            self.vao.render()
    
    def draw(self):
        vp = self.camera.view_proj()
        self.draw_grid(vp)
        self.draw_mesh(vp)
