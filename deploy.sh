#!/bin/bash
sudo git -C /mnt/nas/repos/pi-tunnel pull
docker compose pull
docker compose up -d --force-recreate