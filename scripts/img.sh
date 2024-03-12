#!/bin/bash

for src in deblur_clear;
do
    for sfm in colmap;
    do
        python scripts/img.py \
        --src ${src} \
        --sfm ${sfm}
    done
done