#!/bin/bash
base="/home/cmj.gcp.2/nerfstudio"
# data=room
model=nerfacto

for data in counter room kitchen;
do
    # ns-train
    # ns-train ${model} --data /home/cmj.gcp.2/nerfstudio/data/${data} --pipeline.model.predict-normals True --vis wandb

    outs_dir="${base}/outputs/${data}/${model}/*"
    LIST=()

    for l in $(ls -d ${outs_dir});
    do
        LIST+=(${l})

    done

    output_dir=${LIST[-1]}

    # ns-export
    ns-export pointcloud \
    --load-config ${output_dir}/config.yml \
    --output-dir ${output_dir}/exports/pcd_10000000_s_20/ \
    --num-points 10000000 \
    --remove-outliers True \
    --normal-method open3d \
    --use_bounding_box True \
    --save-world-frame True \
    --obb_center 0.0000000000 0.0000000000 0.0000000000 \
    --obb_rotation 0.0000000000 0.0000000000 0.0000000000 \
    --obb_scale 20.0000000000 20.0000000000 20.0000000000
done