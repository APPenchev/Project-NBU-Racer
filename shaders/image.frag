#version 330 core

layout (location = 0) out vec4 fragColor;

in vec2 uv_0;

uniform sampler2D u_texture_0;

void main()
{
    vec4 texColor = texture(u_texture_0, uv_0);
    if(texColor.a < 0.7)
        discard;
    fragColor = texColor;
}