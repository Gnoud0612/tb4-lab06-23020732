# Tự quay video bài 06 — webcam trực tiếp trong VirtualBox

Chạy tất cả lệnh dưới đây trong Ubuntu. Không cần truyền camera từ Windows. Các lệnh dùng thư mục bài hiện tại `~/workspaces/workspace/lab06`; nếu clone ở nơi khác thì thay đường dẫn này.

## 1. Kết nối và kiểm tra webcam

Đóng Camera, Zoom, Teams hoặc ứng dụng đang dùng webcam trên Windows. Trong cửa sổ VirtualBox trên Windows, chọn **Devices → Webcams → camera laptop**. Giữ kết nối này trong suốt demo.

Mở terminal Ubuntu:

```bash
cd ~/workspaces/workspace/lab06
source scripts/env.bash
ls /dev/video*
bash scripts/check_webcam.sh
```

Kết quả cần có `passed: true`, `frame_received: true` cho ít nhất một thiết bị. `/dev/video1` không đọc được ảnh vẫn bình thường nếu `/dev/video0` đã đọc được. Nếu thiết bị đọc được là `/dev/video2`, dùng `camera_index:=2` ở bước 4.

Chỉ một chương trình dùng webcam mỗi lúc. Đóng cửa sổ preview và dừng recognition cũ bằng Ctrl+C trước khi kiểm tra. Không chạy kiểm tra webcam trong lúc node nhận diện đang dùng camera.

## 2. Build và khởi động một phiên Gazebo mới — Terminal A

Nếu phiên simulator cũ còn chạy, dừng control/ghi hình cũ bằng Ctrl+C tại đúng terminal của chúng. Sau đó:

```bash
cd ~/workspaces/workspace/lab06
bash scripts/stop_sim.sh
bash scripts/build.sh
bash scripts/simulation.sh
```

Giữ Terminal A mở. Đợi Gazebo hiện robot, thường GUI mở sau khoảng 12 giây. World chỉ có sàn và robot, không cần bản đồ/Nav2. Nếu muốn dùng phiên headless cũ thì chỉ mở `bash scripts/gui.sh` ở terminal riêng; không chạy thêm simulator thứ hai. Hướng dẫn chính này dùng phiên mới để robot trở về vị trí ban đầu.

## 3. Chuẩn bị robot — Terminal B

```bash
cd ~/workspaces/workspace/lab06
bash scripts/prepare.sh
```

Chạy một lần cho mỗi phiên simulator mới. Đợi script báo hoàn thành; robot phải rời đế sạc, đế sạc được xóa khỏi arena. Không chạy lại `prepare.sh` giữa các hành vi.

## 4. Mở nhận diện và điều khiển — vẫn Terminal B

```bash
bash scripts/control.sh camera_index:=0 camera_fps:=15
```

Nếu phiên simulator chưa chuẩn bị, control sẽ tự chạy prepare một lần trước khi bật nhận diện. Không cần chạy `perception.sh` riêng. Lệnh trên mở nhận diện, điều khiển và hướng dẫn demo. Kiểm tra cửa sổ webcam có ảnh thật, tên cử chỉ, confidence và trạng thái robot. Dòng vàng `DEMO:` nhắc thao tác tiếp theo. Gazebo và webcam phải cùng nhìn thấy được; phóng robot đủ lớn để quan sát chuyển động, giữ nguyên kích thước cửa sổ khi quay.

Webcam passthrough trên máy này đã đo khoảng **3,4 fps thực** ở 320×240 dù yêu cầu 15 hoặc 20 fps. Con số 15 trong lệnh là yêu cầu tới camera. Không cần tăng tiếp nếu FPS thực không đổi. Bật đủ ánh sáng, để một bàn tay rõ trong khung, giữ cử chỉ chọn/xác nhận khoảng **1–2 giây**. Vẫy rõ ngang trái–phải–trái trong khoảng 2–3 giây; đưa cả bàn tay ngang, không chỉ xoay cổ tay hoặc xòe tay đứng yên. Nếu vẫn khó nhận, xem FPS_VIRTUALBOX.md và dòng số mẫu/lần đổi chiều trên UI.

Có thể thử cử chỉ trước khi quay. Nếu đã thử làm checklist tiến lên hoặc robot đã di chuyển, Ctrl+C ở control; khi bắt đầu lượt chính hãy chạy lại control để checklist về đầu. Nếu muốn đưa robot về gốc, dừng simulator và làm lại bước 2–4. Không cần sử dụng bàn phím để lái robot.

## 5. Bắt đầu quay — Terminal C

```bash
cd ~/workspaces/workspace/lab06
bash scripts/record_demo.sh
```

Script ghi hai cửa sổ Gazebo + webcam cạnh nhau, MP4 H.264, không âm thanh, không phụ đề thêm. Nếu đã có video cùng tên, script tự tạo tên có thời gian để giữ bản cũ. Terminal sẽ in đường dẫn file. Không thu nhỏ, đóng, thay đổi kích thước hoặc che hai cửa sổ khi quay. Video xuất 10 fps; số này không làm webcam có thêm ảnh thật.

## 6. Thứ tự cử chỉ trong video

| Bước | Tay của bạn | Kết quả phải thấy |
|---|---|---|
| 1 | Vẫy bàn tay mở ngang trái–phải–trái | `SELECTED`, hành vi `greet`; robot chưa chạy |
| 2 | Giơ ngón cái và giữ trong khung | `RUNNING`: robot xoay trái–phải, sau đó `COMPLETED` |
| 3 | Giơ một ngón trỏ, đợi `SELECTED`; đổi sang ngón cái và giữ | Tiến–lùi **4 cặp**, tổng **8 đoạn**; đợi `COMPLETED` |
| 4 | Giơ hai ngón chữ V, đợi `SELECTED`; đổi sang ngón cái và giữ | Robot đi **hết một vòng tròn**; đợi `COMPLETED` |
| 5 | Chữ V → ngón cái; khi robot đang chạy thì xòe tay đứng yên | `STOPPED`, robot dừng |
| 6 | Chữ V → ngón cái; khi robot đang chạy thì nắm tay | `IDLE`, hủy hành vi và robot dừng |
| 7 | Chữ V → ngón cái; khi robot đang chạy thì đưa tay hẳn khỏi hình | `STOPPED` do `control signal lost` |

Sau xác nhận, **giữ Thumb Up trong hình liên tục cho đến khi hành vi hoàn thành**. Bỏ tay sớm hoặc đổi sang nhãn không nhận được sẽ kích hoạt dừng mất tín hiệu. Một vòng tròn cần khoảng 24 giây thời gian mô phỏng; máy ảo chậm thì chờ lâu hơn, dựa vào `COMPLETED` thay vì bấm giờ.

Đừng xòe tay đứng yên khi muốn robot tiếp tục chạy: Open Palm là lệnh dừng. Sau khi dừng/hủy/mất tín hiệu, muốn chạy lại phải chọn hành vi rồi xác nhận lại. Lựa chọn hết hạn sau 15 giây nếu chưa xác nhận. Giữ nguyên Thumb Up không làm robot tự lặp hành vi. Nếu dòng vàng chưa chuyển bước thì thực hiện lại đúng thao tác được nhắc; không phát lệnh String tổng hợp hoặc teleop để thay cử chỉ.

Trong phần robot chuyển động, không dùng bàn phím lái và không đặt goal bằng chuột. Bàn phím chỉ dùng mở/dừng chương trình hoặc ghi hình.

## 7. Kết thúc và kiểm tra video

Khi dòng vàng báo `ALL DEMO STEPS COMPLETE`, về **Terminal C**, gõ **q** và đợi FFmpeg thoát. Có thể Ctrl+C một lần nếu cần. Không tắt cưỡng bức terminal khi file chưa ghi xong.

Mở file vừa ghi trong `submission/` để xem lại. Kiểm tra đủ webcam + nhãn, robot, ba chuyển động hoàn chỉnh và ba thử nghiệm dừng/hủy/mất tín hiệu. Log bổ sung:

```bash
cd ~/workspaces/workspace/lab06
python3 -m json.tool evidence/demo_checklist.json
```

Mục tiêu là `passed: true`, `completed_steps: 18`, `required_steps: 18`. Checklist chỉ hỗ trợ kiểm tra; vẫn phải xem video thực tế.

Có thể kiểm tra lỗi giải mã toàn bộ file bằng lệnh sau (thay đúng tên nếu script đã thêm thời gian):

```bash
source scripts/env.bash
ffmpeg -v error -xerror -i submission/demo_lab06_23020732.mp4 -f null -
```

Không có thông báo lỗi và mã thoát 0 là giải mã thành công. Nếu ứng dụng Ubuntu thiếu bộ giải mã H.264, thử mở bằng VLC; không đổi đuôi file để sửa lỗi. Video tải lên Drive phải phát được sau khi Drive xử lý xong.

Dừng **Terminal B** bằng Ctrl+C, rồi:

```bash
bash scripts/stop_sim.sh
```

Ảnh nhận diện thực được lưu lần đầu từng nhãn tại `evidence/gesture_*.png`; log tại `evidence/recognition.jsonl`, `evidence/behavior.json` và `evidence/demo_checklist.json`. Dùng ảnh chụp từ lượt quay cuối nếu ảnh lưu trước chưa rõ. Bổ sung ảnh thực nghiệm và link Drive/GitHub vào báo cáo Word rồi xuất PDF.

## 8. Khi có lỗi

- **Không có `/dev/video0`:** kiểm tra lại Devices → Webcams của VirtualBox; Ubuntu phải nhận thiết bị trước khi mở control.
- **Đang thấy preview mà kiểm tra báo fail:** đóng preview hoặc control cũ, chỉ để một tiến trình mở camera. Chạy lại kiểm tra rồi mới mở control.
- **Nhận cử chỉ chập chờn / robot dừng:** tăng sáng, để cả bàn tay trong hình, giữ ngón cái rõ; xem nhãn/FPS trên cửa sổ. Sau khi dừng phải chọn/xác nhận lại; không tắt watchdog để quay.
- **`FAULT`:** xem lý do trên cửa sổ/Terminal B, đợi sensor hoạt động và kiểm tra đã `prepare.sh`. Nếu robot ra xa vùng demo hoặc trạng thái không rõ, khởi động phiên simulator mới theo bước 2–4.
- **Script quay không tìm thấy cửa sổ:** mở Gazebo GUI và control có `display:=true`; không dùng `headless` mà chưa mở `gui.sh`. Nếu báo thiếu ffmpeg/xdotool, cài hai gói này theo README.
- **Video cũ chưa hoàn chỉnh:** giữ bản cũ để đối chiếu, mở lượt quay mới; script tự đổi tên nếu file đích đã tồn tại.

## Thử các chức năng khác, bỏ qua Wave

Dừng control cũ bằng Ctrl+C, giữ Gazebo và robot đã prepare, rồi:

```bash
bash scripts/control.sh skip_wave:=true
```

Hướng dẫn bắt đầu từ Pointing Up → Thumb Up để tiến–lùi, tiếp theo Victory → Thumb Up để đi tròn, rồi thử dừng/hủy/mất tín hiệu. Giữ Thumb Up trong hình khi robot đang chạy. Chế độ này chỉ bỏ phần chào khỏi checklist; node điều khiển và điều kiện xác nhận giữ nguyên. Checklist riêng `evidence/demo_checklist_without_wave.json` có 15 bước, không ghi đè checklist demo đầy đủ. Khi quay đủ đề, chạy lại với `skip_wave:=false` (mặc định).
