
FROM eclipse-temurin:21-jre

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl unzip bash \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN curl -L -o server_pack.zip https://www.curseforge.com/api/v1/mods/1518508/files/8199866/download
RUN unzip server_pack.zip -d mcserver-template && rm server_pack.zip

WORKDIR /opt/mcserver-template

# mcron
RUN apt-get update && \
    apt-get install -y --no-install-recommends git build-essential && \
    git clone https://github.com/Tiiffi/mcrcon.git /tmp/mcrcon && \
    make -C /tmp/mcrcon && \
    install -m 755 /tmp/mcrcon/mcrcon /usr/local/bin/mcrcon && \
    rm -rf /tmp/mcrcon && \
    apt-get purge -y git build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN echo "eula=true" > eula.txt

ARG RCON_PWD
ENV RCON_PWD=${RCON_PWD} 
ARG MOTD
ENV MOTD=${MOTD}
ARG MEMORY=6G
ENV MEMORY=${MEMORY}
ARG JAVA_ARGS=
ENV JAVA_ARGS=${JAVA_ARGS}
ARG RCON_PORT=
ENV RCON_PORT=${RCON_PORT}
ARG ENABLE_WHITELIST=true
ENV ENABLE_WHITELIST=${ENABLE_WHITELIST}

RUN set_prop() { \
      key="$1"; value="$2"; file="$3"; \
      awk -v key="$key" -v value="$value" 'BEGIN { found=0 } index($0, key "=") == 1 { print key "=" value; found=1; next } { print } END { if (!found) print key "=" value }' "$file" > "$file.tmp"; \
      mv "$file.tmp" "$file"; \
    }; \
    set_prop "motd" "${MOTD}" server.properties; \
    set_prop "rcon.port" "${RCON_PORT}" server.properties; \
    set_prop "rcon.password" "${RCON_PWD}" server.properties; \
    set_prop "white-list" "${ENABLE_WHITELIST}" server.properties; \
    set_prop "JAVA_ARGS" "\"-Xmx${MEMORY} -Xms${MEMORY} ${JAVA_ARGS}\"" variables.txt


# Run ../install-template-hooks.sh for this template before building.
COPY ./resources/start-mcserver.sh /usr/local/bin/start-mcserver.sh
COPY ./resources/auto-restart-container-hook.sh /opt/mcserver-template/auto-restart-container-hook.sh
COPY ./resources/mcron-container-hook.sh /opt/mcserver-template/mcron-container-hook.sh

RUN chmod +x start.sh
RUN mkdir -p /opt/mcserver && chmod +x /usr/local/bin/start-mcserver.sh
ENTRYPOINT ["/usr/local/bin/start-mcserver.sh"]
