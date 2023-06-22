#version 330 core

layout (location = 0) in vec2 in_position;
layout (location = 1) in vec2 in_texCoord_0;

out vec2 uv_0;

uniform vec2 u_pos;
uniform vec2 u_resolution;
uniform float u_rotation_angle;
uniform vec2 u_shake;

void main()
{
    mat2 rotation_matrix = mat2(cos(u_rotation_angle), -sin(u_rotation_angle),
                                sin(u_rotation_angle), cos(u_rotation_angle));
    vec2 rotated_position = rotation_matrix * in_position;

    gl_Position = vec4((rotated_position + u_pos + u_shake) / u_resolution * 2.0 - 1.0,
                       0.0, 1.0);
    uv_0 = in_texCoord_0;
}