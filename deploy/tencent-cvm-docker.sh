#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/mangooding/kaiwen-yimeiji.git}"
APP_DIR="${APP_DIR:-/opt/kaiwen-yimeiji}"
APP_PORT="${APP_PORT:-8891}"
IMAGE_NAME="${IMAGE_NAME:-kaiwen-yimeiji:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-kaiwen-yimeiji}"

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

install_packages() {
  if need_cmd apt-get; then
    sudo apt-get update
    sudo apt-get install -y git ca-certificates curl
  elif need_cmd dnf; then
    sudo dnf install -y git ca-certificates curl
  elif need_cmd yum; then
    sudo yum install -y git ca-certificates curl
  else
    echo "Unsupported Linux distribution: please install git, curl and Docker manually." >&2
    exit 1
  fi
}

install_docker() {
  if need_cmd docker; then
    return
  fi

  curl -fsSL https://get.docker.com | sudo sh
  sudo systemctl enable docker || true
  sudo systemctl start docker || true
}

run_docker() {
  if docker ps >/dev/null 2>&1; then
    docker "$@"
  else
    sudo docker "$@"
  fi
}

main() {
  echo "==> Installing base packages"
  install_packages

  echo "==> Installing or checking Docker"
  install_docker

  echo "==> Preparing app directory: ${APP_DIR}"
  if [ -d "${APP_DIR}/.git" ]; then
    cd "${APP_DIR}"
    git fetch --all --prune
    git reset --hard origin/main
  else
    sudo mkdir -p "$(dirname "${APP_DIR}")"
    sudo chown "$(id -u):$(id -g)" "$(dirname "${APP_DIR}")"
    git clone "${REPO_URL}" "${APP_DIR}"
    cd "${APP_DIR}"
  fi

  echo "==> Building image: ${IMAGE_NAME}"
  run_docker build -t "${IMAGE_NAME}" .

  echo "==> Replacing container: ${CONTAINER_NAME}"
  run_docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  run_docker run -d \
    --name "${CONTAINER_NAME}" \
    --restart unless-stopped \
    -p "${APP_PORT}:8891" \
    "${IMAGE_NAME}"

  echo "==> Health check"
  sleep 2
  if curl -fsS "http://127.0.0.1:${APP_PORT}/api/health"; then
    echo
    echo "Deployed successfully: http://SERVER_PUBLIC_IP:${APP_PORT}"
  else
    echo "Container started, but health check failed. Showing logs:" >&2
    run_docker logs --tail 80 "${CONTAINER_NAME}" >&2
    exit 1
  fi
}

main "$@"
