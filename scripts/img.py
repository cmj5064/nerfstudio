import argparse
import os
import time
from datetime import timedelta
import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import subprocess as sp
import sys
import wget



def main(args):
    start = time.time()

    base = os.getcwd()
    if 'nerfstudio' not in base:
        base = f'{base}/nerfstudio'    # pwd output. ./nerfstudio
    model = args.model                 # nerfacto

    data = args.src             # room
    name = data                 # room
    
    data_url = f'{base}/data/{name}/imgs'
    start_process = time.time()
    # ns-process-data
    if args.sfm == 'colmap':
        command = f'ns-process-data images --data {data_url} --output-dir {base}/data/{name}'
    elif args.sfm == 'hloc':
        command = f'ns-process-data video --data {data_url} --output-dir {base}/data/{name} --sfm-tool hloc --refine-pixsfm --feature-type disk --matcher-type disk+lightglue'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    if s.returncode != 0:
        os.abort()
    
    f = open(f'{base}/data/{name}/colmap_result.txt', 'a')
    f.write(f'Elapsed time: {timedelta(seconds=time.time() - start_process)}')
    f.close()

    # ns-train
    command = f'ns-train {model} --data {base}/data/{name} --output-dir {base}/outputs --pipeline.model.predict-normals True --vis wandb'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    if s.returncode != 0:
        os.abort()

    outs_dir=f"{base}/outputs/{name}/{model}/"
    output_dir = outs_dir + sorted(os.listdir(outs_dir))[-1]

    # ns-export
    command = f'ns-export poisson \
    --load-config {output_dir}/config.yml \
    --output-dir {output_dir}/exports/poisson_s_10/ \
    --save-point-cloud True \
    --texture-method point_cloud \
    --target-num-faces 5000000 \
    --num-pixels-per-side 2048 \
    --num-points 10000000 \
    --remove-outliers True \
    --normal-method open3d \
    --use_bounding_box True \
    --obb_center 0.0000000000 0.0000000000 0.0000000000 \
    --obb_rotation 0.0000000000 0.0000000000 0.0000000000 \
    --obb_scale 10.0000000000 10.0000000000 10.0000000000'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    if s.returncode != 0:
        os.abort()

    print("Point cloud exported!")
    print(f"Elapsed time: {timedelta(seconds=time.time() - start)}")


if __name__ == "__main__":
    # ----- Parser -----
    parser = argparse.ArgumentParser()
    parser.add_argument('--src',
                        type=str, 
                        help='(Required) user data name.')
    parser.add_argument('--model',
                        type=str, 
                        help='model.',
                        default="nerfacto")
    parser.add_argument('--sfm',
                        type=str, 
                        help='sfm.',
                        default="colmap")

    # Parse arguments
    args = parser.parse_args()
    print(args)
    main(args)