#!/bin/bash
IP=$(dig +short myip.opendns.com @resolver1.opendns.com)
envip="server {
    listen 80;
    server_name $IP;
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
"
echo $envip >> /home/ubuntu/home/runner/work/webapp/webapp/ubuntu_web_config/webapp_nginx
