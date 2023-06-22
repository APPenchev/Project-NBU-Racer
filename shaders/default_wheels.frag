#version 330

layout (location = 0) out vec4 fragColor;

in vec2 uv_0;
in vec3 normal;
in vec3 fragPos;
in vec4 shadowCoord;

struct Light {
    vec3 position;
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;

};

uniform Light light;
uniform sampler2D u_texture_0;
uniform vec3 camPos;
uniform float tiling;


vec3 getLight(vec3 color){
    vec3 Normal = normalize(normal);

    vec3 ambient = light.ambient;

    vec3 lightDir = normalize(light.position - fragPos);
    float diff = max(0, dot(lightDir, Normal));
    vec3 diffuse = diff * light.diffuse;

    vec3 viewDir = normalize(camPos - fragPos);
    vec3 reflectDir = reflect(-lightDir,Normal);
    float spec = pow(max(dot(viewDir,reflectDir),0),32);
    vec3 specular = spec * light.specular;

    return color* ( ambient + (diffuse + specular));
}

void main(){
    float gamma = 2.2;
    vec3 color = texture(u_texture_0,uv_0*tiling).rgb;
    color = pow(color,vec3(gamma));
    color = getLight(color);
    color = pow(color,1/vec3(gamma));

    fragColor = vec4(color,1.0);
}