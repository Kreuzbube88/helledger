#!/bin/sh
set -e

PUID=${PUID:-99}
PGID=${PGID:-100}

groupmod -o -g "$PGID" helledger
usermod -o -u "$PUID" helledger

chown -R helledger:helledger /data /backups

exec gosu helledger "$@"
