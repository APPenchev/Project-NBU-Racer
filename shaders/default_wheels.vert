#version 330

layout (location = 0) in vec2 in_texCoord_0;
layout (location = 1) in vec3 in_normal;
layout (location = 2) in vec3 in_position;


out vec2 uv_0;
out vec3 normal;
out vec3 fragPos;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_offset;
uniform mat4 m_model;
uniform mat4 m_car;

mat4 m_shadow_bias = mat4(
    0.5,0.0,0.0,0.0,
    0.0,0.5,0.0,0.0,
    0.0,0.0,0.5,0.0,
    0.5,0.5,0.5,1.0
);

void main() {
    uv_0 = in_texCoord_0;
    fragPos = vec3(m_model *  m_car * m_offset * vec4(in_position,1.0));
    normal = mat3(transpose(inverse(m_car * m_offset * m_model))) * normalize(in_normal);
    gl_Position = m_proj * m_view * m_car * m_offset * m_model * vec4(in_position, 1.0);
}