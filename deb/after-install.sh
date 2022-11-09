#!/bin/bash

systemctl daemon-reload

if `systemctl is-active --quiet sudoisbot@temp_pub`; then
    echo -n "restarting temp_pub..."
    service sudoisbot@temp_pub restart
    echo "ok"
fi
