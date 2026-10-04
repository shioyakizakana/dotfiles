#!/usr/bin/env bash

set -euo pipefail

sudo apt update -y && sudo upgrade -y

sudo apt install -y \
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
