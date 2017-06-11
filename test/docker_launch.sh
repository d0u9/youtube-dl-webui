docker run \
    --rm \
    -d \
    --network sky \
    --name youtube_dl_webui \
    -p 5000:5000 \
    -e FLASK_DEBUG=1 \
    -e CONF_FILE=/conf.json \
    -v $HOME/Documents/example_config.json:/conf.json \
    -v $HOME/youtube-dl-webui/youtube_dl_webui/static:/usr/src/youtube_dl_webui/youtube_dl_webui/static \
    -v $HOME/youtube-dl-webui/youtube_dl_webui/templates:/usr/src/youtube_dl_webui/youtube_dl_webui/templates \
    d0u9/youtube-dl-webui:dev
