#!/usr/bin/env python3

"""
Runs event camera emulation on input from a gstreamer camera device or ROS
topics and publishes results in ROS topics.
"""

import os
import sys
import time
import datetime

import cv2
import rclpy

from rclpy.node import Node
from launch_ros.substitutions import FindPackageShare

from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
from std_msgs.msg import Bool

from event_camera_emulation.emulator import EventCameraEmulator


# Colorized logging variables:
YELLOW = '\033[1;33m'
GREEN = '\033[92m'
RESET = '\033[0m'


## ----------------------------------------------------------------------
## ROS Nodes, Callbacks and Message Initializations:
## ----------------------------------------------------------------------

class EventImageStreamerNode(Node):

    def __init__(self):
        super().__init__('event_image_streamer_node')

        self.pkg_share_path = FindPackageShare(
                package='event_camera_emulation').find('event_camera_emulation')

        # Get node parameters:
        self.declare_parameter('source_type', 'ros_topic')
        self.declare_parameter('camera_device_id', 0)
        self.declare_parameter('input_image_topic', 
                               '/camera/camera/color/image_raw')
        self.declare_parameter('trigger_topic', '~/detector_trigger')
        self.declare_parameter('publish_output', True)
        self.declare_parameter('display_output', False)
        self.declare_parameter('display_combined_images', True)
        self.declare_parameter('theta', 60)
        self.declare_parameter('record_off_events', True)
        self.declare_parameter('register_off_events_as_on', False)
        self.declare_parameter('compute_from_rgb', True)
        self.declare_parameter('use_log_diff', False)
        self.declare_parameter('method', '')
        self.declare_parameter('blur_images', False)
        self.declare_parameter('save_data', False)
        self.declare_parameter('save_data_on_trigger', False)
        self.declare_parameter('data_saving_path', '')
        self.declare_parameter('rate', 30)

        self.source_type = self.get_parameter('source_type').value
        self.camera_device_id = self.get_parameter('camera_device_id').value
        self.input_image_topic = self.get_parameter('input_image_topic').value
        self.trigger_topic = self.get_parameter('trigger_topic').value
        self.publish_output = self.get_parameter('publish_output').value
        self.display_output = self.get_parameter('display_output').value
        self.display_combined_images = self.get_parameter('display_combined_images').value
        self.theta = self.get_parameter('theta').value
        self.record_off_events = self.get_parameter('record_off_events').value
        self.register_off_events_as_on = self.get_parameter('register_off_events_as_on').value
        self.compute_from_rgb = self.get_parameter('compute_from_rgb').value
        self.use_log_diff = self.get_parameter('use_log_diff').value
        self.method = self.get_parameter('method').value
        self.blur_images = self.get_parameter('blur_images').value
        self.save_data = self.get_parameter('save_data').value
        self.save_data_on_trigger = self.get_parameter('save_data_on_trigger').value
        self.data_saving_path = self.get_parameter('data_saving_path').value
        self.rate = self.get_parameter('rate').value

        # Initialize publishers:
        self.original_image_publisher_ = self.create_publisher(Image, 
                                                               'original_images', 10)
        self.events_image_publisher_ = self.create_publisher(Image, 
                                                             'events_images', 10)
        self.visual_events_image_publisher_ = self.create_publisher(Image, 
                                                                    'visual_events_images', 10)

        # Initialize subscribers:
        if self.save_data_on_trigger:
            self.trigger_subscription = self.create_subscription(Bool, 
                                                                 self.trigger_topic, 
                                                                 self.trigger_callback, 
                                                                 10)

        # self.image_subscription = self.create_subscription(Image, self.input_image_topic, self.image_callback, 10)

        # Initialize data variables:
        self.e_camera_emulator = EventCameraEmulator()
        self.initialize()

    def initialize(self):
        self.bridge = CvBridge()
        self.camera_device_ = None
        self.current_image = None
        self.previous_image = None
        self.current_image_msg = None
        self.ros_triggered = False

        # Set up output data directory:
        if self.save_data:
            output_sub_dir_path = f'{self.get_name()}_output_' + \
                                  datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir_path = os.path.join(self.output_dir_path, output_sub_dir_path)
            self.get_logger().info(f'Saving output data in {self.output_dir_path}')

            if not os.path.isdir(self.output_dir_path):
                self.get_logger().info(f'Output directory does not exist! Creating now...')
                if not os.path.exists(self.output_dir_path):
                    os.makedirs(self.output_dir_path)

    def image_callback(self, msg):
        self.current_image_msg = msg

    def trigger_callback(self, msg):
        self.get_logger().info('Received trigger ROS message')
        self.ros_triggered = msg.data
        if self.ros_triggered:
            self.get_logger().info('Starting data recording')
        else:
            self.get_logger().info('Stopping data recording')

    def run_node(self):
        try:
            while rclpy.ok():
                # Note: timeout_sec is necessary to avoid blocking due to camera_device input:
                rclpy.spin_once(self, timeout_sec=0)

                if self.source_type == 'camera_device':
                    _, self.current_image = self.camera_device_.read()
                elif self.source_type == 'ros_topic':
                    try:
                        self.current_image = self.bridge.imgmsg_to_cv2(self.current_image_msg, "bgr8")
                    except CvBridgeError as e:
                        self.get_logger().warn(f'Failed to convert image message to opencv format! Error: {e}')
                        continue

                if self.compute_from_rgb:
                    events_image = self.e_camera_emulator.get_events_image_rgb(self.current_image, self.previous_image, 
                                                                          self.theta, self.record_off_events, 
                                                                          self.register_off_events_as_on, 
                                                                          use_log_diff=self.use_log_diff, method=self.method, 
                                                                          blur_images=self.blur_images)
                else:
                    ## Baseline method: compute events from grayscale images:
                    events_image = self.e_camera_emulator.get_events_image(self.current_image, self.previous_image, 
                                                                      self.theta, self.record_off_events, 
                                                                      self.register_off_events_as_on, 
                                                                      use_log_diff=self.use_log_diff)

                visual_events_image = self.e_camera_emulator.get_visual_events_image(events_image)

                if self.save_data:
                    if self.save_data_on_trigger and not self.ros_triggered:
                        pass
                    else:
                        filename_suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        cv2.imwrite(os.path.join(self.data_saving_path, '{}_ece_rgb_image_1.png'.format(filename_suffix)), self.previous_image)
                        cv2.imwrite(os.path.join(self.data_saving_path, '{}_ece_rgb_image_2.png'.format(filename_suffix)), self.current_image)
                        cv2.imwrite(os.path.join(self.data_saving_path, '{}_ece_visual_events_image.png'.format(filename_suffix)), visual_events_image)

                if self.publish_output:
                    events_image_msg = self.bridge.cv2_to_imgmsg(events_image, encoding="passthrough")
                    events_image_msg.header.stamp = self.get_clock().now().to_msg()
                    self.events_image_publisher_.publish(events_image_msg)

                    visual_events_image_msg = self.bridge.cv2_to_imgmsg(visual_events_image, encoding="bgr8")
                    visual_events_image_msg.header.stamp = self.get_clock().now().to_msg()
                    self.visual_events_image_publisher_.publish(visual_events_image_msg)

                    self.original_image_publisher_.publish(self.bridge.cv2_to_imgmsg(self.current_image, encoding="bgr8"))

                if self.display_output:
                    if not self.display_combined_images:
                        cv2.imshow('Original Camera stream', self.current_image)
                        cv2.imshow('Simulated Event Camera stream', self.visual_events_image)
                    else:
                        current_image_copy = self.current_image.copy()
                        current_image_copy[events_image == 1] = [255., 0., 0.]
                        cv2.imshow('Simulated Event Camera stream', current_image_copy)
                    cv2.waitKey(1)

                self.previous_image = self.current_image.copy()

                time.sleep(float(1. / self.rate))

        except KeyboardInterrupt:
            self.get_logger().info(f'Stopping node')
            if self.source_type == 'camera_device':
                self.camera_device_.release() 
            if self.display_output:
                cv2.destroyAllWindows() 
            raise SystemExit

def main(args=None):
    ## ----------------------------------------------------------------------
    ## ROS Initializations:
    ## ----------------------------------------------------------------------
    rclpy.init(args=args)
    event_image_streamer_node = EventImageStreamerNode()

    ## ----------------------------------------------------------------------
    ## Execution:
    ## ----------------------------------------------------------------------

    if event_image_streamer_node.source_type == 'camera_device':
        event_image_streamer_node.get_logger().info(f'Accessing camera device: {event_image_streamer_node.camera_device_id}')
        try:
            event_image_streamer_node.camera_device_ = cv2.VideoCapture(int(event_image_streamer_node.camera_device_id))
        except Exception as e:
            self.get_logger().error(f'Could not access specified camera device! Error: {e}')
            raise SystemExit

        if event_image_streamer_node.camera_device_.isOpened():
            event_image_streamer_node.get_logger().info(f'{GREEN}Successfully opened camera device{RESET}')
            _, event_image_streamer_node.previous_image = event_image_streamer_node.camera_device_.read()
        else:
            event_image_streamer_node.get_logger().error(f'Could not open camera device!')
            raise SystemExit
    elif event_image_streamer_node.source_type == 'ros_topic':
        event_image_streamer_node.image_subscription = event_image_streamer_node.create_subscription(Image, event_image_streamer_node.input_image_topic, event_image_streamer_node.image_callback, 10)

        event_image_streamer_node.get_logger().info(f'Subscribing to image topic: {event_image_streamer_node.input_image_topic}')
        event_image_streamer_node.get_logger().info(f'Waiting for reception of first image message..')
        try:
            while event_image_streamer_node.current_image_msg is None:
                rclpy.spin_once(event_image_streamer_node)
                time.sleep(float(1. / event_image_streamer_node.rate))
        except (KeyboardInterrupt, ExternalShutdownException, SystemExit):
            event_image_streamer_node.get_logger().info(f'Terminating...')
            event_image_streamer_node.destroy_node()
            event_image_streamer_node.shutdown()

        event_image_streamer_node.get_logger().info(f'{GREEN}Received first image message{RESET}')
        try:
            event_image_streamer_node.previous_image = event_image_streamer_node.bridge.imgmsg_to_cv2(event_image_streamer_node.current_image_msg, "bgr8")
        except CvBridgeError as e:
            event_image_streamer_node.get_logger().warn(f'Failed to convert image message to opencv format! Error: {e}')
            event_image_streamer_node.destroy_node()
            event_image_streamer_node.shutdown()
    else:
        event_image_streamer_node.get_logger().warn(f'Invalid source type! Must be either camera_device or ros_topic')
        event_image_streamer_node.destroy_node()
        event_image_streamer_node.shutdown()

    try:
        event_image_streamer_node.run_node()
    except SystemExit:
        rclpy.logging.get_logger('rclpy').info('Stopping node...')

    event_image_streamer_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
