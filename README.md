# event_camera_emulation

Emulate event camera outputs using RGB camera images.

## Usage

Event images can be obtained by instantiating a `EventCameraEmulator` object, and calling the `get_events_image` function, providing two consecutive images (numpy.ndarray objects):
```
e_camera_emulator = EventCameraEmulator()
event_image = e_camera_emulator.get_events_image_rgb(current_image, previous_image)
```

## Dependencies
* `OpenCV`

For ROS functionalities:
* `rospy`
* `cv_bridge`
