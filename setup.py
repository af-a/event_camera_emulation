#!/usr/bin/env python3

import os
import glob

from setuptools import find_packages, setup

package_name = 'event_camera_emulation'

setup(
    name=package_name,
    version='1.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob.glob(os.path.join('launch', '*launch.[pxy][yma]*')))
    ],
    install_requires=['setuptools'],
    # install_requires=['wheel'],
    author='Ahmed Faisal Abdelrahman',
    author_email='ahmed.abdelrahman@outlook.de',
    maintainer='Ahmed Abdelrahman',
    maintainer_email='ahmed.abdelrahman@outlook.de',
    description='Package for emulating event camera data using standard RGB images',
    license='MIT',
    install_requires=[
      'opencv-python>=4.8.1',
      'numpy',
      'scikit-image',
    ],
    extras_require={
        'test': [
            'pytest',
        ],
    },
    # entry_points={
    #     'console_scripts': [
    #         'todo_node = event_camera_emulation.todo_node:main'
    #     ],
    # },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
    ],
    keywords=[
        'Event camera',
        'Event-based vision',
        'Neuromorphic',
    ],
    zip_safe=True,
)
