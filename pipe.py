import argparse
import os
import time
from datetime import timedelta
import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import json
import subprocess as sp
import sys


def send(name, file, id):
    url = "https://zzimkong.ggm.kr/inference/upload"
    ply_file = MultipartEncoder(
        fields={
            'file': (f'{name}.ply', open(file, 'rb'))
        }
    )
    data = {"file": ply_file, "id": id}
    r = requests.post(url, data=data, verify=False)
    return r.status_code


def status(status, message, id):
    url = "https://zzimkong.ggm.kr/inference/status"
    data = {"status": status, "statusMessage": message, "id": id}
    r = requests.post(url, data=data, verify=False)

def main(args):
    start = time.time()
    msg = '공간 영상 전처리 수행 중 \
        약 30분이 소요됩니다.'    # user에게 보여줄 메시지
    status("progress", msg, args.id)

    base = os.getcwd()
    if 'nerfstudio' not in base:
        base = f'{base}/nerfstudio'    # pwd output. ./nerfstudio
    model = args.model                 # nerfacto

    # src로 url 들어올 시
    # if "https:" in args.src:
    #     data_url = args.src                # https://zzimkong.ggm.kr/2024.mov
    #     data = data_url.split('/')[-1]     # room.mp4
    #     name_0 = data.split('.')[0]        # room
    # else:
    #     data = args.src
    #     data_url = f'{base}/data/{data}'
    #     name_0 = data.split('.')[0]

    # UXR까지는 src로 url이 아닌 파일명만
    data_url = f'https://zzimkong.ggm.kr/{args.src}'                # https://zzimkong.ggm.kr/2024.mov
    data = data_url.split('/')[-1]                                  # room.mp4
    name_0 = data.split('.')[0]                                     # room

    name = name_0
    # 폴더명 중복 피하기
    uniq = 1
    while os.path.exists(f'{base}/data/{name}'):
        name = f'{name_0}{str(uniq)}'
        uniq += 1

    # ns-process-data
    command = f'source activate nerfstudio && ns-process-data video --data {data_url} --output-dir {base}/data/{name}'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    if s.returncode != 0:
        status("error", "데이터 전처리 중 에러가 발생하였습니다.", args.id)
        os.abort()
    # TODO os.popen(f'source activate nerfstudio && ns-process-data video --data {base}/data/{data} --output-dir {base}/data/{name}')
    get_matching_summary = ''   # TODO process-data에서 출력이나 flag 받아와야 함
    msg = f'{get_matching_summary} \
        공간 모델 학습 수행 중 \
        약 30분이 소요됩니다.'
    status("progress", msg, args.id)

    # ns-train
    command = f'source activate nerfstudio && ns-train {model} --data {base}/data/{name} --output-dir {base}/outputs --pipeline.model.predict-normals True --vis wandb'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    if s.returncode != 0:
        status("error", "공간 모델 학습 중 에러가 발생하였습니다.", args.id)
        os.abort()
    msg = '3차원 공간 추출 중 \
        약 10분이 소요됩니다.'
    status("progress", msg, args.id)

    outs_dir=f"{base}/outputs/{name}/{model}/"
    output_dir = outs_dir + sorted(os.listdir(outs_dir))[-1]

    # ns-export
    command = f'source activate nerfstudio && ns-export pointcloud \
    --load-config {output_dir}/config.yml \
    --output-dir {output_dir}/exports/pcd_10000000_s_20/ \
    --num-points 10000000 \
    --remove-outliers True \
    --normal-method open3d \
    --use_bounding_box True \
    --save-world-frame False \
    --obb_center 0.0000000000 0.0000000000 0.0000000000 \
    --obb_rotation 0.0000000000 0.0000000000 0.0000000000 \
    --obb_scale 20.0000000000 20.0000000000 20.0000000000'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    if s.returncode != 0:
        status("error", "공간 추출 중 에러가 발생하였습니다.", args.id)
        os.abort()

    print("Point cloud exported!")
    print(f"Elapsed time: {timedelta(seconds=time.time() - start)}")

    msg = '공간 추출이 완료되었습니다!'
    status("progress", msg, args.id)

    print("web server로 전송 중")
    send_start = time.time()
    result = send(name, f'{output_dir}/exports/pcd_10000000_s_20/point_cloud.ply', args.id)
    if result == 201:
        print(f"전송 완료. Elapsed time: {timedelta(seconds=time.time() - send_start)}")
        status("progress", "ply 전송이 완료되었습니다.", args.id)
    else:
        status("error", "ply 전송에 실패하였습니다.", args.id)


if __name__ == "__main__":
    # ----- Parser -----
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-dc',
        '--config_file',
        dest='config_file',
        type=str,
        default='',
        help='config file',
    )
    parser.add_argument('--id',
                        type=int, 
                        help='(Required) id.')
    parser.add_argument('--src',
                        type=str, 
                        help='(Required) user data name.')
    parser.add_argument('--model',
                        type=str, 
                        help='(Required) model.',
                        default="nerfacto")

    # Parse arguments
    args = parser.parse_args()
    config = json.loads(args.config_file) # dict

    args.id = config["id"]
    args.src = config["src"]
    print(args)
    main(args)