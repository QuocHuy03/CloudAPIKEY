# 🔑 Admin Panel - Key Management System

## 📋 Tổng quan

Admin Panel là giao diện web để quản lý các API keys trong hệ thống CloudApi. Cho phép thêm, sửa, xóa và theo dõi trạng thái của các keys.

## 🚀 Truy cập Admin Panel

```
http://localhost:5000/admin/
```

## 🎯 Các chức năng chính

### 1. Dashboard (`/admin/`)
- **Thống kê tổng quan**: Hiển thị số lượng keys theo từng module
- **Trạng thái keys**: Active, Expired, Used up
- **Hoạt động gần đây**: Hiển thị 5 hoạt động mới nhất
- **Thao tác nhanh**: Thêm key, xem danh sách, làm mới thống kê

### 2. Danh sách Keys (`/admin/keys`)
- **Hiển thị tất cả keys**: Với thông tin chi tiết
- **Lọc và tìm kiếm**: Theo module, trạng thái, key/device_id
- **Phân trang**: Hiển thị 10 keys mỗi trang
- **Thao tác**: Xem chi tiết, chỉnh sửa, xóa

### 3. Thêm Key mới (`/admin/keys/add`)
- **Form thêm key**: Với validation đầy đủ
- **Xem trước**: Hiển thị thông tin key trước khi lưu
- **Các trường**:
  - Key (bắt buộc)
  - Module (bắt buộc)
  - Device ID (tùy chọn)
  - Trạng thái (Active/Inactive)
  - Ngày hết hạn
  - Số lượt tối đa
  - Số lượt đã sử dụng

### 4. Chỉnh sửa Key (`/admin/keys/<module>/<key>/edit`)
- **Form chỉnh sửa**: Không thể thay đổi key và module
- **Cập nhật thông tin**: Device ID, trạng thái, hạn sử dụng, v.v.

### 5. Xem chi tiết Key (`/admin/keys/<module>/<key>/status`)
- **Thông tin đầy đủ**: Tất cả thông tin về key
- **Trạng thái hiện tại**: Active, expired, usage
- **Thao tác**: Chỉnh sửa, xóa, quay lại

### 6. Activity Log (`/admin/activity`) ⭐ MỚI
- **Theo dõi hoạt động**: Tất cả thao tác CRUD trên keys
- **Thống kê hoạt động**: Tổng số, theo loại, theo module
- **Lọc và tìm kiếm**: Theo hành động, module, thời gian
- **Chi tiết thay đổi**: Xem giá trị cũ/mới khi cập nhật
- **Export CSV**: Xuất dữ liệu activity log

## 🔧 API Endpoints

### GET `/admin/api/stats`
Trả về thống kê tổng quan của tất cả modules.

**Response:**
```json
{
  "success": true,
  "data": {
    "voice": {
      "total": 25,
      "active": 20,
      "expired": 3,
      "used_up": 2
    },
    "image": {
      "total": 15,
      "active": 12,
      "expired": 2,
      "used_up": 1
    }
  }
}
```

### GET `/admin/api/keys?module=<module>`
Trả về danh sách keys, có thể lọc theo module.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "key": "abc123",
      "module": "voice",
      "device_id": "device001",
      "status": "active",
      "expires": "12/31/2024",
      "max_usage": 100,
      "usage_count": 25,
      "remaining": 75,
      "is_expired": false
    }
  ]
}
```

### POST `/admin/keys/add`
Thêm key mới.

**Request:**
```json
{
  "key": "new_key_123",
  "module": "voice",
  "device_id": "device001",
  "status": "active",
  "expires": "12/31/2024",
  "max_usage": 100,
  "usage_count": 0
}
```

### POST `/admin/keys/<module>/<key>/edit`
Chỉnh sửa key.

**Request:**
```json
{
  "device_id": "new_device",
  "status": "inactive",
  "expires": "01/01/2025",
  "max_usage": 200,
  "usage_count": 50
}
```

### POST `/admin/keys/<module>/<key>/delete`
Xóa key.

**Response:**
```json
{
  "success": true,
  "message": "Xóa key thành công"
}
```

### GET `/admin/activity`
Trang hiển thị activity log với phân trang và lọc.

### GET `/admin/api/activity`
API endpoint để lấy activity log.

**Parameters:**
- `page`: Số trang (mặc định: 1)
- `action`: Lọc theo hành động (CREATE_KEY, UPDATE_KEY, DELETE_KEY)
- `module`: Lọc theo module
- `limit`: Số lượng records (mặc định: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "action": "CREATE_KEY",
      "key_value": "abc123",
      "module": "voice",
      "old_values": null,
      "new_values": {"key": "abc123", "module": "voice", "status": "active"},
      "user_ip": "127.0.0.1",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2024-09-12 10:30:00"
    }
  ]
}
```

### GET `/admin/api/activity/stats`
API endpoint để lấy thống kê activity.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_activities": 150,
    "actions": {
      "CREATE_KEY": 50,
      "UPDATE_KEY": 80,
      "DELETE_KEY": 20
    },
    "modules": {
      "voice": 60,
      "image": 40,
      "music": 30
    },
    "recent_24h": 25
  }
}
```

## 📊 Modules được hỗ trợ

- `voice` - Text to Speech
- `image` - Image Generation
- `clone_voice` - Voice Cloning
- `music` - Music Generation
- `make_video_ai` - Video Creation
- `merger_video_ai` - Video Merging

## 🎨 Giao diện

### Thiết kế
- **Responsive**: Hoạt động tốt trên desktop và mobile
- **Modern UI**: Sử dụng Bootstrap 5 và Font Awesome
- **Dark theme**: Navigation bar với theme tối
- **Color coding**: Màu sắc phân biệt trạng thái keys

### Tính năng UI
- **Real-time updates**: Thống kê tự động cập nhật
- **Search & Filter**: Tìm kiếm và lọc keys
- **Pagination**: Phân trang cho danh sách dài
- **Progress bars**: Hiển thị mức độ sử dụng
- **Tooltips**: Hướng dẫn sử dụng
- **Alerts**: Thông báo thành công/lỗi
- **Activity Logging**: Theo dõi tất cả hoạt động
- **Export Functions**: Xuất dữ liệu ra CSV

## 🔒 Bảo mật

- **Validation**: Kiểm tra dữ liệu đầu vào
- **CSRF Protection**: Bảo vệ chống tấn công CSRF
- **Input sanitization**: Làm sạch dữ liệu đầu vào
- **Error handling**: Xử lý lỗi an toàn

## 🚀 Cách sử dụng

1. **Khởi động server**:
   ```bash
   python app.py
   ```

2. **Truy cập admin panel**:
   ```
   http://localhost:5000/admin/
   ```

3. **Thêm key mới**:
   - Click "Thêm Key mới"
   - Điền thông tin
   - Click "Thêm Key"

4. **Quản lý keys**:
   - Xem danh sách tại "Danh sách Keys"
   - Lọc theo module hoặc trạng thái
   - Chỉnh sửa hoặc xóa keys

## 🛠️ Phát triển

### Cấu trúc thư mục
```
templates/admin/
├── base.html          # Template cơ sở
├── dashboard.html     # Trang dashboard
├── keys_list.html     # Danh sách keys
├── add_key.html       # Thêm key
├── edit_key.html      # Chỉnh sửa key
└── key_status.html    # Chi tiết key

static/admin/
├── css/
│   └── admin.css      # Styles tùy chỉnh
└── js/
    └── admin.js       # JavaScript functions

routes/
└── admin.py           # Admin routes
```

### Thêm tính năng mới
1. Thêm route trong `routes/admin.py`
2. Tạo template trong `templates/admin/`
3. Cập nhật CSS/JS nếu cần
4. Test tính năng

## 📝 Ghi chú

- Admin panel sử dụng SQLite database (`keys.db`)
- Tất cả thao tác đều được ghi log
- Hỗ trợ real-time updates mỗi 30 giây
- Có thể export dữ liệu ra CSV (sẽ được thêm)

## 🐛 Troubleshooting

### Lỗi thường gặp

1. **404 Not Found**: Kiểm tra URL và routes
2. **500 Internal Error**: Kiểm tra database connection
3. **Template not found**: Kiểm tra đường dẫn templates
4. **Static files not loading**: Kiểm tra thư mục static

### Debug
```bash
# Chạy với debug mode
python app.py

# Kiểm tra logs
tail -f app.log
```

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra logs
2. Xem console browser
3. Kiểm tra network requests
4. Liên hệ developer