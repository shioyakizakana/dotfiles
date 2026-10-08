#!/usr/bin/env bash

set -euo pipefail

log() {
  printf "\n=== %s\n" "$*"
}

read -rp "インストールを開始しますか? [y/N]: " confirm

if [[ "$confirm" =~ ^[Yy] ]]; then

  sudo apt update -y && sudo apt upgrade -y

  sudo apt install -y \
    age \
    autoconf \
    build-essential \
    cmake \
    curl \
    gpg \
    libbz2-dev \
    libcurl4-openssl-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    ligz-dev \
    make \
    tar \
    tree \
    unzip \
    vim \
    wget

  log "インストールが完了しました。"
else
  log "インストールをスキップしました。"
  exit 0
fi
