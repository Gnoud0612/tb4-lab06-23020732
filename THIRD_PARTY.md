# Sources and third-party components

- MediaPipe Gesture Recognizer model: Google, official float16 version 1 bundle, URL/SHA256 in `models/manifest.json`. MediaPipe source is Apache-2.0; model use remains governed by the terms/metadata published with Google's distribution. See https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer .
- MediaPipe Python 0.10.21: Google / MediaPipe authors, Apache-2.0. OpenCV 4.10: OpenCV authors, Apache-2.0. NumPy/SciPy: respective BSD licenses. Dependencies keep their own licenses.
- TurtleBot 4 / Create 3 simulator: Clearpath Robotics and iRobot; the official packages and descriptions are included through installed launch files, not republished model meshes in this repository. Upstream: https://github.com/turtlebot/turtlebot4_simulator and https://github.com/iRobotEducation/create3_sim .
- `undock.py`, `sim_profile.py`, `local_underlay.bash`, and `stop_sim.sh` are adapted from this student's earlier TurtleBot 4 lab implementation. Simulator behavior and service interfaces come from the official Humble packages. Local underlay libraries are environment-only and excluded from the source ZIP.
- Images under local `evidence/model_test_inputs/` are Google MediaPipe reference test assets (URLs recorded in `model_smoke_test.json`). They are not webcam recordings and are excluded from the GitHub source ZIP.
- New gesture filtering, temporal Wave, behavior state machine and ROS application nodes are provided under this repository's Apache-2.0 LICENSE.
