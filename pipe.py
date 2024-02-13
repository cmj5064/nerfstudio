import argparse
import os
import time
from datetime import timedelta
import json


def main(args):
    start = time.time()
    msg = '공간 영상 전처리 수행 중 \
        약 30분이 소요됩니다.'    # user에게 보여줄 메시지
    # TODO 웹 서버로 msg 전송

    base = os.getcwd()                 # pwd output. ./nerfstudio
    model = args.model                 # nerfacto
    data = args.data                   # room.mp4 saved in {base}/data
    name_0 = data.split('.')[0]        # room

    name = name_0
    # 폴더명 중복 피하기
    uniq = 1
    while os.path.exists(f'{base}/data/{name}'):
        name = f'{name_0}{str(uniq)}'
        uniq += 1

    # ns-process-data
    os.system(f'ns-process-data video --data {base}/data/{data} --output-dir {base}/data/{name}')
    # TODO os.popopen(f'ns-process-data video --data {base}/data/{data} --output-dir {base}/data/{name}')
    get_matching_summary = ''   # TODO process-data에서 출력이나 flag 받아와야 함
    msg = f'{get_matching_summary} \
        공간 모델 학습 수행 중 \
        약 30분이 소요됩니다.'
    # TODO 웹 서버로 msg 전송

    # ns-train
    os.system(f'ns-train {model} --data {base}/data/{name} --pipeline.model.predict-normals True --vis wandb')
    msg = '3차원 공간 추출 중 \
        약 10분이 소요됩니다.'
    # TODO 웹 서버로 msg 전송

    outs_dir=f"{base}/outputs/{name}/{model}/"
    output_dir = outs_dir + sorted(os.listdir(outs_dir))[-1]

    # ns-export
    os.system(f'ns-export pointcloud \
    --load-config {output_dir}/config.yml \
    --output-dir {output_dir}/exports/pcd_10000000_s_20/ \
    --num-points 10000000 \
    --remove-outliers True \
    --normal-method open3d \
    --use_bounding_box True \
    --save-world-frame False \
    --obb_center 0.0000000000 0.0000000000 0.0000000000 \
    --obb_rotation 0.0000000000 0.0000000000 0.0000000000 \
    --obb_scale 20.0000000000 20.0000000000 20.0000000000')

    print("Point cloud exported!")
    print(f"Elapsed time: {timedelta(seconds=time.time() - start)}")

    msg = '공간 추출이 완료되었습니다!'
    # TODO 웹 서버로 msg 전송


if __name__ == "__main__":
    # ----- Parser -----
    cli_parser = argparse.ArgumentParser(
        description='configuration arguments provided at run time from the CLI'
    )

    cli_parser.add_argument(
        '-c',
        '--config_file',
        dest='config_file',
        type=str,
        default='./config.json',
        help='config file',
    )

    args, unknown = cli_parser.parse_known_args()

    # parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(parents=[cli_parser], add_help=False)

    parser.add_argument('--data',
                        type=str, 
                        help='(Required) user data name.',
                        default="room3.mp4")
    parser.add_argument('--model',
                        type=str, 
                        help='(Required) model.',
                        default="nerfacto")

    # The escaping of "\t" in the config file is necesarry as
    # otherwise Python will try to treat is as the string escape
    # sequence for ASCII Horizontal Tab when it encounters it
    # during json.load
    config = json.load(open(args.config_file))
    parser.set_defaults(**config)

    [
        parser.add_argument(arg)
        for arg in [arg for arg in unknown if arg.startswith('--')]
        if arg.split('--')[-1] in config
    ]

    # Parse arguments
    args = parser.parse_args()
    print(args)
    main(args)