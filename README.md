<p align="center"><img width=60% src="https://github.com/AhmedFaisal95/event_camera_emulation/blob/main/media/images/ece_logo.png"></p>
&nbsp;

<div align="center">

[![Python 3.8](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![GitHub license](https://badgen.net/github/license/Naereen/Strapdown.js)](https://github.com/AhmedFaisal95/event_camera_emulation/blob/main/LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/AhmedFaisal95/event_camera_emulation.svg)](https://github.com/AhmedFaisal95/event_camera_emulation/releases)
[![Maintenance](https://img.shields.io/badge/Maintained-yes-green.svg)](https://github.com/AhmedFaisal95/event_camera_emulation)
![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)

</div>

--------------------------------------------------------------------------------

<div align="center">

Emulate <b>event camera</b> outputs using conventional color camera images.

The emulator processes input images from live camera feeds or ROS topics into compact and visual representations of events. The package is designed for integration with ROS components and includes ROS nodes and launch files with various parameterization options.

Tested in Linux Ubuntu 20.04 and Python 3.8.
</div>

&nbsp;

![](media/gifs/demo_rgb_and_events_images.gif)

## Contents
- [➤ Purpose](#purpose)
- [➤ Features](#features)
- [➤ Installation](#installation)
- [➤ Usage](#usage)
    - [ROS](#ros)
    - [Custom Implementations](#custom-implementations)
- [➤ Directory Structure](#directory-structure)
- [➤ Dependencies](#dependencies)
- [➤ Future Plans](#future-plans)
- [➤ Contributing](#contributing)
- [➤ Credits](#credits)

## Purpose

<b>Event cameras (ECs)</b> are neuromorphic sensors designed to mimic the operation of photoreceptor cells in biological retinas. Compared to conventional color cameras, they can be more power-efficient, experience less latencies, have higher dynamic ranges, and mitigate effects of motion blur. Instead of synchronously capturing absolute light intensities, EC pixels asynchronously capture significant, local changes in light intensity, emitting <b>events</b> at these locations. This is useful in exclusively capturing motion, for example. Developing algorithms for utilizing this novel event-based data is an ongoing research topic.

ECs are not widely commerically available yet and current models are fairly expensive. This package enables emulating event data from conventional RGB data in the absence of a real EC to ease experimentation in research and development applications that explore the event-based vision paradigm.

Though other emulators exist, this was developed during a thesis project for lack of a simple, extensible package that enables processing data from live camera feeds or ROS topics, integrates easily in ROS pipelines, and is not tied to a specific simulation environment.


## Features

* An extensible `EventCameraEmulator` class, which can be adapted for different emulation and data visualization methods.
* Using source RGB images from a connected camera device or a ROS topic to emulate events.
* Different implementations of event emulation (e.g. using changes in absolute or log values, single or multi-channel change detection criteria, etc.)
* ROS nodes and launch files.


## Installation

### Python Package

The recommended way to install the core python package is using pip in the main directory:
```
pip install .
```

Alternatively, the package can also be installed by running:
```
python setup.py install
```

### ROS Package

The `event_camera_emulation` ROS package can be built by cloning this repository in the `src` directory of a catkin workspace and using any standard build tool, e.g. `catkin_make`, `catkin build`, etc.

For example, if using `catkin build`, simply run:
```
catkin build event_camera_emulation
```

Make sure to source your workspace setup file so that the package's ROS files are accessible:
```
source $CATKIN_WORKSPACE/devel/setup.bash
```
Note: this has been tested in ROS Noetic.

## Usage

A sample Python program demonstrating the core emulation functionality of the package can be run using:
```
python3 scripts/stream_camera_events.py
```
If a camera device (ID 0) is accessible, you should see two video streams: the source camera images and a visual representation of emulated events, until the program is terminated

### ROS

To start the provided `event_image_streamer` ROS node, simply run the launch file:
```
roslaunch event_camera_emulation stream.launch display_output:=True
```

This sets default values for various ROS parameters; expand the following for a summary of the most important parameters.

<details>
<summary> <b>event_image_streamer</b> Node Parameters </summary>
&nbsp;

| Parameter                   | Description                                  |
| --------------------------- | -------------------------------------------- |
| `source_type`               | source image type; either *camera_device* or *ros_topic*               |
| `camera_device_id`          | if `source_type` is *camera_device*, the device ID               |
| `image_topic`               | if `source_type` is *ros_topic*, the ROS image topic to subscribe to               |
| `publish_output`            | whether to publish the emulator's output in ROS topics               |
| `display_output`            | whether to display the emulator's output in a GUI (OpenCV) window               |
| `theta`                     | event emission threshold value               |
| `record_off_events`         | whether to record or disregard OFF (i.e negative) events               |
| `register_off_events_as_on` | whether to register OFF events (if recorded) as ON events, thus disregarding event polarity.               |
| `compute_from_rgb`          | whether to compute events from RGB values (as opposed to converting input images to grayscale first)               |
| `use_log_diff`              | whether to compute events using differences in log intensities instead of absolute intensities               |
| `method`                    | custom event emulation method to use; at the moment, only the *salvatore* method is implemented (apart from the default method)               |
| `blur_images`               | whether to blur input images before computing events (could reduce noisy events)               |
| `save_data`                 | whether to save the emulator's data (source images, visual events images, etc.)               |
| `data_saving_path`          | if `save_data`, the directory in which to save the emulator's output               |
</details>


In the example command above, `display_output` is set to `True` to start a window that displays the current emulated events overlaid on the source RGB images, but this is usually not needed in ROS pipelines.

<b>Note:</b> the `event_image_streamer` node can optionally save the input (RGB) and output (images) captured during emulation in a specified directory by setting the appropriate ROS parameters (`save_data`, `save_data_on_trigger`, `data_saving_path`).

An implementation of the [pyDVS](https://github.com/chanokin/pyDVS) emulator can be launched using the similar `stream_pydvs.launch` file.

### Custom Implementations

If you are integrating the emulator in your own code, event images can be obtained by instantiating an `EventCameraEmulator` object and calling the `get_events_image` function, providing two consecutive images (`numpy.ndarray` objects):
```
e_camera_emulator = EventCameraEmulator()
event_image = e_camera_emulator.get_events_image_rgb(current_image, previous_image)
```

Refer to the [stream_camera_events.py](https://github.com/AhmedFaisal95/event_camera_emulation/blob/main/scripts/stream_camera_events.py) script for an example.

<!--
## Examples

-->

## Directory Structure

<details>
<summary> Package Files </summary>

```
event_camera_emulation
│
├── common
│   └── event_camera_emulation
│       ├── emulator.py
│       └── __init__.py
│
├── ros
│   ├── launch
│   │   ├── stream.launch
│   │   └── stream_pydvs.launch
│   └── scripts
│       ├── event_image_streamer
│       └── pydvs_event_image_streamer
│
├── scripts
│   └── stream_camera_events.py
│
├── setup.py
├── CMakeLists.txt
├── package.xml
├── README.md
└── LICENSE
```

</details>


## Dependencies

* `OpenCV`

For ROS functionalities:
* `rospy`
* `cv_bridge`
* `sensor_msgs`

## Future Plans

* Adapting package for ROS2 (foxy)
* Implementing unit tests.

## Contributing

Have any feedback or suggestions? Please consider opening issues or contributing through pull requests!


## Credits

* The `pydvs_event_image_streamer` is based on the implementation of [pyDVS](https://github.com/chanokin/pyDVS), presented in: García, Garibaldi Pineda, et al. "pydvs: An extensible, real-time dynamic vision sensor emulator using off-the-shelf hardware." <i>2016 IEEE Symposium Series on Computational Intelligence (SSCI)</i>. IEEE, 2016.
