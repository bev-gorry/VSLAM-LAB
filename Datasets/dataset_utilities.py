import os
import cv2
import numpy as np
from tqdm import tqdm

def load_rgb_txt(rgb_txt):
    with open(rgb_txt, 'r') as file:
        lines = file.readlines()
        columns = len(lines[0].strip().split(' '))

        rgb_paths = []
        rgb_timestamps = []

        if columns == 2: # rgb_timestamp rgb_path
            for line in lines:
                rgb_timestamp, rgb_path = line.strip().split(' ')
                rgb_paths.append(rgb_path)
                rgb_timestamps.append(rgb_timestamp)
            return rgb_paths, rgb_timestamps
        
        if columns == 4: # rgb_timestamp rgb_path depth_timestamp depth_path
            depth_paths = []
            depth_timestamps = []
            for line in lines:
                rgb_timestamp, rgb, depth_timestamp, depth_path, = line.strip().split(' ')
                rgb_paths.append(rgb)
                rgb_timestamps.append(rgb_timestamp)
                depth_paths.append(depth_path)
                depth_timestamps.append(depth_timestamp)
            return rgb_paths, rgb_timestamps, depth_paths, depth_timestamps
        
        if columns > 4: # rgb_timestamp rgb_path ...
            for line in lines:
                rgb_timestamp, rgb_path, *extra = line.strip().split(' ')
                rgb_paths.append(rgb_path)
                rgb_timestamps.append(rgb_timestamp)
            return rgb_paths, rgb_timestamps
        
def undistort_rgb_rad_tan(rgb_txt, sequence_path, camera_matrix, distortion_coeffs):

    rgb_paths, *_ = load_rgb_txt(rgb_txt)

    # Estimate undistortion transformation
    rgb_path = os.path.join(sequence_path, rgb_paths[0])
    rgb = cv2.imread(rgb_path)
    h, w = rgb.shape[:2]
    new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, distortion_coeffs, (w, h), 1, (w, h))
    map1, map2 = cv2.initUndistortRectifyMap(camera_matrix, distortion_coeffs, np.eye(3), new_camera_matrix, (w, h),5)
    x, y, w, h = roi

    # Undistort rgb images
    for rgb_subpath in tqdm(rgb_paths):
        rgb_path = os.path.join(sequence_path, rgb_subpath)
        rgb = cv2.imread(rgb_path)
        undistorted_rgb = cv2.remap(rgb, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        undistorted_rgb = undistorted_rgb[y:y+h, x:x+w]
        cv2.imwrite(rgb_path, undistorted_rgb)

    fx, fy, cx, cy = (new_camera_matrix[0, 0], new_camera_matrix[1, 1],
                      new_camera_matrix[0, 2], new_camera_matrix[1, 2])
    return fx, fy, cx, cy

def undistort_depth_rad_tan(rgb_txt, sequence_path, camera_matrix, distortion_coeffs):
    
    _, _, depth_paths, _ = load_rgb_txt(rgb_txt)

    # Estimate undistortion transformation
    depth_path = os.path.join(sequence_path, depth_paths[0])
    depth = cv2.imread(depth_path, cv2.IMREAD_UNCHANGED)
    h, w = depth.shape[:2]
    new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, distortion_coeffs, (w, h), 1, (w, h))
    map1, map2 = cv2.initUndistortRectifyMap(camera_matrix, distortion_coeffs, np.eye(3), new_camera_matrix, (w, h), cv2.CV_16SC2)
    x, y, w, h = roi

    # Undistort depth images
    for depth_subpath in tqdm(depth_paths):
        depth_path = os.path.join(sequence_path, depth_subpath)
        depth = cv2.imread(depth_path)
        undistorted_depth = cv2.remap(depth, map1, map2, interpolation=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT)
        undistorted_depth = undistorted_depth[y:y+h, x:x+w]
        cv2.imwrite(depth_path, undistorted_depth)

    fx, fy, cx, cy = (new_camera_matrix[0, 0], new_camera_matrix[1, 1],
                      new_camera_matrix[0, 2], new_camera_matrix[1, 2])
    return fx, fy, cx, cy

def undistort_fisheye(rgb_txt, sequence_path, camera_matrix, distortion_coeffs):
    image_list = []
    with open(rgb_txt, 'r') as file:
        for line in file:
            timestamp, path, *extra = line.strip().split(' ')
            image_list.append(path)

    first = True
    for image_name in tqdm(image_list):
        image_path = os.path.join(sequence_path, image_name)
        image = cv2.imread(image_path)
        if first:
            first = False
            h, w = image.shape[:2]
            new_camera_matrix = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
                camera_matrix, distortion_coeffs, (w, h), None)
            map1, map2 = cv2.fisheye.initUndistortRectifyMap(
                camera_matrix, distortion_coeffs, np.eye(3), new_camera_matrix, (w, h), cv2.CV_16SC2)

        undistorted_image = cv2.remap(image, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        cv2.imwrite(image_path, undistorted_image)

    fx, fy, cx, cy = (new_camera_matrix[0, 0], new_camera_matrix[1, 1],
                      new_camera_matrix[0, 2], new_camera_matrix[1, 2])
    return fx, fy, cx, cy


def resize_rgb_images(rgb_txt, sequence_path, target_width, target_height, camera_matrix):
    
    rgb_paths, *_ = load_rgb_txt(rgb_txt)

    # Load the first image to get original dimensions and compute scaling factors
    sample_rgb_path = os.path.join(sequence_path, rgb_paths[0])
    sample_rgb = cv2.imread(sample_rgb_path)
    original_height, original_width = sample_rgb.shape[:2]

    # Scaling factors for adjusting the camera intrinsic parameters
    scale = np.sqrt(target_width * target_height * original_width / original_height) / original_width
    w = int(original_width * scale)
    h = int(original_height * scale)
    scale_x = w / original_width
    scale_y = h / original_height

    # Resize all RGB images
    for rgb_subpath in tqdm(rgb_paths, desc="Resizing RGB Images"):
        rgb_path = os.path.join(sequence_path, rgb_subpath)
        rgb_image = cv2.imread(rgb_path)
        resized_rgb = cv2.resize(rgb_image, (w, h), interpolation=cv2.INTER_LINEAR)
        cv2.imwrite(rgb_path, resized_rgb)

    # Adjust the camera matrix for the new resolution
    fx, fy, cx, cy = (camera_matrix[0,0] * scale_x, camera_matrix[1,1] * scale_y,
                      camera_matrix[0,2] * scale_x, camera_matrix[1,2] * scale_y)
    
    return fx, fy, cx, cy

