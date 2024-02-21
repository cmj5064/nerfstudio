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


def upload(name, file, id):
    url = "https://zzimkong.ggm.kr/inference/upload"
    ply_file = MultipartEncoder(
        fields={
            'file': (f'{name}.ply', open(file, 'rb')),
            'id': str(id)
        }
    )
    headers = {'Content-Type' : ply_file.content_type}              # multipart/form-data
    r = requests.post(url, headers=headers, data=ply_file, verify=False)
    return r.status_code


def status(status, message, id):
    url = "https://zzimkong.ggm.kr/inference/status"
    data = {"status": status, "statusMessage": message, "id": id}
    r = requests.post(url, data=data, verify=False)

def main(args):
    start = time.time()
    msg = '업로드 된 공간 영상을 전처리 중입니다. \
        (전처리에는 약 30분이 소요됩니다!)'    # user에게 보여줄 메시지
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
        status("error", "공간 영상 전처리 중 문제가 발생하였습니다.", args.id)
        os.abort()
    # TODO os.popen(f'source activate nerfstudio && ns-process-data video --data {base}/data/{data} --output-dir {base}/data/{name}')
    get_matching_summary = ''   # TODO process-data에서 출력이나 flag 받아와야 함
    msg = f'{get_matching_summary} \
        공간 학습을 진행 중입니다. \
        (학습에는 약 30분이 소요됩니다!)'
    status("progress", msg, args.id)

    # ns-train
    command = f'source activate nerfstudio && ns-train {model} --data {base}/data/{name} --output-dir {base}/outputs --pipeline.model.predict-normals True --vis wandb'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    if s.returncode != 0:
        status("error", "공간 학습 중 문제가 발생하였습니다.", args.id)
        os.abort()
    msg = '공간 학습이 완료되어 공간 재구성을 진행 중 입니다. \
        (재구성에는 약 10분이 소요됩니다!)'
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
        status("error", "공간 재구성 중 문제가 발생하였습니다.", args.id)
        os.abort()

    print("Point cloud exported!")
    print(f"Elapsed time: {timedelta(seconds=time.time() - start)}")

    msg = '공간 재구성이 완료되었습니다! 재구성 결과를 서버에 업로드 중입니다.'
    status("progress", msg, args.id)

    print("web server로 전송 중")
    send_start = time.time()
    result = upload(name, f'{output_dir}/exports/pcd_10000000_s_20/point_cloud.ply', args.id)
    if result == 201:
        print(f"전송 완료. Elapsed time: {timedelta(seconds=time.time() - send_start)}")
        status("progress", "업로드가 완료되었습니다.", args.id)
    else:
        status("error", "재구성 결과 업로드 중 문제가 발생하였습니다.", args.id)
        os.abort()


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