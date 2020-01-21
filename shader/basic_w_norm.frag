#version 330

out vec4 f_color;
in float intensity;
uniform vec3 const_color;

void main() {
    float intensity = intensity * 0.6 + 0.4;
    f_color = vec4(const_color * intensity, 1.0);
}