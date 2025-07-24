FROM ubuntu:22.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      build-essential cmake libncurses5-dev libssl-dev git \
      iputils-ping wget tcpdump net-tools && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Compilation de SIPp
RUN git clone https://github.com/SIPp/sipp.git /opt/sipp && \
    cd /opt/sipp && \
    cmake . && \
    make -j"$(nproc)" && \
    make install

# On démarre en mode UAS intégré par défaut
EXPOSE 5060/udp

ENTRYPOINT ["sipp", "-sn", "uas", "-i", "0.0.0.0", "-p", "5060", "-trace_msg", "-trace_stat"]
