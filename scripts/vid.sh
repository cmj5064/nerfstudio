#!/bin/bash
type=url

# # 쇼룸, 민지방, 수민방, 조명, 
# for src in 1709188970613.mp4 1709190480556.mp4 1709182881023.mov 1709193779304.mov 1709803509092.mp4 1709803553327.mp4;
for src in 1709803509092.mp4 1709803553327.mp4;
do
    for sfm in hloc;
    do
        python scripts/vid.py \
        --type ${type} \
        --src ${src} \
        --sfm ${sfm}
    done
done