#!/bin/bash
base=/workspace/nerfstudio
name=gallery    # gallery.mp4
# data=room
model=nerfacto

DATA_ROOT=/workspace/nerfstudio/data/data/
# SCENE_ID=036bce3393
SCENE_ID=be66c57b92

# ns-train nerfacto \
#      --max_num_iterations 100000 \P
#      --pipeline.datamanager.train_num_rays_per_batch 8192 \
#      --pipeline.datamanager.train_num_images_to_sample_from 400 \
#      --pipeline.datamanager.train_num_times_to_repeat_images 100 \
#      --vis viewer+tensorboard \
#      scannetpp-data \
#      --data ${DATA_ROOT} \
#      --scene-id ${SCENE_ID} \
#      --scene_scale 1.5

    #  --pipeline.datamanager.train_num_images_to_sample_from 400 \
    #  --pipeline.datamanager.train_num_times_to_repeat_images 100 \
    #  --pipeline.datamanager.images-on-gpu True \
    #  --pipeline.datamanager.max-thread-workers 24 \
    #  --pipeline.datamanager.num-processes 2 \
####################################################################

ns-process-data video \
    --data ${base}/data/${name}.mp4 \
    --output-dir ${base}/data/${name}3
    # --sfm-tool hloc \
    # --feature-type superpoint_aachen \
    # --matcher-type superglue

# ns-train nerfacto \
#      --data ${base}/data/${name}2 \
#      --output-dir ${base}/outputs \
#      --pipeline.model.predict-normals True \
#      --vis wandb

# ns-train nerfacto \
#      --pipeline.datamanager.images-on-gpu True \
#      --pipeline.model.camera-optimizer.mode off \
#      --pipeline.model.predict-normals True \
#      --vis wandb \
#      --output-dir ${base}/outputs \
#      --experiment-name ${SCENE_ID} \
#      scannetpp-data \
#      --data ${DATA_ROOT}/${SCENE_ID} \
#      --scene_scale 1.0

# outs_dir="${base}/outputs/${SCENE_ID}/${model}/*"
# LIST=()

# for l in $(ls -d ${outs_dir});
# do
#     LIST+=(${l})

# done

# output_dir=${LIST[-1]}
output_dir=/workspace/nerfstudio/outputs/gallery2/nerfacto/2024-03-04_162829/

# ns-export

# ns-export pointcloud \
# --load-config ${output_dir}/config.yml \
# --output-dir ${output_dir}/exports/pcd_10000000_s_3/ \
# --num-points 10000000 \
# --remove-outliers True \
# --normal-method open3d \
# --use_bounding_box True \
# --save-world-frame False \
# --obb_center 0.0000000000 0.0000000000 0.0000000000 \
# --obb_rotation 0.0000000000 0.0000000000 0.0000000000 \
# --obb_scale 3.0000000000 3.0000000000 3.0000000000

# ns-export tsdf \
# --load-config ${output_dir}/config.yml \
# --output-dir ${output_dir}/exports/tsdf_10000000_1000000_s_3/ \
# --resolution 256 256 256 \
# --batch-size 1 \
# --target-num-faces 1000000 \
# --num-pixels-per-side 2048 \
# --use_bounding_box True

# ns-export poisson \
# --load-config ${output_dir}/config.yml \
# --output-dir ${output_dir}/exports/poisson_s_5/ \
# --save-point-cloud True \
# --texture-method point_cloud \
# --target-num-faces 5000000 \
# --num-pixels-per-side 2048 \
# --num-points 10000000 \
# --remove-outliers True \
# --normal-method open3d \
# --use_bounding_box True \
# --obb_center 0.0000000000 0.0000000000 0.0000000000 \
# --obb_rotation 0.0000000000 0.0000000000 0.0000000000 \
# --obb_scale 5.0000000000 5.0000000000 5.0000000000

############################################################

# output_dir=/workspace/nerfstudio/data

# ns-export poisson-pcd \
# --pcd-dir ${output_dir}/gallery.ply \
# --output-dir ${output_dir}/ \
# --save-point-cloud True \
# --texture-method point_cloud \
# --target-num-faces 5000000 \
# --num-pixels-per-side 2048 \
# --num-points 10000000 \
# --remove-outliers True \
# --normal-method open3d \
# --use_bounding_box True \
# --obb_center 0.0000000000 0.0000000000 0.0000000000 \
# --obb_rotation 0.0000000000 0.0000000000 0.0000000000 \
# --obb_scale 10.0000000000 10.0000000000 10.0000000000