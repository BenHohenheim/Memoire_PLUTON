# Dockerfile.client
FROM ubuntu:22.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      build-essential cmake libncurses5-dev libssl-dev git \
      iputils-ping wget tcpdump net-tools && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/SIPp/sipp.git /opt/sipp && \
    cd /opt/sipp && \
    cmake . && \
    make -j"$(nproc)" && \
    make install

# On copie le scénario UAS depuis scenario/
COPY scenario/uas_scenario.xml /opt/sipp/uas_scenario.xml

EXPOSE 5060/udp

ENTRYPOINT ["sipp", "-sf", "/opt/sipp/uas_scenario.xml", "-p", "5060", "-trace_msg"]
