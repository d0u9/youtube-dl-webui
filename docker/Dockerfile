# For ubuntu, the latest tag points to the LTS version, since that is
# recommended for general use.
FROM python:3.6-slim

# grab gosu for easy step-down from root
ENV GOSU_VERSION 1.10
RUN set -x \
	&& buildDeps=' \
		unzip \
		ca-certificates \
		dirmngr \
		wget \
	' \
	&& apt-get update && apt-get install -y --no-install-recommends $buildDeps \
	&& wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$(dpkg --print-architecture)" \
	&& wget -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$(dpkg --print-architecture).asc" \
	&& export GNUPGHOME="$(mktemp -d)" \
	&& gpg --keyserver ha.pool.sks-keyservers.net --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4 \
	&& gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu \
	&& rm -r "$GNUPGHOME" /usr/local/bin/gosu.asc \
	&& chmod +x /usr/local/bin/gosu \
	&& gosu nobody true

# install youtube-dl-webui
ENV YOUTUBE_DL_WEBUI_SOURCE /usr/src/youtube_dl_webui
WORKDIR $YOUTUBE_DL_WEBUI_SOURCE

RUN : \
	&& pip install --no-cache-dir youtube-dl flask \
	&& wget -O youtube-dl-webui.zip https://github.com/d0u9/youtube-dl-webui/archive/master.zip \
	&& unzip youtube-dl-webui.zip \
	&& cd youtube-dl-webui*/ \
	&& cp -r ./* $YOUTUBE_DL_WEBUI_SOURCE/ \
	&& ln -s $YOUTUBE_DL_WEBUI_SOURCE/example_config.json /etc/youtube-dl-webui.json \
	&& cd .. && rm -rf youtube-dl-webui* \
	&& apt-get purge -y --auto-remove wget unzip dirmngr \
	&& rm -fr /var/lib/apt/lists/*

COPY docker-entrypoint.sh /usr/local/bin
COPY default_config.json /config.json
ENTRYPOINT ["docker-entrypoint.sh"]

CMD ["python", "-m", "youtube_dl_webui"]
