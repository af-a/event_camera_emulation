#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, Shutdown, RegisterEventHandler, EmitEvent
from launch.substitutions import LaunchConfiguration
from launch.events.process import ShutdownProcess
from launch.events.matchers import matches_action
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions.lifecycle_node import LifecycleNode
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState

from lifecycle_msgs.msg import Transition 


def generate_launch_description():
    source_type_arg = DeclareLaunchArgument('source_type', 
                                            default_value='ros_topic')
    camera_device_id_arg = DeclareLaunchArgument('camera_device_id', 
                                                 default_value='0')
    input_image_topic_arg = DeclareLaunchArgument('input_image_topic', 
                                                  default_value='/camera/camera/color/image_raw')
    trigger_topic_arg = DeclareLaunchArgument('trigger_topic', 
                                              default_value='~/detector_trigger')
    publish_output_arg = DeclareLaunchArgument('publish_output', 
                                               default_value='True')
    display_output_arg = DeclareLaunchArgument('display_output', 
                                               default_value='False')
    display_combined_images_arg = DeclareLaunchArgument('display_combined_images', 
                                                        default_value='True')
    record_off_events_arg = DeclareLaunchArgument('record_off_events', 
                                                  default_value='True')
    register_off_events_as_on_arg = DeclareLaunchArgument('register_off_events_as_on', 
                                                          default_value='False')
    compute_from_rgb_arg = DeclareLaunchArgument('compute_from_rgb', 
                                                 default_value='False')
    use_log_diff_arg = DeclareLaunchArgument('use_log_diff', 
                                             default_value='False')
    blur_images_arg = DeclareLaunchArgument('blur_images', 
                                             default_value='False')
    save_image_data_arg = DeclareLaunchArgument('save_image_data', 
                                                default_value='False')
    save_event_data_arg = DeclareLaunchArgument('save_event_data', 
                                                default_value='True')
    save_data_on_trigger_arg = DeclareLaunchArgument('save_data_on_trigger', 
                                                     default_value='True')
    scale_images_arg = DeclareLaunchArgument('scale_images', 
                                             default_value='True')
    theta_arg = DeclareLaunchArgument('theta', default_value='10')
    method_arg = DeclareLaunchArgument('method', default_value='')
    scale_factor_arg = DeclareLaunchArgument('scale_factor', default_value='0.25')
    rate_arg = DeclareLaunchArgument('rate', default_value='30.')
    output_dir_path_arg = DeclareLaunchArgument('output_dir_path', 
                                                default_value='/tmp')

    event_image_streamer_node_name = 'event_image_streamer'
    event_image_streamer_node = LifecycleNode(
        package='event_camera_emulation',
        executable='event_image_streamer',
        name=event_image_streamer_node_name,
        namespace='',
        parameters=[
            {'source_type': LaunchConfiguration('source_type')},
            {'camera_device_id': LaunchConfiguration('camera_device_id')},
            {'input_image_topic': LaunchConfiguration('input_image_topic')},
            {'trigger_topic': LaunchConfiguration('trigger_topic')},
            {'publish_output': LaunchConfiguration('publish_output')},
            {'display_output': LaunchConfiguration('display_output')},
            {'display_combined_images': LaunchConfiguration('display_combined_images')},
            {'record_off_events': LaunchConfiguration('record_off_events')},
            {'register_off_events_as_on': LaunchConfiguration('register_off_events_as_on')},
            {'compute_from_rgb': LaunchConfiguration('compute_from_rgb')},
            {'use_log_diff': LaunchConfiguration('use_log_diff')},
            {'blur_images': LaunchConfiguration('blur_images')},
            {'save_image_data': LaunchConfiguration('save_image_data')},
            {'save_event_data': LaunchConfiguration('save_event_data')},
            {'save_data_on_trigger': LaunchConfiguration('save_data_on_trigger')},
            {'scale_images': LaunchConfiguration('scale_images')},
            {'method': LaunchConfiguration('method')},
            {'theta': LaunchConfiguration('theta')},
            {'scale_factor': LaunchConfiguration('scale_factor')},
            {'rate': LaunchConfiguration('rate')},
            {'output_dir_path': LaunchConfiguration('output_dir_path')},
        ],
        on_exit=Shutdown(),
    )

    # Event for starting node in configure state:
    configure_node = EmitEvent(
        event=ChangeState(
           lifecycle_node_matcher=matches_action(event_image_streamer_node),
           transition_id=Transition.TRANSITION_CONFIGURE,
        )
    )
    # Event for activating node when in inactive state:
    activate_node = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=event_image_streamer_node,
            start_state='configuring',
            goal_state='inactive',
            entities=[
                EmitEvent(
                    event=ChangeState(
                       lifecycle_node_matcher=matches_action(event_image_streamer_node),
                       transition_id=Transition.TRANSITION_ACTIVATE,
                    )
                )
            ],
        )
    )
    # Event for shutting down node when in shutdown state:
    shutdown_node = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=event_image_streamer_node,
            goal_state='shuttingdown',
            entities=[
                EmitEvent(event=ShutdownProcess(process_matcher=matches_action(event_image_streamer_node))),
            ],
        )
    )

    return LaunchDescription([
        source_type_arg,
        camera_device_id_arg,
        input_image_topic_arg,
        trigger_topic_arg,
        publish_output_arg,
        display_output_arg,
        display_combined_images_arg,
        record_off_events_arg,
        register_off_events_as_on_arg,
        compute_from_rgb_arg,
        use_log_diff_arg,
        blur_images_arg,
        save_image_data_arg,
        save_event_data_arg,
        save_data_on_trigger_arg,
        scale_images_arg,
        theta_arg,
        method_arg,
        scale_factor_arg,
        rate_arg,
        output_dir_path_arg,
        event_image_streamer_node, 
        configure_node,
        activate_node,
        shutdown_node
    ])
