import argparse
import os
import time
from datetime import datetime, timedelta
import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import subprocess as sp
import sys
from loguru import logger

from google.cloud import storage
from google.oauth2 import service_account
from mysql.connector import Error
import mysql


def changeStatus(status, message, id, store_file_url = None, thumbnail_file_url = None, infer_start_time = None, infer_end_time = None):
    connection = None
    
    try:
        connection = mysql.connector.connect(
            host='34.64.80.157',
            database='ZZIMKONG',
            user='root',
            password='NewSt@rt!70'
        )

        if connection.is_connected():
            if(store_file_url == None and thumbnail_file_url == None):
                insert_query = f"UPDATE space_model_result SET status_code = '{status}', status_message = '{message}' WHERE message_id = {id};"
            elif(store_file_url != None):
                insert_query = f"UPDATE space_model_result SET status_code = '{status}', status_message = '{message}', store_file_url = '{store_file_url}' WHERE message_id = {id};"
            elif(thumbnail_file_url != None):
                insert_query = f"UPDATE space_model_result SET thumbnail_file_url = '{thumbnail_file_url}' WHERE message_id = {id};"
            elif(infer_start_time != None):
                insert_query = f"UPDATE space_model_result SET learned_date = '{infer_start_time}' WHERE message_id = {id};"
            elif(infer_end_time != None):
                insert_query = f"UPDATE space_model_result SET finished_date = '{infer_end_time}' WHERE message_id = {id};"
                
            cursor = connection.cursor()
            cursor.execute(insert_query)
            connection.commit()
            print("space_model_result 테이블에 메시지를 입력하였습니다.")

    except Error as e:
        print("MySQL에 연결되지 않았습니다.", e)

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL 연결을 끊었습니다.")


# 서비스 계정 인증 정보가 담긴 JSON 파일 경로
KEY_PATH = "./nerfstudio/key/local-turbine-417512-1d12c5c178e1.json"
# Credentials 객체 생성
credentials = service_account.Credentials.from_service_account_file(KEY_PATH)


def download_from_gcp(src, dest, file_name, bucket_name = "zzimkong-bucket"):
    # Google Cloud Storage 클라이언트 객체 생성
    storage_client = storage.Client(credentials = credentials, project = credentials.project_id)
    
    # 버킷 객체 생성
    bucket = storage_client.bucket(bucket_name)
    
    # Blob 객체 생성 -> 버킷의 파일명을 선택
    blob = bucket.blob("space/video/" + file_name)
    
    # 다운로드될 파일명
    blob.download_to_filename(os.path.join(dest, file_name +".mp4"))

    
def upload_ply(src, dest, bucket_name = "zzimkong-bucket"):
    """파일을 Google Cloud Storage 버킷에 업로드합니다."""
    
    try:
        storage_client = storage.Client(credentials = credentials, project = credentials.project_id)
        
        bucket = storage_client.bucket(bucket_name)
        
        # 이게 스토리지 명(space/ply/) + 저장될 파일 명
        blob = bucket.blob(f'space/ply/{dest}.ply')
        
        # 이게 로컬 파일
        blob.upload_from_filename(src)
        return 201
    except GoogleCloudError as e:
        return 500


def upload_thumb(src, dest, bucket_name = "zzimkong-bucket"):
    """파일을 Google Cloud Storage 버킷에 업로드합니다."""
    storage_client = storage.Client(credentials = credentials, project = credentials.project_id)
    
    bucket = storage_client.bucket(bucket_name)
    
    # 이게 스토리지 명(space/ply/) + 저장될 파일 명
    blob = bucket.blob(f'space/thumbnail/{dest}.png')
    
    # 이게 로컬 파일
    blob.upload_from_filename(src)


def save_log(args, log_dir):
    # mysql 연결
    connection = None
    try:
        connection = mysql.connector.connect(
            host='34.64.80.157',
            database='ZZIMKONG',
            user='root',
            password='NewSt@rt!70'
        )
    except Error as e:
        print("Log MySQL에 연결하는 동안 오류가 발생했습니다:", e)
        return None
    
    # 로그 추출
    all_texts = []
    with open(log_dir, 'r', encoding='utf-8') as file: # log 파일 경로
        for line in file:
            log_text = line.split('-')[-1].strip()
            all_texts.append(log_text)
    combined_text = '\n'.join(all_texts)
    
    # mysql에 저장    
    try:
        cursor = connection.cursor()
        query = "INSERT INTO space_log (message_id, text) VALUES (%s, %s)"
        cursor.execute(query, (args.id, combined_text)) # 메세지 id, 로그 텍스트
        connection.commit()
        print("로그 레코드가 성공적으로 저장되었습니다.")
        cursor.close()
        connection.close()
    except Error as e:
        print("log를 데이터베이스에 저장하는 도중 오류가 발생했습니다:", e)


def main(args):
    start = time.time()
    msg = '업로드 된 공간 영상을 전처리 중입니다. \n\
    (전처리에는 약 30분이 소요됩니다!)'    # user에게 보여줄 메시지
    changeStatus("PROCESSING", msg, args.id, infer_start_time=str(datetime.now()))

    base = os.getcwd()
    if 'nerfstudio' not in base:
        base = f'{base}/nerfstudio'    # pwd output. ./nerfstudio
    model = args.model                 # nerfacto

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

    # NOTE: ffmpeg에서 url 직접 사용 불가 / process_data_utils.py convert_video_to_images 참조
    # 영상 다운로드
    if not os.path.exists(f'{base}/data/{name}'):
        os.mkdir(f'{base}/data/{name}')
    download_from_gcp(src = data_url, dest = f'{base}/data/{name}', file_name = data)
    
    data_url = f'{base}/data/{name}/{data}.mp4'

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
        changeStatus("ERROR", "공간 영상 전처리 중 문제가 발생하였습니다.", args.id)
        save_log(args, f'{base}/data/{name}/{name}.log')
        command = f'chmod -R a+x {base}/data/{name} && rm -rf {base}/data/{name}'
        s = sp.run(command, capture_output=False, text=True, shell=True)
        os.abort()
    
    f = open(f'{base}/data/{name}/colmap_result.txt', 'r')
    line = f.readline()
    f.close()
    get_matching_summary = line.split(']')[-1]
    logger.info(f'공간 영상 전처리 결과: {get_matching_summary}')

    f = open(f'{base}/data/{name}/colmap_result.txt', 'a')
    f.write(f'Elapsed time: {elapsed_process}')
    f.close()

    if "all" in get_matching_summary:
        matching = float(100)
    else:
        matching = float(line.split('%')[0][-5:])
    # 매칭률 30% 미만일 경우 더 이상 진행 안 함
    MATCHING_THRES = 30
    if matching < float(MATCHING_THRES):
        msg = f'{get_matching_summary} \n\
        전처리 수행 결과 학습 가능한 프레임이 전체의 {MATCHING_THRES}% 미만으로 공간 재구성을 진행하기 어렵습니다. \n\
        상세 가이드를 읽고 촬영을 한번 더 시도해주세요. 촬영과 관련된 문의는 고지된 링크로 해주시면 감사하겠습니다.'
        changeStatus("ERROR", msg, args.id)
        save_log(args, f'{base}/data/{name}/{name}.log')
        command = f'chmod -R a+x {base}/data/{name} && rm -rf {base}/data/{name}'
        s = sp.run(command, capture_output=False, text=True, shell=True)
        os.abort()

    msg = f'{get_matching_summary} \n\
    전처리가 완료되어 공간 학습을 진행 중입니다. \n\
    (학습에는 약 30분이 소요됩니다!)'
    upload_thumb(
        src = f'{base}/data/{name}/images/frame_00001.png',
        dest = data
    )
    changeStatus("PROCESSING", msg, args.id, thumbnail_file_url = "space/thumbnail/" + data + ".png")

    # logging 학습
    start_train = time.time()
    # ns-train
    command = f'ns-train {model} --data {base}/data/{name} --output-dir {base}/outputs --pipeline.model.predict-normals True --vis tensorboard'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    elapsed_train = timedelta(seconds=time.time() - start_train)
    logger.info(f'공간 모델 학습에 {elapsed_train} 소요')
    
    outs_dir=f"{base}/outputs/{name}/{model}/"
    output_dir = outs_dir + sorted(os.listdir(outs_dir))[-1]

    if s.returncode != 0:
        changeStatus("ERROR", "공간 학습 중 문제가 발생하였습니다.", args.id)
        save_log(args, f'{base}/data/{name}/{name}.log')
        command = f'chmod -R a+x {base}/data/{name} && rm -rf {base}/data/{name} && chmod -R a+x {base}/outputs/{name} && rm -rf {base}/outputs/{name}'
        s = sp.run(command, capture_output=False, text=True, shell=True)
        os.abort()
    msg = '공간 학습이 완료되어 공간 재구성을 진행 중 입니다. \n\
    (재구성에는 약 10분이 소요됩니다!)'
    changeStatus("PROCESSING", msg, args.id)

    # logging 추출
    start_export = time.time()
    # ns-export
    command = f'ns-export poisson \
    --load-config {output_dir}/config.yml \
    --output-dir {output_dir}/exports/poisson_s_20/ \
    --save-point-cloud True \
    --texture-method point_cloud \
    --target-num-faces 1000000 \
    --num-pixels-per-side 2048 \
    --num-points 10000000 \
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
        changeStatus("ERROR", "공간 재구성 중 문제가 발생하였습니다.", args.id)
        save_log(args, f'{base}/data/{name}/{name}.log')
        command = f'chmod -R a+x {base}/data/{name} && rm -rf {base}/data/{name} && chmod -R a+x {base}/outputs/{name} && rm -rf {base}/outputs/{name}'
        s = sp.run(command, capture_output=False, text=True, shell=True)
        os.abort()

    print("Point cloud exported!")
    print(f"Elapsed time: {timedelta(seconds=time.time() - start)}")
    logger.info(f'전체 소요 시간: {timedelta(seconds=time.time() - start)}')
    save_log(args, f'{base}/data/{name}/{name}.log')

    # # pcd
    # command = f'python nerfstudio/planedet.py \
    # --sparse {base}/data/{name}/sparse_pc.ply \
    # --dense {output_dir}/exports/poisson_s_20/point_cloud.ply \
    # --json {output_dir}/dataparser_transforms.json \
    # --output {output_dir}/exports/poisson_s_20/point_cloud_det.ply'
    # mesh
    command = f'python nerfstudio/planedet.py \
    --sparse {base}/data/{name}/sparse_pc.ply \
    --dense {output_dir}/exports/poisson_s_20/poisson_mesh_d_10.ply \
    --json {output_dir}/dataparser_transforms.json \
    --output {output_dir}/exports/poisson_s_20/poisson_det.ply'
    s = sp.run(command, capture_output=False, text=True, shell=True)
    if s.returncode != 0:
        changeStatus("ERROR", "공간 재구성 중 문제가 발생하였습니다.", args.id)
        command = f'chmod -R a+x {base}/data/{name} && rm -rf {base}/data/{name} && chmod -R a+x {base}/outputs/{name} && rm -rf {base}/outputs/{name}'
        s = sp.run(command, capture_output=False, text=True, shell=True)
        os.abort()

    msg = '공간 재구성이 완료되었습니다! 재구성 결과를 서버에 업로드 중입니다.'
    changeStatus("PROCESSING", msg, args.id)

    print("web server로 전송 중")
    send_start = time.time()

    # # pcd
    # result = upload_ply(
    #     src = f'{output_dir}/exports/poisson_s_20/point_cloud_det.ply',
    #     dest = data
    # )
    # #
    # mesh
    result = upload_ply(
        src = f'{output_dir}/exports/poisson_s_20/poisson_det.ply',
        dest = data
    )
    #

    if result == 201:
        print(f"전송 완료. Elapsed time: {timedelta(seconds=time.time() - send_start)}")
        changeStatus("PROCESSING", "업로드가 완료되었습니다.", args.id, store_file_url = "space/ply/" + data + ".ply")
        command = f'chmod -R a+x {base}/data/{name} && rm -rf {base}/data/{name} && chmod -R a+x {base}/outputs/{name} && rm -rf {base}/outputs/{name}'
        s = sp.run(command, capture_output=False, text=True, shell=True)
    else:
        changeStatus("ERROR", "재구성 결과 업로드 중 문제가 발생하였습니다.", args.id)
        command = f'chmod -R a+x {base}/data/{name} && rm -rf {base}/data/{name} && chmod -R a+x {base}/outputs/{name} && rm -rf {base}/outputs/{name}'
        s = sp.run(command, capture_output=False, text=True, shell=True)
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
    parser.add_argument('--sfm',
                        type=str, 
                        help='sfm.',
                        default="colmap")

    # Parse arguments
    args = parser.parse_args()
    config = json.loads(args.config_file) # dict

    args.id = config["id"]
    args.src = config["src"]
    print(args)
    main(args)
