import numpy as np
import open3d as o3d


pcd = o3d.io.read_point_cloud("/workspace/nerfstudio/data/gallery.ply", remove_nan_points=True, remove_infinite_points=True, print_progress=True)
print('run Poisson surface reconstruction')
with o3d.utility.VerbosityContextManager(
        o3d.utility.VerbosityLevel.Debug) as cm:
    poisson_mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=10, linear_fit=False)
bbox = pcd.get_axis_aligned_bounding_box()
print(bbox)
p_mesh_crop = poisson_mesh.crop(bbox)

# o3d.visualization.draw_geometries([poisson_mesh]) 
o3d.io.write_triangle_mesh("/workspace/nerfstudio/data/gallery_d_10_s_10_no_linear.ply", p_mesh_crop)