
FROM eclipse-temurin:8-jre-jammy

RUN apt-get update && apt-get install -y curl unzip bash && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN curl -L -o server_pack.zip https://www.curseforge.com/api/v1/mods/253026/files/5222157/download
RUN unzip server_pack.zip -d mcserver-template && rm server_pack.zip

WORKDIR /opt/mcserver-template

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

ARG RCON_PWD
ENV RCON_PWD=${RCON_PWD} 
ARG MOTD
ENV MOTD=${MOTD}
ARG JAVA_ARGS
ENV JAVA_ARGS=${JAVA_ARGS}

RUN cat > server.properties <<EOF
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

# Run ../install-template-hooks.sh for this template before building.
COPY ./resources/start-mcserver.sh /usr/local/bin/start-mcserver.sh
COPY ./resources/auto-restart-container-hook.sh /opt/mcserver-template/auto-restart-container-hook.sh
COPY ./resources/mcron-container-hook.sh /opt/mcserver-template/mcron-container-hook.sh

RUN chmod +x start.sh
RUN mkdir -p /opt/mcserver && chmod +x /usr/local/bin/start-mcserver.sh
ENTRYPOINT ["/usr/local/bin/start-mcserver.sh"]
