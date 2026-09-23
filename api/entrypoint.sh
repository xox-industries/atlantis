#!/bin/bash
set -e

usermod -u "${UID}" "${USERNAME}"
groupmod -g "${GID}" "${USERNAME}"
usermod -g "${GID}" "${USERNAME}"

chown -R "${UID}:${GID}" /app
chown -R "${UID}:${GID}" "/home/${USERNAME}"

if [ -S /var/run/docker.sock ]; then
    DOCKER_GID=$(stat -c '%g' /var/run/docker.sock)
    GROUP_NAME="dockergroup_${DOCKER_GID}"

    if ! getent group "${DOCKER_GID}" >/dev/null 2>&1; then
        groupadd --gid "${DOCKER_GID}" "${GROUP_NAME}"
    else
        GROUP_NAME=$(getent group "${DOCKER_GID}" | cut -d: -f1)
    fi

    usermod -aG "${GROUP_NAME}" "${USERNAME}"
fi

echo "Username: ${USERNAME}"
echo "UID: $(id -u "${USERNAME}")"
echo "GID: $(id -g "${USERNAME}")"
echo "Groups: $(id -Gn "${USERNAME}")"
echo "Docker GID: ${DOCKER_GID}"
echo "Docker Group: ${GROUP_NAME}"

exec gosu "${USERNAME}" "$@"
