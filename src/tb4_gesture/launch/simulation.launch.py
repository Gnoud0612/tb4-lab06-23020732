"""Empty local world plus the unmodified official TurtleBot 4 Lite spawn."""

import os
from pathlib import Path
from ament_index_python.packages import get_package_share_directory as share
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import UnlessCondition
from launch_ros.actions import Node


def start(context):
    root = Path(share("tb4_gesture"))
    resources = []
    for package in [
        "turtlebot4_description",
        "irobot_create_description",
        "irobot_create_ignition_bringup",
    ]:
        path = Path(share(package))
        resources += [str(path.parent), str(path / "worlds")]
    cmd = ["ign", "gazebo", "-r", "-s", "-v", "2"]
    cmd += [str(root / "worlds/gesture_arena.sdf")]
    spawn = (
        Path(share("turtlebot4_ignition_bringup")) / "launch/turtlebot4_spawn.launch.py"
    )
    return [
        SetEnvironmentVariable("IGN_GAZEBO_RESOURCE_PATH", os.pathsep.join(resources)),
        SetEnvironmentVariable(
            "IGN_GAZEBO_SYSTEM_PLUGIN_PATH",
            os.pathsep.join(
                [
                    os.environ.get("IGN_GAZEBO_SYSTEM_PLUGIN_PATH", ""),
                    os.environ.get("LD_LIBRARY_PATH", ""),
                ]
            ),
        ),
        ExecuteProcess(cmd=cmd, output="screen"),
        TimerAction(
            period=12.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        "ign",
                        "gazebo",
                        "-g",
                        "--gui-config",
                        str(root / "config/gui.config"),
                    ],
                    condition=UnlessCondition(LaunchConfiguration("headless")),
                    output="screen",
                )
            ],
        ),
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            name="clock_bridge",
            arguments=["/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock"],
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(spawn)),
            launch_arguments={
                "model": "lite",
                "rviz": "false",
                "nav2": "false",
                "slam": "false",
                "localization": "false",
                "use_sim_time": "true",
                "x": "0",
                "y": "0",
                "yaw": "0",
            }.items(),
        ),
    ]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "world", default_value="gesture_arena", choices=["gesture_arena"]
            ),
            DeclareLaunchArgument(
                "headless", default_value="false", choices=["true", "false"]
            ),
            OpaqueFunction(function=start),
        ]
    )
