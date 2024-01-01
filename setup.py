from setuptools import setup, find_packages

setup(
    name='event_camera_emulation',
    version='0.1.1',
    description='The event_camera_emulation package',
    author='Ahmed Faisal Abdelrahman',
    author_email='ahmed.abdelrahman@outlook.de',
    maintainer='Ahmed Faisal Abdelrahman',
    maintainer_email='ahmed.abdelrahman@outlook.de',
    url='https://github.com/af-a/event_camera_emulation',
    package_dir={'': 'common'},
    packages=find_packages(include=['event_camera_emulation'], 
                           where='common'),
    license='MIT',
    install_requires=[
      'opencv-python>=4.8.1',
      'numpy',
      'scikit-image',
    ],
    setup_requires=['wheel'],
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
    zip_safe=False,
)
