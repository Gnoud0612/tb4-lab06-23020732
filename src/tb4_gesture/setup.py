from glob import glob
from setuptools import find_packages, setup

setup(
    name="tb4_gesture",
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/tb4_gesture"]),
        ("share/tb4_gesture", ["package.xml"]),
        ("share/tb4_gesture/launch", glob("launch/*.launch.py")),
        ("share/tb4_gesture/worlds", glob("worlds/*.sdf")),
        ("share/tb4_gesture/config", glob("config/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Nguyen Tung Duong",
    maintainer_email="student@example.com",
    description="TurtleBot4 hand gesture HRI",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "gesture_recognition_node=tb4_gesture.gesture_recognition_node:main",
            "robot_behavior_node=tb4_gesture.robot_behavior_node:main",
            "flat_profile=tb4_gesture.sim_profile:main",
            "demo_guide=tb4_gesture.demo_guide:main",
            "undock=tb4_gesture.undock:main",
        ]
    },
)
