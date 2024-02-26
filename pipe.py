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


def thumbnail(name, file, id):
    url = "https://zzimkong.ggm.kr/inference/upload/thumbnail"
    png_file = MultipartEncoder(
        fields={
            'file': (f'{name}.png', open(file, 'rb')),
            'id': str(id)
        }
    )
    headers = {'Content-Type' : png_file.content_type}              # multipart/form-data
    r = requests.post(url, headers=headers, data=png_file, verify=False)
    return r.status_code


def status(status, message, id):
    url = "https://zzimkong.ggm.kr/inference/status"
    data = {"status": status, "statusMessage": message, "id": id}
    r = requests.post(url, data=data, verify=False)

def main(args):
    start = time.time()
    msg = '업로드 된 공간 영상을 전처리 중입니다. \n\
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
    data_url = f'https://zzimkong.ggm.kr/inference/{args.src}'                # https://zzimkong.ggm.kr/2024.mov
    data = data_url.split('/')[-1]                                  # room.mp4
    name_0 = data.split('.')[0]                                     # room

    name = name_0
    # 폴더명 중복 피하기
    uniq = 1
    while os.path.exists(f'{base}/data/{name}'):
        name = f'{name_0}{str(uniq)}'
        uniq += 1

    # TODO: ffmpeg pix_fmt none이라 url 사용 불가 / process_data_utils.py convert_video_to_images
    # wget
    if not os.path.exists(f'{base}/data/{name}'):
        os.mkdir(f'{base}/data/{name}')
    wget.download(data_url, f'{base}/data/{name}/{data}')
    data_url = f'{base}/data/{name}/{data}'
    # ns-process-data
    command = f'source activate nerfstudio && ns-process-data video --data {data_url} --output-dir {base}/data/{name}'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    if s.returncode != 0:
        status("error", "공간 영상 전처리 중 문제가 발생하였습니다.", args.id)
        os.abort()
    
    f = open(f'{base}/data/{name}/colmap_result.txt', 'r')
    line = f.readline()
    f.close()
    get_matching_summary = line.split(']')[-1]
    if "all" in get_matching_summary:
        matching = float(100)
    else:
        matching = float(line.split('%')[0][-5:])
    # 매칭률 50% 미만일 경우 더 이상 진행 안 함
    if matching < float(50):
        msg = f'{get_matching_summary} \n\
        전처리 수행 결과 학습 가능한 프레임이 전체의 50% 미만으로 공간 재구성을 진행하기 어렵습니다. \n\
        상세 가이드를 읽고 촬영을 한번 더 시도해주세요. 촬영과 관련된 문의는 고지된 링크로 해주시면 감사하겠습니다.'
        status("error", msg, args.id)
        os.abort()

    msg = f'{get_matching_summary} \n\
    전처리가 완료되어 공간 학습을 진행 중입니다. \n\
    (학습에는 약 30분이 소요됩니다!)'
    status("progress", msg, args.id)

    thumbnail(name, f'{base}/data/{name}/images/frame_00001.png', args.id)

    # ns-train
    command = f'source activate nerfstudio && ns-train {model} --data {base}/data/{name} --output-dir {base}/outputs --pipeline.model.predict-normals True --vis wandb'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    if s.returncode != 0:
        status("error", "공간 학습 중 문제가 발생하였습니다.", args.id)
        os.abort()
    msg = '공간 학습이 완료되어 공간 재구성을 진행 중 입니다. \n\
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