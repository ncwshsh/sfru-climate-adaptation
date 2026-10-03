#!/usr/bin/env bash
export PATH=/home/hugo/mamba/envs/sfru/bin:$PATH
echo "samtools: $(samtools --version 2>&1 | head -1)"
echo "bcftools: $(bcftools --version 2>&1 | head -1)"
echo "minimap2: $(minimap2 --version 2>&1)"
echo "bwa: $(bwa 2>&1 | grep -i version | head -1)"
echo "nproc: $(nproc)"
echo "mem: $(free -g | head -2 | tail -1)"
