# Bài thực hành 06 — TurtleBot 4 và cử chỉ tay

```bash
# Cài đặt và build một lần, tại thư mục repository đã clone
sudo apt update
sudo apt install -y ros-humble-turtlebot4-simulator ros-humble-irobot-create-nodes \
  ros-humble-cv-bridge python3-venv python3-colcon-common-extensions \
  python3-pytest python3-yaml python3-pil
bash scripts/setup_mediapipe.sh
bash scripts/build.sh
```

```bash
# Terminal 1: mở Gazebo
# Thay đường dẫn cd nếu clone ở thư mục khác
cd ~/workspaces/workspace/lab06
bash scripts/simulation.sh
```

```bash
# Terminal 2: mở webcam và điều khiển, bỏ qua Wave
cd ~/workspaces/workspace/lab06
bash scripts/control.sh skip_wave:=true
```

```bash
# Kiểm tra webcam khi chưa mở control/preview
cd ~/workspaces/workspace/lab06
bash scripts/check_webcam.sh
```

```bash
# Kết thúc: Ctrl+C ở terminal control, rồi dừng simulator
cd ~/workspaces/workspace/lab06
bash scripts/stop_sim.sh
```
