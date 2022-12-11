#!/usr/bin/env python3

import os
import sys
import argparse
import datetime

import rospy
import rospkg
import cv2

from event_camera_emulation.emulator import EventCameraEmulator

from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
from std_msgs.msg import Bool


camera_device_ = None
bridge = CvBridge()
triggered_ = False

image_publisher_ = None
visual_events_image_publisher_ = None
current_image_msg_ = None

def trigger_callback(msg):
    global triggered_
    triggered_ = msg.data
    if triggered_:
        rospy.loginfo('[event_image_streamer] Starting data recording')
    else:
        rospy.loginfo('[event_image_streamer] Stopping data recording')

def image_callback(msg):
    global current_image_msg_
    current_image_msg_ = msg


if __name__ == '__main__':
    rospy.init_node('event_image_streamer')
    rate = rospy.Rate(30)         # currently highest achievable

    source_type = rospy.get_param('~source_type', 'camera_device')
    publish_output = rospy.get_param('~publish_output', True)
    display_output = rospy.get_param('~display_output', False)
    display_combined_images = rospy.get_param('~display_combined_images', True)
    theta = rospy.get_param('~theta', 60)
    record_off_events = rospy.get_param('~record_off_events', True)
    register_off_events_as_on = rospy.get_param('~register_off_events_as_on', True)
    compute_from_rgb = rospy.get_param('~compute_from_rgb', True)
    use_log_diff = rospy.get_param('~use_log_diff', False)
    method = rospy.get_param('~method', '')
    blur_images = rospy.get_param('~blur_images', False)
    save_data = rospy.get_param('~save_data', False)
    save_data_on_trigger = rospy.get_param('~save_data_on_trigger', False)
    data_saving_path = rospy.get_param('~data_saving_path', '')

    original_image_publisher_ = rospy.Publisher('original_images', Image, queue_size=10)
    events_image_publisher_ = rospy.Publisher('events_images', Image, queue_size=10)
    visual_events_image_publisher_ = rospy.Publisher('visual_events_images', Image, queue_size=10)

    if save_data_on_trigger:
        trigger_topic = '/trigger'
        trigger_subscriber = rospy.Subscriber(trigger_topic, Bool, trigger_callback)

    if source_type == 'camera_device':
        camera_device_id = rospy.get_param('~camera_device_id', 0)
        rospy.loginfo('[event_image_streamer] Accessing camera device: {}'.format(camera_device_id))
        try:
            camera_device_ = cv2.VideoCapture(int(camera_device_id))
        except Exception as e:
            rospy.loginfo('[event_image_streamer] Could not access specified camera device!')
            print('Error:', e)
            sys.exit()

        if camera_device_.isOpened():
            rospy.loginfo('[event_image_streamer] Successfully opened camera device')
            _, previous_image = camera_device_.read()
        else:
            rospy.loginfo('[event_image_streamer] Could not open camera device!')
            sys.exit()
    elif source_type == 'ros_topic':
        image_topic = rospy.get_param('~image_topic', '/camera/color/image_raw')
        image_subscriber = rospy.Subscriber(image_topic, Image, image_callback)

        rospy.loginfo('[event_image_streamer] Subscribing to image topic: {}'.format(image_topic))
        rospy.loginfo('[event_image_streamer] Waiting for reception of first image message...')
        try:
            while current_image_msg_ is None:
                rospy.sleep(0.1)
        except (KeyboardInterrupt, rospy.ROSInterruptException):
            rospy.loginfo('[event_image_streamer] Terminating...')
            sys.exit()

        rospy.loginfo('[event_image_streamer] Received first image message')
        try:
            previous_image = bridge.imgmsg_to_cv2(current_image_msg_, "bgr8")
        except CvBridgeError as e:
            rospy.logwarn('[event_image_streamer] Failed to convert image message to opencv format!')
            print('Error:', e)
            sys.exit()
    else:
        rospy.logerr('[event_image_streamer] Invalid source type! Must be either camera_device or ros_topic')
        sys.exit()

    e_camera_emulator = EventCameraEmulator()

    if save_data:
        rospy.logwarn('[event_image_streamer] Will save data to:')
        print(data_saving_path)
    if save_data_on_trigger:
        rospy.logwarn('[event_image_streamer] Will save data only when triggered!')

    rospy.loginfo('[event_image_streamer] Streaming emulated event images')
    try:
        while not rospy.is_shutdown(): 
            if source_type == 'camera_device':
                _, current_image = camera_device_.read()
            elif source_type == 'ros_topic':
                try:
                    current_image = bridge.imgmsg_to_cv2(current_image_msg_, "bgr8")
                except CvBridgeError as e:
                    rospy.logwarn('[event_image_streamer] Failed to convert image message to opencv format!')
                    print('Error:', e)
                    continue

            if compute_from_rgb:
                events_image = e_camera_emulator.get_events_image_rgb(current_image, previous_image, theta, record_off_events, register_off_events_as_on, use_log_diff=use_log_diff, method=method, blur_images=blur_images)
            else:
                ## Baseline method: compute events from grayscale images:
                events_image = e_camera_emulator.get_events_image(current_image, previous_image, theta, record_off_events, register_off_events_as_on, use_log_diff=use_log_diff)

            visual_events_image = e_camera_emulator.get_visual_events_image(events_image)

            if save_data:
                if save_data_on_trigger and not triggered_:
                    pass
                else:
                    filename_suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    cv2.imwrite(os.path.join(data_saving_path, '{}_ece_rgb_image_1.png'.format(filename_suffix)), previous_image)
                    cv2.imwrite(os.path.join(data_saving_path, '{}_ece_rgb_image_2.png'.format(filename_suffix)), current_image)
                    cv2.imwrite(os.path.join(data_saving_path, '{}_ece_visual_events_image.png'.format(filename_suffix)), visual_events_image)

            if publish_output:
                events_image_msg = bridge.cv2_to_imgmsg(events_image, encoding="passthrough")
                events_image_msg.header.stamp = rospy.Time.now()
                events_image_publisher_.publish(events_image_msg)

                visual_events_image_msg = bridge.cv2_to_imgmsg(visual_events_image, encoding="bgr8")
                visual_events_image_msg.header.stamp = rospy.Time.now()
                visual_events_image_publisher_.publish(visual_events_image_msg)

                original_image_publisher_.publish(bridge.cv2_to_imgmsg(current_image, encoding="bgr8"))

            if display_output:
                if not display_combined_images:
                    cv2.imshow('Original Camera stream', current_image)
                    cv2.imshow('Simulated Event Camera stream', visual_events_image)
                else:
                    current_image_copy = current_image.copy()
                    current_image_copy[events_image == 1] = [255., 0., 0.]
                    cv2.imshow('Simulated Event Camera stream', current_image_copy)
                cv2.waitKey(1)

            previous_image = current_image

            try:
                rate.sleep()
            except rospy.ROSTimeMovedBackwardsException as e:
                rospy.logwarn('[event_image_streamer] Caught ROSTimeMovedBackwardsException when executing rate.sleep(). '
                               'This can happen when incoming messages had stopped, and have just resumed publishing.')
    except (KeyboardInterrupt, rospy.ROSInterruptException):
        rospy.loginfo('[event_image_streamer] Stopping node')
        if source_type == 'camera_device':
            camera_device_.release() 
        if display_output:
            cv2.destroyAllWindows() 
