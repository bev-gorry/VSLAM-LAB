import rosbag
from cv_bridge import CvBridge
import os
import argparse
import cv2
from tqdm import tqdm
import numpy as np

def main():
    parser = argparse.ArgumentParser(description=f"{__file__}")

    parser.add_argument('rosbag_path', type=str, help=f"rosbag path")
    parser.add_argument('output_folder', type=str, help=f"output folder")
    parser.add_argument('image_topic', type=str, help=f"image topic")


    args = parser.parse_args()

    bridge = CvBridge()
    rosbag_path = args.rosbag_path
    image_topic = args.image_topic
    output_folder = args.output_folder
    with rosbag.Bag(rosbag_path, 'r') as bag:
        for topic, msg, t in tqdm(bag.read_messages(topics=[image_topic])):
            try:
                cv_image = bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            except Exception as e:
                print(f"Could not convert image: {e}")
                continue

            image_name = f"{t}.png"
            image_path = os.path.join(output_folder,image_name)
         
            cv2.imwrite(image_path, cv_image)

if __name__ == "__main__":
    main()

  
