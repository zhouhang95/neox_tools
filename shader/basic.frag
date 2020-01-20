#version 330

out vec4 f_color;
uniform vec3 const_color;

void main() {
    f_color = vec4(const_color, 1.0);
}