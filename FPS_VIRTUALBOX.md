# FPS webcam máy ảo và nhận diện Wave

Vẫn sử dụng webcam trực tiếp qua **Devices → Webcams**, không cần máy chủ truyền ảnh Windows.

## Các thay đổi trong chương trình

- Yêu cầu MJPEG native, ảnh 320×240 và buffer 1; camera thread luôn lấy ảnh mới nhất.
- Giữ FPS yêu cầu 15 vì thử 30 không tăng đáng kể FPS thực trên máy này.
- Wave dùng các mẫu AI Open_Palm có score từ 0,55, tối thiểu 5 mẫu, chuyển động ngang đủ lớn và ít nhất 2 lần đổi chiều. Cửa sổ lịch sử tối đa 4 giây.
- Khung AI không chắc chắn trong khoảng ngắn không xóa cả chuỗi, nhưng không được tính là mẫu vẫy và không kéo dài chuỗi. Khoảng cách giữa hai mẫu hợp lệ quá 0,9 giây sẽ xóa chuỗi. Mất tay, nắm tay hoặc đổi sang cử chỉ tĩnh khác cũng xóa chuỗi.
- UI hiển thị thêm số mẫu và số lần đổi chiều để biết vì sao Wave chưa đạt. Các kiểm thử bao gồm 2–3 fps, score 0,62, một khung bị phân loại None, nhiễu, mất tay và chuyển động chỉ một chiều.
- Wave chỉ **chọn** hành vi chào. Vẫn phải giơ ngón cái xác nhận. Dừng bằng Open Palm, hủy bằng Closed Fist và watchdog 0,65 giây giữ nguyên.

## Cách thử bản đã sửa

Dừng control cũ bằng Ctrl+C, không mở preview song song:

```bash
cd ~/workspaces/workspace/lab06
bash scripts/control.sh camera_index:=0 camera_fps:=15 camera_buffers:=1
```

Nếu chưa mở Gazebo hoặc chưa chuẩn bị robot, làm trước các bước simulation/prepare trong README. Xòe tay nhìn rõ rồi đưa **cả bàn tay ngang** trái–phải–trái trong khoảng 2–3 giây, không chỉ xoay cổ tay tại một chỗ. Khi hiện `SELECTED | greet`, đổi sang ngón cái và giữ. Nếu chỉ luyện nhận diện, dùng `bash scripts/perception.sh`; chế độ này không điều khiển robot, phải dừng nó trước khi mở control.

## Đo FPS thực

Dừng control/preview bằng Ctrl+C trước khi đo:

```bash
cd ~/workspaces/workspace/lab06
bash scripts/measure_camera.sh
```

Đọc `camera.observed_fps`, không dùng `reported_fps` làm số đo thực. Kết quả lưu tại `evidence/fps_probe_current.json`. Chương trình chỉ đọc camera, không phát lệnh robot. Cần build package trước trên máy clone mới.

Đo ngày 27/10/2026, không chạy Gazebo hay AI: 320×240 MJPEG, buffer4, yêu cầu30: khoảng 2,89 fps; buffer1, yêu cầu30: khoảng 3,13 fps; buffer1, yêu cầu15: khoảng 3,12 fps. MJPEG chưa giải mã cũng chỉ khoảng 3,06 fps. 640×360 còn khoảng 1,01 fps. Đây là các phép đo ngắn riêng biệt, không bảo đảm mức tăng ổn định giữa các lần thử. Chưa đạt 15–20 fps.

## Thử cấu hình VirtualBox trên Windows

Ubuntu hiện nhận webcam qua nhánh OHCI **12 Mb/s** mặc dù máy ảo có cả EHCI. Đây là dấu hiệu cần thử cấu hình USB phía host; chưa đủ kết luận là nguyên nhân duy nhất. Không thể thay bộ điều khiển USB của VirtualBox bằng lệnh ROS trong Ubuntu.

Cách thử 1, vẫn giữ máy ảo đang mở:

1. Dừng control/preview trong Ubuntu.
2. Bỏ tích **Devices → Webcams → HD Webcam**.
3. Mở PowerShell **trên Windows** và chạy:

```powershell
$vb = "$env:ProgramFiles\Oracle\VirtualBox\VBoxManage.exe"
& $vb list runningvms
& $vb list webcams
```

4. Thay `TEN_MAY_AO` bằng đúng tên hiện ở lệnh đầu, thay `.0` nếu muốn chọn alias camera khác từ lệnh thứ hai:

```powershell
& $vb controlvm "TEN_MAY_AO" webcam attach .0 "MaxFramerate=30;MaxPayloadTransferSize=16384"
```

5. Trở lại Ubuntu, đợi thiết bị xuất hiện và chạy `bash scripts/measure_camera.sh`. Nếu không đọc được hoặc FPS kém hơn, bỏ tích camera rồi tích lại trong Devices → Webcams để trở về cách kết nối mặc định. MaxFramerate chỉ là giới hạn trên, không ép camera tạo đủ 30 fps. Payload lớn không được mọi guest hỗ trợ.

Cách thử 2 nếu cách 1 chưa cải thiện:

1. Lưu công việc và **Shut Down Ubuntu** hoàn toàn, không chọn Save State.
2. Trong VirtualBox Manager, chọn máy ảo → **Settings → USB → Enable USB Controller → USB 3.0 (xHCI)** nếu có. Extension Pack trên Windows phải tương ứng phiên bản VirtualBox.
3. Mở lại Ubuntu, kết nối webcam qua Devices → Webcams, đo lại bằng `measure_camera.sh`.
4. Có thể xem `lsusb -t`: so sánh nhánh/tốc độ camera trước và sau. Có xHCI không bảo đảm webcam tự chạy nhanh; dùng FPS đo được để đánh giá. Nếu cấu hình gây lỗi, tắt máy và khôi phục lựa chọn USB trước đó.

Không thay USB controller khi đang quay. Sau khi thay hoặc khởi động lại máy, cần chạy simulation và prepare lại theo QUAY_VIDEO.md.

Nguồn: [Oracle VirtualBox webcam passthrough](https://docs.oracle.com/en/virtualization/virtualbox/7.0/user/AdvancedTopics.html#webcam-passthrough), [OpenCV Video I/O properties](https://docs.opencv.org/4.10.0/d4/d15/group__videoio__flags__base.html).

Ngón cái cần được nhận ban đầu ở score ≥0,70 qua ít nhất 3 ảnh. Sau khi đã ổn định, cùng nhãn Thumb_Up được duy trì ở score ≥0,55 trên các ảnh mới cách nhau không quá 0,65 giây. Nhờ đó score giảm nhẹ không làm hành vi bị ngắt. Mất tay, đổi nhãn, ảnh cũ hoặc score thấp hơn ngưỡng sẽ xóa trạng thái duy trì; cơ chế dừng mất tín hiệu giữ nguyên. Nếu hành vi bị ngắt khi đang chờ hoàn thành, lời nhắc demo tự quay về chọn/xác nhận lại.
