FROM itzg/minecraft-server:java8

USER root

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl unzip \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /modpacks

RUN curl -fsSL -o /modpacks/server_pack.zip \
  https://www.curseforge.com/api/v1/mods/253026/files/5222157/download

COPY ./resources/auto-restart-container-hook.sh /extras/auto-restart-container-hook.sh
COPY ./resources/mcron-container-hook.sh /extras/mcron-container-hook.sh

RUN chmod +x /extras/auto-restart-container-hook.sh /extras/mcron-container-hook.sh \
 && chown -R 1000:1000 /modpacks /extras

USER 1000
WORKDIR /data

ENV EULA=TRUE \
    TYPE=CURSEFORGE \
    CF_SERVER_MOD=/modpacks/server_pack.zip \
    VERSION=1.10.2 \
    ENABLE_RCON=true \
    RCON_PORT=25575 \
    DIFFICULTY=easy \
    MAX_PLAYERS=20 \
    ENABLE_WHITELIST=true \
    VIEW_DISTANCE=10 \
    USE_AIKAR_FLAGS=true

EXPOSE 25565 25575

ENTRYPOINT ["/start"]
