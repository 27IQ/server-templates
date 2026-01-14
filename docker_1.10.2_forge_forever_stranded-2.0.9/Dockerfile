FROM eclipse-temurin:8-jre-jammy

ARG RCON_PWD
ENV RCON_PWD=${RCON_PWD} 
ARG MOTD
ENV MOTD=${MOTD}
ARG JAVA_ARGS
ENV JAVA_ARGS=${JAVA_ARGS}

RUN apt-get update && apt-get install -y curl unzip bash && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN curl -L -o server_pack.zip https://www.curseforge.com/api/v1/mods/253026/files/5222157/download
RUN unzip server_pack.zip -d mcserver && rm server_pack.zip

WORKDIR /opt/mcserver

# mcron
RUN apt-get update && \
    apt-get install -y --no-install-recommends git build-essential && \
    git clone https://github.com/Tiiffi/mcrcon.git /tmp/mcrcon && \
    make -C /tmp/mcrcon && \
    ls -l /tmp/mcrcon && \
    install -m 755 /tmp/mcrcon/mcrcon /usr/local/bin/mcrcon && \
    ls -l /usr/local/bin && \
    rm -rf /tmp/mcrcon && \
    apt-get purge -y git build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN echo "eula=true" > eula.txt

RUN cat > server.properties <<EOF
generator-settings=
use-native-transport=true
op-permission-level=4
allow-nether=true
level-name=world
enable-query=false
allow-flight=false
announce-player-achievements=true
server-port=25565
max-world-size=29999984
level-type=DEFAULT
enable-rcon=true
force-gamemode=false
level-seed=
server-ip=
network-compression-threshold=256
max-build-height=256
spawn-npcs=true
white-list=true
spawn-animals=true
snooper-enabled=true
resource-pack-sha1=
online-mode=true
resource-pack=
pvp=true
difficulty=1
enable-command-block=false
player-idle-timeout=0
gamemode=0
max-players=20
max-tick-time=60000
spawn-monsters=true
generate-structures=true
view-distance=10
motd=${MOTD}
rcon.port=25575
rcon.password=${RCON_PWD}
EOF

RUN cat > variables.txt <<EOF
MINECRAFT_VERSION=1.10.2
MODLOADER=Forge
MODLOADER_VERSION=12.18.3.2511
LEGACYFABRIC_INSTALLER_VERSION=1.0.0
FABRIC_INSTALLER_VERSION=1.0.0
QUILT_INSTALLER_VERSION=0.9.1
MINECRAFT_SERVER_URL=https://launcher.mojang.com/v1/objects/3d501b23df53c548254f5e3f66492d178a48db63/server.jar
JAVA_ARGS="${JAVA_ARGS}"
JAVA="java"
EOF

COPY ./resources/auto-restart-container-hook.sh /opt/mcserver/auto-restart-container-hook.sh
COPY ./resources/mcron-container-hook.sh /opt/mcserver/mcron-container-hook.sh

RUN chmod +x start.sh
CMD ["./start.sh"]