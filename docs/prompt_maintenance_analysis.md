# PROMPT NGHIÊN CỨU & THIẾT KẾ CHUẨN KIẾN TRÚC HỆ THỐNG BẢO TRÌ THIẾT BỊ (CMMS)

> **Hướng dẫn sử dụng:** Copy toàn bộ nội dung dưới đây và dán vào Claude để nhận được bản tư vấn kiến trúc chuẩn hóa cao nhất.

---

```markdown
Bạn là một chuyên gia Kiến trúc sư Hệ thống (System Architect) và Chuyên gia tư vấn Giải pháp ERP / CMMS (Computerized Maintenance Management System) công nghiệp theo chuẩn SAP PM và ISO 55000.

Tôi đang xây dựng phân hệ Quản lý Bảo trì Thiết bị (Maintenance Management Module) cho một nhà máy sản xuất, tích hợp chặt chẽ với hệ thống Kho (WMS) và Mua sắm (Procurement) sẵn có. 

Dưới đây là toàn bộ bối cảnh, quy trình nghiệp vụ và các bài toán thực tế (kèm câu hỏi hóc búa từ Mentor) mà hệ thống bắt buộc phải giải quyết. Hãy phân tích chuyên sâu và thiết kế lại Kiến trúc CSDL (Database Schema chuẩn PostgreSQL) và Quy trình Vòng đời (State Machine).

---

### I. CÁC MODULE HỆ THỐNG HIỆN HỮU (CORE DATABASE)
Hệ thống đã có sẵn 7 bảng cốt lõi (không được phá vỡ logic):
1. `parties`: Thông tin đối tác/cá nhân gốc (`party_id`, `party_type`, `display_name`, `phone`, `email`, `address`).
2. `suppliers`: Nhà cung cấp, kế thừa 1:1 từ `parties` (`supplier_id`, `supplier_code`).
3. `user_accounts`: Tài khoản người dùng, liên kết 1:1 với `parties` (`user_id`, `party_id`, `username`, `password_hash`).
4. `warehouses`: Kho chứa (`warehouse_id`, `warehouse_code`, `warehouse_name`).
5. `locations`: Vị trí/Kệ hàng theo cây phân cấp cha-con (`location_id`, `warehouse_id`, `parent_location_id`, `location_code`, `can_store_inventory`).
6. `products`: Danh mục phụ tùng/vật tư (`product_id`, `sku`, `name`, `unit`, `price`).
7. `inventories`: Tồn kho lưu theo vị trí cụ thể (`inventory_id`, `location_id`, `product_id`, `quantity_on_hand`, `reserved_quantity`).
8. `inventory_movements`: Lịch sử mọi giao dịch xuất/nhập/điều chuyển kho (`movement_id`, `movement_type`, `reference_code`, `product_id`, `from_location_id`, `to_location_id`, `quantity`, `performed_by`, `occurred_at`).

---

### II. QUY TRÌNH BẢO TRÌ 3 GIAI ĐOẠN & CÁC BÀI TOÁN THỰC TẾ CẦN GIẢI QUYẾT

#### Giai đoạn 1: Tiếp nhận & Xử lý Yêu cầu Bảo trì (Maintenance Request)
- **Đối tượng:** Người vận hành máy (Operator) khi thấy máy rung, ồn, kẹt phôi, dừng đột ngột... sẽ tạo Yêu cầu.
- **Bài toán 1 (Bản nháp):** Nếu Operator đang tạo dở, chưa chắc chắn hoặc bận việc thì xử lý sao?
  $\rightarrow$ Cần trạng thái `DRAFT` (lưu nháp, hệ thống chưa gửi thông báo cho ai). Khi bấm "Gửi" mới sang `SUBMITTED`.
- **Bài toán 2 (Cảnh báo Quản lý):** Quản lý ca nhận được khi nào?
  $\rightarrow$ Nhận tức thì qua Notification khi sang `SUBMITTED`. Nếu mức độ là `URGENT` (dừng chuyền), kích hoạt cảnh báo đỏ trên màn hình điều hành.
- **Bài toán 3 (Sàng lọc - Screening & Duplicate):**
  - Nếu báo sai, lỗi thao tác (chưa bật nguồn) hoặc 2 người cùng báo 1 máy hỏng $\rightarrow$ Quản lý bấm `REJECT` + ghi rõ lý do để báo lại cho Operator.
  - Nếu đúng sự cố kỹ thuật $\rightarrow$ Quản lý bấm `APPROVE` $\rightarrow$ Hệ thống tự động sinh **Work Order**. Quản lý chỉ định **Kỹ thuật viên Trưởng (`lead_technician_id`)** và hạn chót hoàn thành (`planned_end_at`).

#### Giai đoạn 2: Lập Lệnh Sửa chữa, Phân công Task & Quản lý Vật tư
- **Bài toán 4 (Phân công nhiều người & chia đầu việc):**
  - Một Work Order sự cố lớn không thể chỉ có 1 người làm. Làm sao phân KTV A tháo máy chẩn đoán điện, KTV B thay linh kiện cơ khí, KTV C chạy thử?
  - Ai là người tạo và chia các task nhỏ này? (KTV Trưởng là người trực tiếp tại hiện trường có chuyên môn cao nhất chia task, không phải Quản lý xưởng).
- **Bài toán 5 (Xung đột lịch & Chuyển giao việc dở dang):**
  - Khi phân công, nếu KTV đang bận việc khác thì hệ thống cảnh báo thế nào?
  - Nếu phân công rồi nhưng vài ngày sau KTV bận đột xuất / ốm / nghỉ ca $\rightarrow$ Cơ chế chuyển giao task (Reassign) cho KTV mới hoạt động ra sao mà không làm mất lịch sử giờ công (`work_order_logs`) KTV cũ đã thực hiện trước đó?
- **Bài toán 6 (Đồng bộ trạng thái WO ngược về Request):**
  - Operator và Quản lý xưởng không có chuyên môn sâu để vào xem chi tiết kỹ thuật của Work Order. Làm sao họ theo dõi được tiến độ từ màn hình Request ban đầu?
  - Cơ chế đồng bộ tự động: Khi WO chuyển `ASSIGNED` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `WAITING_PARTS` $\rightarrow$ `TESTING` $\rightarrow$ `READY_FOR_ACCEPTANCE`, Request phải hiển thị đúng trạng thái tương ứng theo thời gian thực.
- **Bài toán 7 (Xác định tồn kho, số lượng lấy ra và số thiếu cần mua):**
  - KTV kê khai số lượng cần dùng (`required_quantity`).
  - **Trường hợp Kho ĐỦ hàng:** Thủ kho giữ chỗ (`reserved_quantity`), sau đó xuất kho thực tế qua `inventory_movements` (`MAINTENANCE_ISSUE`), cập nhật `issued_quantity`. Không phát sinh mua sắm!
  - **Trường hợp Kho THIẾU hàng:** Kho giữ phần có sẵn, hệ thống tự động tính số lượng thiếu:
    $$\text{Số lượng thiếu cần mua} = \text{required\_quantity} - (\text{reserved\_quantity} + \text{issued\_quantity})$$
  - Hệ thống tự động kích hoạt Đề nghị mua hàng (`purchase_requests`) cho đúng số lượng thiếu đó. Work Order chuyển sang `WAITING_PARTS`.

#### Giai đoạn 3: Mua sắm, Nghiệm thu Kỹ thuật & Khép kín Lệnh
- **Bài toán 8 (Phê duyệt mua sắm theo hạn mức):**
  - Đề nghị mua phụ tùng phải qua luồng duyệt đa cấp (`purchase_approvals`): Trưởng bộ phận $\rightarrow$ Kế toán $\rightarrow$ Giám đốc dựa trên tổng tiền dự tính (`total_estimated_amount`).
- **Bài toán 9 (Nhận hàng, Kiểm định chất lượng & Cấp phát nối tiếp):**
  - Khi NCC giao hàng đến: Kho lập phiếu nhận (`goods_receipts`).
  - KTV phụ trách kiểm định kỹ thuật phụ tùng mới (`goods_receipt_items.inspected_by` và `inspection_status` = `PASSED` / `FAILED`).
  - Phụ tùng đạt chuẩn tự động sinh phiếu nhập kho (`PURCHASE_RECEIPT`), sau đó thủ kho xuất tiếp cho Work Order để KTV có đủ 100% phụ tùng lắp vào máy.
- **Bài toán 10 (Nghiệm thu chạy thử & Vòng lặp Rework):**
  - KTV sửa xong, chạy thử ghi nhận kết quả (`root_cause`, `repair_action`, `test_result`).
  - Ai là người audit nghiệm thu? $\rightarrow$ Quản lý / Operator ra máy kiểm tra thực tế.
  - **Nếu nghiệm thu KHÔNG ĐẠT:** Bấm từ chối nghiệm thu $\rightarrow$ Work Order tự động quay lại trạng thái `IN_PROGRESS` để KTV sửa chữa lại.
  - **Nếu nghiệm thu ĐẠT:** Quản lý xác nhận `ACCEPTED` $\rightarrow$ Hệ thống tự động đóng Work Order (`CLOSED`), đóng Request (`CLOSED`), và máy móc chuyển trạng thái về `OPERATIONAL` (sẵn sàng sản xuất).

---

### III. YÊU CẦU ĐẦU RA ĐỐI VỚI BẠN (OUTPUT DELIVERABLES)

1. **Phân tích Kiến trúc Dữ liệu & Chuẩn hóa 3NF:**
   - Chỉ ra các quan hệ khóa ngoại (Foreign Keys) để không bị vòng lặp tam giác (Diamond Dependency) và không bị dư thừa liên kết kép (Double Reference).
   - Thiết kế bảng phân công công việc (`work_order_tasks`), nhật ký giờ công (`work_order_logs`), và bảng vật tư (`work_order_materials`).
2. **Sơ đồ Trạng thái (State Machine):**
   - Định nghĩa toàn bộ danh sách Enum/Status chuẩn hóa cho: `equipment`, `maintenance_requests`, `work_orders`, `work_order_tasks`, `work_order_materials`, `purchase_*`, `goods_receipt_*`.
3. **Mã nguồn SQL DDL chuẩn PostgreSQL (hoặc DBML):**
   - Đầy đủ các bảng thuộc module Bảo trì & Mua sắm kết nối hoàn hảo với 7 bảng hệ thống gốc.
   - Sử dụng kiểu dữ liệu `BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY`, `TIMESTAMPTZ`, `NUMERIC(18, 4)`.
   - Có đầy đủ các ràng buộc `REFERENCES` và `CHECK` logic.
```
