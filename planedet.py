import os
import open3d as o3d
import numpy as np
from scipy.signal import find_peaks
from scipy.linalg import svd
from scipy.spatial.transform import Rotation as R
import math
import json
import copy
import matplotlib.pyplot as plt

def get_transfrom_pcd_with_json(pcd, json_path):
    with open(json_path, "r") as file:
        extrinsic_matrix_json = json.load(file)
    extrinsic_matrix = np.asarray(extrinsic_matrix_json["transform"])
    extrinsic_matrix = np.concatenate([extrinsic_matrix, np.array([[0., 0., 0., 1. / extrinsic_matrix_json["scale"]]])], 0)
    temp = extrinsic_matrix[1].copy()
    extrinsic_matrix[1] = extrinsic_matrix[2] * -1
    extrinsic_matrix[2] = temp
    pcd_transformed = copy.deepcopy(pcd)
    pcd_transformed.transform(extrinsic_matrix)
    return pcd_transformed

def get_plane_sample_point(points, init_point=True, bins=1000, coef_dist=1.5) -> np.ndarray:
    z_position = points[:, 2]
    min_z = z_position.min()
    max_z = z_position.max()
    histogram, edge = np.histogram(z_position, bins=bins)
    delta = (max_z - min_z) / bins
    if init_point:
        peaks, peak_info = find_peaks(histogram, height=histogram.sum() / bins, distance=math.sqrt(bins), width=1)
        z_plane_position = edge[peaks[0]]
        first_peak_width = peak_info["widths"][0]
        first_start = z_plane_position - int(first_peak_width * coef_dist) * delta
        first_end = z_plane_position + int(first_peak_width * coef_dist) * delta
    else:
        peaks, peak_info = find_peaks(histogram, height=histogram.sum() / bins, distance=math.sqrt(bins))
        z_plane_position = edge[peaks[0]]
        first_start = z_plane_position - int(2 * coef_dist) * delta
        first_end = z_plane_position + int(2 * coef_dist) * delta
        
    filtered_points = points[z_position <= first_end]
    filtered_points = filtered_points[filtered_points[:, 2] >= first_start]
    
    return filtered_points

def find_null_space(points):
    A = np.column_stack([points, np.ones(points.shape[0])])
    _, S, Vt = svd(A)
    null_space = Vt.T[:, S.argmin()]
    return null_space

def create_rotation_matrix(null_space):
    normalized_vector = null_space[0:3] / np.linalg.norm(null_space[0:3])
    z_axis = np.array([0, 0, 1])
    rotation_axis = np.cross(z_axis, normalized_vector)
    cosine_angle = np.dot(z_axis, normalized_vector) / (np.linalg.norm(z_axis) * np.linalg.norm(normalized_vector))
    rotation = R.from_rotvec(rotation_axis * -cosine_angle)
    rotation_matrix = rotation.as_matrix()
    return rotation_matrix

def get_transfrom_pcd_from_matrix(pcd, matrix):
    pcd.transform(matrix)
    return pcd

def save_plane_image(sample_points_list, null_space_list):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    x = np.linspace(-2, 2, 10)
    y = np.linspace(-2, 2, 10)
    x, y = np.meshgrid(x, y)
    for smaple_points, null_space in zip(sample_points_list, null_space_list):
        z = -(null_space[0] * x + null_space[1] * y + null_space[3]) / null_space[2]
        ax.plot_surface(x, y, z, alpha=0.5, rstride=100, cstride=100)
        ax.scatter(smaple_points[:, 0], smaple_points[:, 1], smaple_points[:, 2], label='Sampled Points')
        
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')
    ax.set_zlim3d([-2, 2])
    plt.grid(True)
    plt.savefig("debug_image.jpg")
    plt.close()
    
def main(args):
    pcd = o3d.io.read_point_cloud(args.sparse)
    pcd_transformed = get_transfrom_pcd_with_json(pcd, args.json)
    
    sampled_points_list = []
    null_space_list = []
    
    transformed_points = np.asarray(pcd_transformed.points)
    sampled_points = get_plane_sample_point(transformed_points)
    null_space = find_null_space(sampled_points)
    rotation_matrix = create_rotation_matrix(null_space)

    transform_matrix = np.row_stack((rotation_matrix, (0, 0, 0)))
    transform_matrix = np.column_stack((transform_matrix, (0, 0, 0, 1)))
    pcd_transformed.transform(transform_matrix)
    sampled_points_list.append(sampled_points)
    null_space_list.append(null_space)
    
    for _ in range(args.iteration - 1):
        transformed_points = np.asarray(pcd_transformed.points)
        sampled_points = get_plane_sample_point(transformed_points, init_point=False)
        null_space = find_null_space(sampled_points)
        rotation_matrix = create_rotation_matrix(null_space)

        transform_matrix = np.row_stack((rotation_matrix, (0, 0, 0)))
        transform_matrix = np.column_stack((transform_matrix, (0, 0, 0, 1)))
        pcd_transformed.transform(transform_matrix)
        
        sampled_points_list.append(sampled_points)
        null_space_list.append(null_space)
    
    if args.debug:
        save_plane_image(sampled_points_list, null_space_list)
    
    rotation_matrix = create_rotation_matrix(null_space_list[-1])
    transform_matrix = np.row_stack((rotation_matrix, (0, 0, 0)))
    transform_matrix = np.column_stack((transform_matrix, (0, 0, null_space_list[-1][3], 1)))
    
    if 'point' in args.dense:
        pcd_dense = o3d.io.read_point_cloud(args.dense)
    elif 'mesh' in args.dense:
        pcd_dense = o3d.io.read_triangle_mesh(args.dense)
    pcd_dense.transform(transform_matrix)
    
    with open(os.path.splitext(args.output)[0] + '.json', 'w', encoding='utf-8') as file:
        json.dump({'transform': transform_matrix.tolist()}, file)
    
    if 'point' in args.dense:
        o3d.io.write_point_cloud(args.output, pcd_dense, write_ascii=True)
    elif 'mesh' in args.dense:
        o3d.io.write_triangle_mesh(args.output, pcd_dense, write_ascii=True)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--sparse', type=str, default="output.ply")
    parser.add_argument('--dense', type=str, default="output.ply")
    parser.add_argument('--json', type=str, default="dataparser_transforms.json")
    parser.add_argument('--iteration', type=int, default=2)
    parser.add_argument('--output', type=str, default="result.ply")
    parser.add_argument('--debug', default=True, action='store_true')
    args = parser.parse_args()
    
    if args.iteration < 2:
        raise Exception("must be iteration >= 1 :<")
    
    main(args)