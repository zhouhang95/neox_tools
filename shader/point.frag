#version 330

out vec4 f_color;
uniform vec3 const_color;

void main() {
    float dist = distance(gl_PointCoord, vec2(0.5, 0.5));
    if (dist > 0.5) {
        discard;
    }
    f_color = vec4(const_color, 1.0);
}