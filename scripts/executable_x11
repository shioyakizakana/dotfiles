#!/usr/bin/env bash

set -e

export DISPLAY=:0

# 二重起動を防ぐ
pkill fcitx5 2>/dev/null || true
pkill mozc_server 2>/dev/null || true
sleep 1

# ========================================
# 環境変数
# ========================================

# XDG
export XDG_CURRENT_DESKTOP=XFCE
export XDG_MENU_PREFIX=xfce-
export XDG_SESSION_DESKTOP=xfce
export XDG_RUNTIME_DIR=${TMPDIR:-/tmp}
export XDG_CONFIG_DIRS=/data/data/com.termux/files/usr/etc/xdg
# 日本語入力
export GTK_IM_MODULE=fcitx
export QT_IM_MODULE=fcitx
export CLUTTER_IM_MODULE=fcitx
export GLFW_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx

# ブラウザ
# Termux側のブラウザを使う
export BROWSER="/data/data/com.termux/files/usr/bin/firefox"

# GPU
export MESA_GL_VERSION_OVERRIDE=4.0
export GALLIUM_DRIVER=virpipe

# ========================================
# 音声
# ========================================
# TermuxのXFCEを起動する場合はpulseaudioを起動
# Proot版UbuntuのXFCEを起動する場合は事前にTermux側で起動
# pulseaudio --start --verbose --exit-idle-time=-1 &

export PULSE_SERVER=tcp:127.0.0.1:4713

# ========================================
# fcitx5の有効化
# ========================================
/usr/lib/mozc/mozc_server &
/usr/bin/fcitx5 --enable xim &

# ========================================
# Termux:X11 + XFCE(Termux)
# ========================================
# TermuxのXFCEを起動する場合
# Termux側で`termux-x11 :0 &`を実行
# `--shared-tmpオプションをつけてProotにログイン`
dbus-launch --exit-with-session xfce4-session
