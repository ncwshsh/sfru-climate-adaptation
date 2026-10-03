#!/bin/bash
echo "=== WSL out net ==="
timeout 15 curl -sI -A "Mozilla/5.0" https://github.com 2>&1 | head -2
echo "--- api ---"
timeout 15 curl -sI -A "Mozilla/5.0" https://api.github.com 2>&1 | head -2
echo "--- ncbi ftp ---"
timeout 15 curl -sI -A "Mozilla/5.0" https://ftp.ncbi.nlm.nih.gov 2>&1 | head -2
echo "=== apt ==="
which apt-get
echo "=== sra-tools? ==="
which fasterq-dump 2>/dev/null || echo "not installed"
echo "=== disk /mnt/c ==="
df -h /mnt/c 2>/dev/null | tail -1
