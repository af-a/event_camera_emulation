#!/usr/bin/env python3

"""Runs a sample program demonstrating basic event emulation.

Usage:
    $ python3 stream_camera_events.py -v $DEVICE_ID

"""

import sys
import argparse

import cv2

from event_camera_emulation.emulator import EventCameraEmulator


camera_device_ = None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--video_device', '-v', type=str,
                        default='0', help='The video device. For a camera,'
                        'provide its id, for e.g. 0. For a video file, provide'
                        'its path.')
    args = parser.parse_args()

    try:
        camera_device_ = cv2.VideoCapture(int(args.video_device))
    except ValueError:
        camera_device_ = cv2.VideoCapture(args.video_device)

    if camera_device_.isOpened():
        print('[stream_camera_events] [INFO] Successfully opened camera device')
        _, previous_image = camera_device_.read()
    else:
        print('[stream_camera_events] [ERROR] Could not access camera device!')
        sys.exit()

    e_camera_emulator = EventCameraEmulator()

    try:
        while True: 
            _, current_image = camera_device_.read()
            event_image = e_camera_emulator.get_events_image_rgb(current_image, previous_image, 30, 
                                                                 record_off_events=True, 
                                                                 register_off_events_as_on=False)

            visual_event_image = e_camera_emulator.get_visual_events_image(event_image)

            previous_image = current_image

            cv2.imshow('Original Camera stream', current_image) 
            cv2.imshow('Simulated Event Camera stream', visual_event_image)
            cv2.waitKey(1)

    except KeyboardInterrupt:
        print('\n[stream_camera_events] [INFO] Finished streaming, exiting program...')
        camera_device_.release() 
        cv2.destroyAllWindows() 
