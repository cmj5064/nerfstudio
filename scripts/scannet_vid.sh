#!/bin/bash
type=mp4

# scannet scenes
# nvs_test
# for src in beb802368c ca0e09014e ebff4de90b d228e2d9dd 9e019d8be1 11b696efba 471cc4ba84 f20e7b5640 18fd041970;
# nvs_sem_val
# for src in 7b6477cb95 c50d2d1d42 cc5237fd77 acd95847c5 fb5a96b1a2 a24f64f7fb 1ada7a0617 5eb31827b7 3e8bba0176 3f15a9266d 21d970d8de 5748ce6f01 c4c04e6d6c 7831862f02 bde1e479ad 38d58a7a31 5ee7c22ba0 f9f95681fd 3864514494;
for src in bde1e479ad 38d58a7a31 5ee7c22ba0 f9f95681fd 3864514494;
do
    for sfm in hloc colmap;
    do
        python scripts/scannet_vid.py \
        --type ${type} \
        --src ${src} \
        --sfm ${sfm}
    done
done