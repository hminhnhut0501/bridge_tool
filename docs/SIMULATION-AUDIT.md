# Kiểm thử giả lập và đánh giá điểm yếu — 2026-10-06

**Cập nhật: 4 lỗi P1 đã được sửa và chạy lại PASS — xem [bản khắc phục](P1-REMEDIATION.md). Ba lỗi P2 còn tồn tại. Nội dung dưới đây ghi nhận đánh giá trước khi sửa; JSON liên kết phản ánh lần chạy mới nhất.**

**Kết luận tại thời điểm đánh giá ban đầu: cần sửa 4 lỗi P1 trước khi đưa lên VPS vận hành 24/7.** Bộ kiểm thử chức năng vẫn pass, nhưng kiểm thử đối kháng đã tái hiện 7 điểm yếu. Chưa sửa logic production trong đợt đánh giá này.

## Phạm vi và kết quả

Mọi kịch bản đối kháng và E2E mới chạy trên SQLite, tài khoản thử nghiệm và thư mục rclone crypt riêng trong thư mục tạm. Không sử dụng mật khẩu ứng dụng đang chạy; không thay đổi dữ liệu instance local hiện có. Mã hóa/giải mã rclone là thật; Telegram dùng mock, lỗi Google được tiêm vào adapter. Chưa kiểm thử tài khoản Telegram/Google thật, quota thật, Docker runtime hoặc reboot Ubuntu/VPS.

| Hạng mục | Kết quả |
|---|---|
| Backend hiện có | 22/22 pass, 22,64 giây; gồm SIGKILL 10/50/90% và restart |
| Kịch bản bảo vệ bổ sung | 4/4 pass |
| Kịch bản đối kháng | 7 điểm yếu tái hiện; không có lỗi harness |
| Web E2E instance riêng | 1/1 pass: đăng nhập, nguồn, topics, settings, job crypt, library, desktop/mobile |
| Build React/TypeScript | Pass |

Bằng chứng máy đọc được: [adversarial-audit.json](../data/reports/adversarial-audit.json), [Web E2E](../data/reports/audit-web/result.json), [history](../data/reports/history.json), [workers](../data/reports/workers.json). Ảnh giao diện: [desktop](../data/reports/audit-web/dashboard-desktop.png), [mobile](../data/reports/audit-web/dashboard-mobile.png).

## Điểm yếu đã tái hiện

P1: ảnh hưởng tính đầy đủ backup, khả năng tự phục hồi hoặc tài nguyên service; nên chặn triển khai 24/7. P2: cần khắc phục nhưng phạm vi hoặc điều kiện kích hoạt hẹp hơn. Đây là phân loại vận hành của đợt đánh giá, không phải CVSS.

| ID | Mức | Bằng chứng và tác động | Hướng sửa |
|---|---|---|---|
| F01 | P1 | Đổi topics trong lúc batch scan đang chờ: checkpoint kết thúc ở 12 nhưng chỉ có 9/12 job; thiếu message 1, 3, 5. Batch cũ ghi đè tiến độ đã reset, làm bỏ sót video thuộc topic vừa chọn. Recent scan chỉ cứu được phần trong cửa sổ gần đây. | Thêm generation cho scan; chỉ batch cùng generation được ingest/advance checkpoint. Hủy batch cũ khi đổi lựa chọn. |
| F02 | P1 | File `.incomplete` sai nội dung nhưng cùng size: lần đầu RETRY_WAIT, hai lần retry thủ công đều FAILED; không có final. Retry tiếp tục kiểm tra lại cùng temp hỏng. | Phân biệt temp hỏng với final conflict. Với temp đã xác định hỏng, tạo attempt mới và tải lại; giữ bảo vệ không ghi đè final. |
| F03 | P1 | Tiêm một lỗi SQLite `OperationalError` tại claim: worker dừng, job vẫn QUEUED, health vẫn HTTP 200. Không có supervisor tự khởi động lại task. | Bao phủ claim bằng recovery/backoff; supervise worker/scanner. Readiness phải kiểm tra task còn sống; lỗi fatal phải khiến process thoát để service manager restart. |
| F05 | P1 | 20 login đồng thời từ client giả lập khác nhau tạo tối đa 16 hash task đồng thời. Argon2 cấu hình 64 MiB/hash tương ứng khoảng 1 GiB bộ nhớ hash nếu thực hiện thật. Giới hạn theo IP chưa giới hạn tài nguyên toàn cục. | Semaphore toàn cục cho Argon2, backlog có giới hạn, trả 429 khi quá tải; kiểm tra cấu hình trusted proxy và giới hạn tại reverse proxy. |
| F04 | P2 | Login bằng mật khẩu cũ đang verify khi reset password: sau reset vẫn tạo được session mới, `/auth/me` trả 200. Thu hồi session hiện có không chặn verify đang chạy. | Dùng auth generation; kiểm tra lại hash/generation trước khi tạo session, trong transaction phù hợp. |
| F06 | P2 | Thay nội dung ciphertext qua crypt bằng payload khác cùng size: reconcile báo checked=1, missing=0, unexpected=0; job vẫn COMPLETED dù SHA khác. | Bổ sung deep reconcile đọc giải mã + SHA-256, có lịch và giới hạn băng thông. Hiện tại reconcile chỉ xác minh tồn tại/size, không chứng minh toàn vẹn nội dung. |
| F07 | P2 | Ba attempt mất kết nối để lại 3 temp object; 2 path cũ không còn được job hiện tại tham chiếu. Dữ liệu tạm có thể tăng liên tục và chiếm quota. | Lưu registry attempt/path; cleanup có TTL với điều kiện sở hữu rõ ràng và không còn active; hiển thị dung lượng temp và cảnh báo quota. |

Vị trí liên quan: `api.py` login và cập nhật topics; `database.py` ingest checkpoint; `engine.py` scan, worker, kiểm tra temp và reconcile. Các kịch bản tái hiện nằm trong [audit_simulations.py](../scripts/audit_simulations.py).

**Giới hạn F05:** concurrency hash được đo bằng verifier thay thế có độ trễ; 1 GiB là ước lượng theo tham số Argon2, không phải RAM đã cấp phát hay một lần OOM thật. Số thread/CPU và cách proxy xác định IP sẽ thay đổi kết quả trên VPS.

## Các cơ chế đã vượt qua thử nghiệm

- Mất mạng giữa stream: RETRY_WAIT, retry hoàn thành, SHA-256 khớp.
- 20 thao tác cạnh tranh khi gặp FloodWait 300 giây: chỉ 1 API call thực sự, mọi thao tác còn lại bị chặn; deadline được giữ khi tạo lại controller. Không chờ 300 giây ngoài đời: test xác minh deadline và việc từ chối gọi API.
- Google 429 giả lập: RETRY_WAIT → RETRY_WAIT → FAILED theo ngưỡng retry, backoff khoảng 5,12 / 16,00 / 52,47 giây, concurrency vẫn 1. Thời điểm retry được đẩy nhanh trong DB thử nghiệm; không phải thử quota Google thật.
- Sink crypt bị giới hạn 1 MiB/s: payload 8 MiB mất 8,14 giây; sau 200 ms producer chỉ tạo 512 KiB. Hash khớp, cho thấy backpressure không đọc hết video vào RAM.

## Hiệu năng local

- 500.000 message metadata giả lập → 50.000 job: 35,72 giây; RAM peak 65 MiB, tăng khoảng 3,61 MiB; DB khoảng 42,05 MiB. Không có truyền video hoặc traffic Telegram/Google trong phép đo này.
- Core + crypt thật, 256 MiB/worker: 1 worker 3,643 giây, RAM process tree peak 152,44 MiB; 2 worker 3,602 giây, RAM peak 218,89 MiB. Tổng throughput local khoảng 70,27 và 142,14 MiB/s. Bao gồm hai lượt đọc giải mã kiểm tra hash.
- Dung lượng đĩa vận hành đo được khoảng 366 KiB / 539 KiB, không tính đích chứa ciphertext local. Các số liệu này không dự báo throughput mạng hoặc Google Drive trên VPS.

Ngoài các lỗi tái hiện, cần tính chi phí bandwidth khi verify đầy đủ đọc lại file hai lần; kiểm tra độ trễ event loop dưới SQLite contention và khả năng job ưu tiên thấp bị chậm khi nguồn live liên tục. Đây là rủi ro cần đo thêm, chưa được khẳng định là lỗi bằng kịch bản trong đợt này.

## Chạy lại

Tại root dự án:

```sh
RCLONE_CONFIG="$PWD/data/local-crypt/rclone.conf" .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/audit_simulations.py
.venv/bin/python scripts/audit_web.py
.venv/bin/python scripts/history_benchmark.py
RCLONE_CONFIG="$PWD/data/local-crypt/rclone.conf" .venv/bin/python scripts/worker_benchmark.py
cd frontend
npm run build
```

Script đối kháng xuất tất cả verdict để thu thập bằng chứng; exit code 0 không có nghĩa mọi kịch bản pass. Phải đọc `WEAKNESS_REPRODUCED`/`HARNESS_ERROR` trong JSON. Script Web E2E tự tạo và dừng server riêng.

Thứ tự khắc phục đề xuất: F01/F02 (đầy đủ và phục hồi backup), F03 (worker supervision/readiness), F05 (giới hạn tài nguyên xác thực), sau đó F04/F06/F07. Chạy lại đúng kịch bản thất bại thành regression test sau mỗi bản sửa; tiếp theo mới kiểm thử tích hợp Telegram/Google thật và triển khai VPS.
