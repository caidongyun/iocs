#!/bin/bash
# IOC Sync 快捷脚本
# 使用方法: ./sync.sh "commit message"

cd "$(dirname "$0")"

if [ "$1" == "--init" ]; then
    python src/ioc_sync.py --path . --init
elif [ "$1" == "--status" ]; then
    python src/ioc_sync.py --path . --status
else
    python src/ioc_sync.py --path . --message "$1"
fi
