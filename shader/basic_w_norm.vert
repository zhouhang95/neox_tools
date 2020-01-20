#version 330

in vec3 in_vert;
in vec3 in_norm;
out float intensity;
uniform mat4 mvp;

void main() {
    vec3 norm = normalize(transpose(inverse(mat3(mvp))) * in_norm);
    intensity = abs(dot(norm, vec3(0.0, 0.0, 1.0)));
    gl_Position = mvp * vec4(in_vert, 1.0);
}