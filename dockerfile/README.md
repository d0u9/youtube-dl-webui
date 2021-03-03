# youtube-dl-webui

---

Visit [GitHub](https://github.com/d0u9/youtube-dl-webui) for more details.


## Install

1. From DockerHUB

        docker pull d0u9/youtube-dl-webui

    For china users, aliyun docker repo is more preferable:

        docker pull registry.cn-hangzhou.aliyuncs.com/master/youtube-dl-webui


2. From DockerFile

        cd /tmp
        docker build -f </path/to/Dockerfile> -t youtube-dl-webui .

## Usage

1. Run container

        docker run -d \
            --name <container_name> \
            -e PGID=<gid> \
            -e PUID=<uid> \
            -e PORT=port \
            -e CONF_FILE=<config_file_in_container> \
            -v <config_file>:<config_file_in_container> \
            -p <host_port>:<port> \
            -v <host_download_dir>:<download_dir> \
            d0u9/youtube-dl-webui


2. Automatically start container after booting

    Create `/etc/systemd/system/docker-youtube_dl_webui.service`, and fill
    with the contents below:

        [Unit]
        Description=youtube-dl downloader
        Requires=docker.service
        After=docker.service

        [Service]
        Restart=always
        ExecStart=/usr/bin/docker start -a <container_name>
        ExecStop=/usr/bin/docker stop -t 2 <container_name>

        [Install]
        WantedBy=default.target

## Default configurations

All defualt settings can be found in [this json file](https://github.com/d0u9/docker/blob/master/dockerfiles/youtube-dl-webui/default_config.json).

- Files save to: `/tmp/youtube_dl`;
- Database file location: `/tmp/youtube_dl_webui.db`;
- Log size: `10`;
- Listen address: `0.0.0.0`;
- Listen port: `5000`

---


