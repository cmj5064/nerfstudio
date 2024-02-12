import argparse
import os

def main(args):
    base = os.getcwd()      # pwd output. ./nerfstudio
    model=args.model        # nerfacto
    data=args.data          # room.mp4
    name=data.split('.')[0] # room

    # ns-processd-data
    os.system(f'ns-process-data video --data {base}/data/{data} --output-dir {base}/data/{name}')

    # ns-train
    os.system(f'ns-train {model} --data {base}/data/{name} --pipeline.model.predict-normals True --vis wandb') # TODO wandb out

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
    --save-world-frame True \
    --obb_center 0.0000000000 0.0000000000 0.0000000000 \
    --obb_rotation 0.0000000000 0.0000000000 0.0000000000 \
    --obb_scale 20.0000000000 20.0000000000 20.0000000000')

    print("Point cloud exported!")

if __name__ == "__main__":
    # ----- Parser -----
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--data',
                        type=str, 
                        help='(Required) user data name.',
                        default="room.mp4")
    parser.add_argument('--model',
                        type=str, 
                        help='(Required) model.',
                        default="nerfacto")

    # Parse arguments
    args = parser.parse_args()
    main(args)