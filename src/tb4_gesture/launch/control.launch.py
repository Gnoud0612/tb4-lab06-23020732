from launch import LaunchDescription
from launch.conditions import IfCondition
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("camera_index", default_value="0"),
            DeclareLaunchArgument("display", default_value="true"),
            DeclareLaunchArgument("guide", default_value="true"),
            DeclareLaunchArgument("skip_wave", default_value="false"),
            DeclareLaunchArgument("camera_fps", default_value="15"),
            DeclareLaunchArgument("camera_url", default_value=""),
            DeclareLaunchArgument("camera_width", default_value="320"),
            DeclareLaunchArgument("camera_height", default_value="240"),
            DeclareLaunchArgument("camera_buffers", default_value="1"),
            Node(
                package="tb4_gesture",
                executable="demo_guide",
                output="screen",
                condition=IfCondition(LaunchConfiguration("guide")),
                parameters=[
                    {
                        "skip_wave": ParameterValue(
                            LaunchConfiguration("skip_wave"), value_type=bool
                        )
                    }
                ],
            ),
            Node(
                package="tb4_gesture", executable="robot_behavior_node", output="screen"
            ),
            Node(
                package="tb4_gesture",
                executable="gesture_recognition_node",
                output="screen",
                parameters=[
                    {
                        "camera_width": ParameterValue(
                            LaunchConfiguration("camera_width"), value_type=int
                        ),
                        "camera_height": ParameterValue(
                            LaunchConfiguration("camera_height"), value_type=int
                        ),
                        "camera_buffers": ParameterValue(
                            LaunchConfiguration("camera_buffers"), value_type=int
                        ),
                        "camera_fps": ParameterValue(
                            LaunchConfiguration("camera_fps"), value_type=int
                        ),
                        "camera_url": ParameterValue(
                            LaunchConfiguration("camera_url"), value_type=str
                        ),
                        "camera_index": ParameterValue(
                            LaunchConfiguration("camera_index"), value_type=int
                        ),
                        "display": ParameterValue(
                            LaunchConfiguration("display"), value_type=bool
                        ),
                    }
                ],
            ),
        ]
    )
