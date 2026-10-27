from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    defaults = {
        "camera_index": ("0", int),
        "camera_fps": ("15", int),
        "camera_width": ("320", int),
        "camera_height": ("240", int),
        "camera_buffers": ("1", int),
        "camera_url": ("", str),
        "display": ("true", bool),
    }
    return LaunchDescription(
        [
            *[
                DeclareLaunchArgument(k, default_value=v[0])
                for k, v in defaults.items()
            ],
            Node(
                package="tb4_gesture",
                executable="gesture_recognition_node",
                output="screen",
                parameters=[
                    {
                        k: ParameterValue(LaunchConfiguration(k), value_type=t)
                        for k, (_, t) in defaults.items()
                    }
                ],
            ),
        ]
    )
