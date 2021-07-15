from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup(
    packages=['event_camera_emulation'],
    package_dir={'event_camera_emulation': 'event_camera_emulation'}
)

setup(**d)
