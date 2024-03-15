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
from loguru import logger


def main(args):
    start = time.time()

    base = os.getcwd()
    if 'nerfstudio' not in base:
        base = f'{base}/nerfstudio'    # pwd output. ./nerfstudio
    model = args.model                 # nerfacto

    if args.type == 'url':
        data_url = f'https://zzimkong.ggm.kr/inference/{args.src}'                # https://zzimkong.ggm.kr/2024.mov
        data = data_url.split('/')[-1]                                  # room.mp4
        name_0 = data.split('.')[0]                                     # room
    elif args.type == 'mp4':
        data_url = args.src         # room.mp4
        data = data_url             # room.mp4
        name_0 = data.split('.')[0] # room

    name = name_0
    # 폴더명 중복 피하기
    uniq = 1
    while os.path.exists(f'{base}/data/{name}'):
        name = f'{name_0}{str(uniq)}'
        uniq += 1

    if not os.path.exists(f'{base}/data/{name}'):
        os.mkdir(f'{base}/data/{name}')
    
    if args.type == 'url':
        with open(f'{base}/data/{name}/{data}', "wb") as file:   # open in binary mode
            headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiYWRtaW4iLCJpYXQiOjE3MDkwMTE5NDIsImV4cCI6MTcxNzY1MTk0Mn0.GDqzeLFwWziLvFzRPNJ0AsJiy4l2UwzAy74Cg27wY5A"}
            response = requests.get(data_url, headers=headers)               # get request
            file.write(response.content)      # write to file#
    
    data_url = f'{base}/data/{name}/{data}'
    # logging init 설정
    logger.add(f'{base}/data/{name}/{name}.log')

    # logging 전처리
    start_process = time.time()
    # ns-process-data
    if args.sfm == 'colmap':
        command = f'ns-process-data video --data {data_url} --output-dir {base}/data/{name}'
    elif args.sfm == 'hloc':
        command = f'ns-process-data video --data {data_url} --output-dir {base}/data/{name} --sfm-tool hloc --feature-type superpoint_aachen --matcher-type superglue'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    elapsed_process = timedelta(seconds=time.time() - start_process)
    logger.info(f'공간 영상 전처리에 {elapsed_process} 소요')
    if s.returncode != 0:
        os.abort()
    
    f = open(f'{base}/data/{name}/colmap_result.txt', 'r')
    line = f.readline()
    f.close()
    get_matching_summary = line.split(']')[-1]
    logger.info(f'공간 영상 전처리 결과 \n\
    {get_matching_summary}')

    f = open(f'{base}/data/{name}/colmap_result.txt', 'a')
    f.write(f'Elapsed time: {elapsed_process}')
    f.close()

    # logging 학습
    start_train = time.time()
    # ns-train
    command = f'ns-train {model} --data {base}/data/{name} --output-dir {base}/outputs --pipeline.model.predict-normals True --vis wandb'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    elapsed_train = timedelta(seconds=time.time() - start_train)
    logger.info(f'공간 모델 학습에 {elapsed_train} 소요')
    if s.returncode != 0:
        os.abort()

    outs_dir=f"{base}/outputs/{name}/{model}/"
    output_dir = outs_dir + sorted(os.listdir(outs_dir))[-1]

    # logging 추출
    start_export = time.time()
    # ns-export
    command = f'ns-export poisson \
    --load-config {output_dir}/config.yml \
    --output-dir {output_dir}/exports/poisson_s_20/ \
    --save-point-cloud True \
    --texture-method point_cloud \
    --target-num-faces 2000000 \
    --num-pixels-per-side 2048 \
    --num-points 5000000 \
    --remove-outliers True \
    --normal-method open3d \
    --use_bounding_box True \
    --obb_center 0.0000000000 0.0000000000 0.0000000000 \
    --obb_rotation 0.0000000000 0.0000000000 0.0000000000 \
    --obb_scale 20.0000000000 20.0000000000 20.0000000000'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    elapsed_export = timedelta(seconds=time.time() - start_export)
    logger.info(f'공간 재구성 결과 추출에 {elapsed_export} 소요')
    if s.returncode != 0:
        os.abort()

    print("Point cloud exported!")
    print(f"Elapsed time: {timedelta(seconds=time.time() - start)}")
    logger.info(f'전체 소요 시간: {timedelta(seconds=time.time() - start)}')


if __name__ == "__main__":
    # ----- Parser -----
    parser = argparse.ArgumentParser()
    parser.add_argument('--type',
                        type=str, 
                        help='(Required) user data. mp4 or url')
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