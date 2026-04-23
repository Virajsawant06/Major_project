FROM ubuntu:22.04

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies (Java for ZAP, Python for Sentinel, Node for npm)
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    python3 \
    python3-pip \
    python3-venv \
    openjdk-11-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for npm
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install ZAP
ENV ZAP_VERSION=2.15.0
RUN wget https://github.com/zaproxy/zap-archive/releases/download/zap-v${ZAP_VERSION}/ZAP_${ZAP_VERSION}_Linux.tar.gz -O /tmp/zap.tar.gz \
    && tar -xzf /tmp/zap.tar.gz -C /opt/ \
    && mv /opt/ZAP_${ZAP_VERSION} /opt/zap \
    && rm /tmp/zap.tar.gz

ENV PATH="/opt/zap:$PATH"

# Install project discovery tools (nuclei, subfinder)
RUN wget https://github.com/projectdiscovery/nuclei/releases/download/v3.3.0/nuclei_3.3.0_linux_amd64.zip -O /tmp/nuclei.zip \
    && apt-get update && apt-get install -y unzip \
    && unzip /tmp/nuclei.zip -d /usr/local/bin \
    && rm /tmp/nuclei.zip

RUN wget https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_amd64.zip -O /tmp/subfinder.zip \
    && unzip /tmp/subfinder.zip -d /usr/local/bin \
    && rm /tmp/subfinder.zip

# Set up Sentinel application
WORKDIR /app
COPY . /app/

# Install python dependencies globally inside the container
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir -e .

# Install npm wrapper globally
RUN npm pack && npm install -g sentinel-security-*.tgz

# Expose ZAP API port
EXPOSE 8080

# The entry script will start ZAP in the background and then drop into the CLI
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["sentinel"]
