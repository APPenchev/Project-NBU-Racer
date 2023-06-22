#version 330 core

layout (location = 0) out vec4 fragColor;

in vec2 uv_0;

uniform float u_heat;
uniform sampler2D u_texture_0;
uniform float u_transparency;
uniform vec2 u_offset;
uniform float u_tiling;

void main()
{
    vec4 texColor = texture(u_texture_0, (uv_0*u_tiling)+u_offset);
    if(texColor.a < 0.7)
        discard;
    fragColor = vec4(texColor.rgb * (1 +u_heat),texColor.a * u_transparency);
}