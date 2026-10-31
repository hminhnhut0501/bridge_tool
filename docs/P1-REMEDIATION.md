# Khắc phục 4 lỗi P1 — 2026-10-06

Đã sửa F01, F02, F03 và F05 trong báo cáo đối kháng. Kết quả chạy lại cả bốn kịch bản: PASS. Ba lỗi P2 F04/F06/F07 vẫn còn; tích hợp Telegram/Google thật và nghiệm thu VPS chưa được thực hiện.

| Lỗi | Thay đổi | Bằng chứng chạy lại |
|---|---|---|
| F01: đổi topics khi scan | Schema v2 thêm `scan_generation`; thay topics hoặc yêu cầu scan mới tăng generation. Batch đang chờ latest ID, ingest checkpoint và kết thúc scan chỉ được cập nhật cùng generation. CLI scan cũng tăng generation. | 12/12 job, không thiếu message; test bổ sung reset khi latest ID đang chờ pass. |
| F02: temp hỏng chặn retry | Kiểm tra final vẫn giữ nguyên chính sách không ghi đè. Temp có size/hash sai được bỏ qua, tạo attempt mới và tải lại. Lỗi kết nối storage vẫn theo retry/backoff. | RETRY_WAIT → COMPLETED; final tồn tại. Test bảo vệ final conflict hiện có tiếp tục pass. |
| F03: worker chết nhưng health OK | Supervisor cho worker/scanner/maintenance tự khởi động lại sau lỗi với backoff 1 giây; theo dõi job bị gián đoạn để trả về RETRY_WAIT, giữ ý định cancel. Ghi lỗi không phụ thuộc SQLite. Health trả 503 khi chưa chạy, task chết, supervisor đang phục hồi hoặc SQLite lỗi. | Worker còn sống, job COMPLETED; health 503 trong recovery, 200 sau recovery. Test bổ sung lỗi DB sau claim cũng phục hồi thành công. |
| F05: hash login không giới hạn | Mỗi process tối đa 2 Argon2 task; không có backlog chờ hash, quá tải trả 429 + Retry-After. Shield giữ slot tới khi thread thực sự xong ngay cả khi request bị cancel. Giới hạn 5 lần/IP/15 phút vẫn áp dụng. | 20 client: peak 2 hash, 18 request nhận 429; test cancel request không làm vượt 2 slot pass. |

Với Argon2 64 MiB/hash, ngân sách hash đồng thời khoảng 128 MiB, chưa tính phần còn lại của process. Đây là tính theo cấu hình, không phải phép đo RAM tổng service. Kiến trúc vẫn yêu cầu một process; tăng số process sẽ nhân giới hạn này.

## Kiểm chứng

- **30/30 test backend pass trong 28,40 giây**, gồm 22 test gốc và 8 regression mới; gồm hard SIGKILL/restart, giữ final conflict, topic race, migration v1→v2, lỗi DB và cancel login.
- Web E2E instance riêng pass: đăng nhập, discovery, crypt job thật, topics/settings, library và desktop/mobile.
- Ruff pass. Không đổi frontend trong bản sửa này.
- [Kết quả đối kháng hiện tại](../data/reports/adversarial-audit.json): 4 safety pass + 4 P1 pass; 3 P2 còn tái hiện.
- [Regression tests](../tests/test_p1.py), [báo cáo gốc](SIMULATION-AUDIT.md).

Schema v1 được snapshot sang `.pre-v2.sqlite3` trước migration. Schema v2 không tương thích với binary v1; nếu rollback phải dừng service và phục hồi snapshot tương ứng, không mở DB v2 bằng bản cũ. Bản local được restart để nạp core mới; không upload VPS.

Supervisor giúp phục hồi exception và báo trạng thái, chưa phát hiện task bị treo vô hạn mà không ném exception. Các giới hạn của thử nghiệm local trong báo cáo gốc vẫn áp dụng.
