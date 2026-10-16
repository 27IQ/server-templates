FROM debian:bookworm-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl bash tar python3 git build-essential \
 && update-ca-certificates \
 && git clone https://github.com/Tiiffi/mcrcon.git /tmp/mcrcon \
 && make -C /tmp/mcrcon \
 && install -m 755 /tmp/mcrcon/mcrcon /usr/local/bin/mcrcon \
 && rm -rf /tmp/mcrcon \
 && apt-get purge -y git build-essential \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

ARG GRAALVM_ARCH=x64
ENV JAVA_HOME=/opt/graalvm
ENV PATH="${JAVA_HOME}/bin:${PATH}"

RUN curl -fsSL "https://download.oracle.com/graalvm/21/latest/graalvm-jdk-21_linux-${GRAALVM_ARCH}_bin.tar.gz" -o /tmp/graalvm.tar.gz \
 && tar -xzf /tmp/graalvm.tar.gz -C /opt \
 && mv /opt/graalvm-jdk-* "${JAVA_HOME}" \
 && rm /tmp/graalvm.tar.gz \
 && java -version

WORKDIR /opt/mcserver-template

# Versions from the Prism instance: Minecraft 1.21.1 / NeoForge 21.1.259.
RUN curl -fsSL "https://maven.neoforged.net/releases/net/neoforged/neoforge/21.1.259/neoforge-21.1.259-installer.jar" -o /tmp/neoforge-installer.jar \
 && java -jar /tmp/neoforge-installer.jar --installServer \
 && rm /tmp/neoforge-installer.jar

# Run ../install-template-hooks.sh for this template before building.
COPY ./resources/start-mcserver.sh /usr/local/bin/start-mcserver.sh
COPY ./resources/auto-restart-container-hook.sh ./auto-restart-container-hook.sh
COPY ./resources/mcron-container-hook.sh ./mcron-container-hook.sh
COPY ./resources/prism-mods.py /usr/local/bin/prism-mods.py
COPY ./resources/start-prism.sh ./start.sh

RUN mkdir -p /opt/mcserver /opt/prism \
 && chmod +x /usr/local/bin/start-mcserver.sh start.sh

EXPOSE 25565 25575
ENTRYPOINT ["/usr/local/bin/start-mcserver.sh"]
