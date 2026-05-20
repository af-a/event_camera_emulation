#!/usr/bin/env python3

"""
Runs event camera emulation on input from a gstreamer camera device or ROS
topics and publishes results in ROS topics.
"""

import os
import sys
import time
import pickle
import datetime

import cv2
import rclpy
import numpy as np

from rclpy.lifecycle import State, TransitionCallbackReturn, Node, Publisher
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
        self.declare_parameter('theta', 10)
        self.declare_parameter('record_off_events', True)
        self.declare_parameter('register_off_events_as_on', False)
        self.declare_parameter('compute_from_rgb', True)
        self.declare_parameter('use_log_diff', False)
        self.declare_parameter('method', '')
        self.declare_parameter('blur_images', False)
        self.declare_parameter('save_image_data', False)
        self.declare_parameter('save_event_data', True)
        self.declare_parameter('save_data_on_trigger', True)
        self.declare_parameter('scale_images', True)
        self.declare_parameter('scale_factor', 0.25)
        self.declare_parameter('rate', 30.)
        self.declare_parameter('output_dir_path', '/tmp')

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
        self.save_image_data = self.get_parameter('save_image_data').value
        self.save_event_data = self.get_parameter('save_event_data').value
        self.save_data_on_trigger = self.get_parameter('save_data_on_trigger').value
        self.scale_images = self.get_parameter('scale_images').value
        self.scale_factor = self.get_parameter('scale_factor').value
        self.rate = self.get_parameter('rate').value
        self.output_dir_path = self.get_parameter('output_dir_path').value

    def initialize(self):
        self.bridge = CvBridge()
        self.camera_device_ = None
        self.current_image = None
        self.previous_image = None
        self.current_image_msg = None
        self.ros_triggered = False
        self.active = False

        # Set up output data directory:
        if self.save_image_data or self.save_event_data:
            output_sub_dir_path = f'{self.get_name()}_output_' + \
                                  datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir_path = os.path.join(self.output_dir_path, output_sub_dir_path)
            self.get_logger().info(f'Saving output data in {self.output_dir_path}')

            if not os.path.isdir(self.output_dir_path):
                self.get_logger().info(f'Output directory does not exist! Creating now...')
                if not os.path.exists(self.output_dir_path):
                    os.makedirs(self.output_dir_path)

        if self.scale_images:
            self.get_logger().info(f'Will scale images by a factor of {self.scale_factor}')

    def on_configure(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info(f'In state "{state.label}". Transitioning to "configure"')

        # Initialize rate timer:
        self.timer = self.create_timer(1. / self.rate, self.timer_callback, clock=self.get_clock())

        # Initialize publishers:
        self.original_image_publisher_ = self.create_lifecycle_publisher(Image, 
                                                               'original_images', 10)
        self.events_image_publisher_ = self.create_lifecycle_publisher(Image, 
                                                             'events_images', 10)
        self.visual_events_image_publisher_ = self.create_lifecycle_publisher(Image, 
                                                                    'visual_events_images', 10)

        # Initialize subscribers:
        if self.save_data_on_trigger:
            self.trigger_subscription = self.create_subscription(Bool, 
                                                                 self.trigger_topic, 
                                                                 self.trigger_callback, 
                                                                 10)

        if self.source_type == 'ros_topic':
            self.image_subscription = self.create_subscription(Image, self.input_image_topic, 
                                                               self.image_callback, 10)
            self.get_logger().info(f'Subscribing to image topic: {self.input_image_topic}')
            self.get_logger().info(f'Waiting for reception of first image message..')

        # Initialize data variables:
        self.e_camera_emulator = EventCameraEmulator()
        self.initialize()

        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info(f'In state "{state.label}". Transitioning to "activate"')
        return super().on_activate(state)

    def on_deactivate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info(f'In state "{state.label}". Transitioning to "deactivate"')
        return super().on_deactivate(state)

    def on_shutdown(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info(f'In state "{state.label}". Transitioning to "shutdown"')

        self.destroy_publisher(self.original_image_publisher_)
        self.destroy_publisher(self.events_image_publisher_)
        self.destroy_publisher(self.visual_events_image_publisher_)

        if self.save_data_on_trigger:
            self.destroy_subscription(self.trigger_subscription)

        if self.source_type == 'ros_topic':
            self.destroy_subscription(self.image_subscription)

        self.destroy_timer(self.timer)

        if self.source_type == 'camera_device':
            self.camera_device_.release() 
        if self.display_output:
            cv2.destroyAllWindows() 

        return TransitionCallbackReturn.SUCCESS

    def image_callback(self, msg):
        self.current_image_msg = msg

    def trigger_callback(self, msg):
        self.get_logger().info('Received trigger ROS message')
        self.ros_triggered = msg.data
        if self.ros_triggered:
            self.get_logger().info('Starting data recording')
        else:
            self.get_logger().info('Stopping data recording')

    def timer_callback(self):
        ## ----------------------------------------------------------------------
        ## Execution:
        ## ----------------------------------------------------------------------

        if not self.active:
            if self.source_type == 'camera_device':
                self.get_logger().info(f'Accessing camera device: {self.camera_device_id}')
                try:
                    self.camera_device_ = cv2.VideoCapture(int(self.camera_device_id))
                except Exception as e:
                    self.get_logger().error(f'Could not access specified camera device! Error: {e}')
                    self.trigger_shutdown()

                if self.camera_device_.isOpened():
                    self.get_logger().info(f'{GREEN}Successfully opened camera device{RESET}')
                    _, self.previous_image = self.camera_device_.read()
                    if self.scale_images:
                        self.previous_image = cv2.resize(self.previous_image, (0, 0), 
                                                         fx=self.scale_factor, fy=self.scale_factor)
                    self.active = True
                else:
                    self.get_logger().error(f'Could not open camera device!')
                    self.trigger_shutdown()
            elif self.source_type == 'ros_topic':
                if self.current_image_msg is None:
                    return
                else:

                    self.get_logger().info(f'{GREEN}Received first image message{RESET}')
                    # self.get_logger().info(f'[DEBUG] dir(self): {dir(self)}')
                    try:
                        self.previous_image = self.bridge.imgmsg_to_cv2(self.current_image_msg, "bgr8")
                        if self.scale_images:
                            self.previous_image = cv2.resize(self.previous_image, (0, 0), 
                                                             fx=self.scale_factor, fy=self.scale_factor)
                        self.active = True
                    except CvBridgeError as e:
                        self.get_logger().warn(f'Failed to convert image message to opencv format! Error: {e}')
                        self.trigger_shutdown()
            else:
                self.get_logger().warn(f'Invalid source type! Must be either camera_device or ros_topic')
                self.trigger_shutdown()
        else:
            if self.source_type == 'camera_device':
                _, self.current_image = self.camera_device_.read()
            elif self.source_type == 'ros_topic':
                try:
                    self.current_image = self.bridge.imgmsg_to_cv2(self.current_image_msg, "bgr8")
                except CvBridgeError as e:
                    self.get_logger().warn(f'Failed to convert image message to opencv format! Error: {e}')
                    return

            if self.scale_images:
                self.current_image = cv2.resize(self.current_image, (0, 0), 
                                                fx=self.scale_factor, fy=self.scale_factor)

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

            if self.save_image_data or self.save_event_data:
                if self.save_data_on_trigger and not self.ros_triggered:
                    pass
                else:
                    filename_suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    if self.save_image_data:
                        cv2.imwrite(os.path.join(self.output_dir_path, 
                                                 f'{filename_suffix}_ece_rgb_image_1.png'), 
                                    self.previous_image)
                        cv2.imwrite(os.path.join(self.output_dir_path, 
                                                 f'{filename_suffix}_ece_rgb_image_2.png'), 
                                    self.current_image)
                        cv2.imwrite(os.path.join(self.output_dir_path, 
                                                 f'{filename_suffix}_ece_visual_events_image.png'), 
                                    visual_events_image)
                        cv2.imwrite(os.path.join(self.output_dir_path, 
                                                 f'{filename_suffix}_ece_events_image.png'), 
                                    events_image)

                    if self.save_event_data:
                        with open(os.path.join(self.output_dir_path, f'{filename_suffix}_ece_events_array.pkl'), 'wb') as handle:
                            pickle.dump(events_image, handle, protocol=pickle.HIGHEST_PROTOCOL)

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

def main(args=None):
    ## ----------------------------------------------------------------------
    ## ROS Initializations:
    ## ----------------------------------------------------------------------
    rclpy.init(args=args)
    executor = rclpy.executors.SingleThreadedExecutor()
    event_image_streamer_node = EventImageStreamerNode()
    executor.add_node(event_image_streamer_node)

    try:
        executor.spin()
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        event_image_streamer_node.destroy_node()

if __name__ == '__main__':
    main()
