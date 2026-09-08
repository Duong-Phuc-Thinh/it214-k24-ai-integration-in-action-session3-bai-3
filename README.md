# BÀI TẬP 3: XÂY DỰNG VÀ SỬA LỖI CẤU HÌNH CONFIG SERVER

## 1. PHÂN TÍCH LỖI VÀ BẢN CHẤT VẤN ĐỀ

### Lỗi 1: Thiếu Annotation `@EnableConfigServer` trên Class Main
- **Nguyên nhân & Hậu quả:** Nốt ứng dụng chỉ khai báo `@SpringBootApplication` thì Spring Boot chỉ khởi chạy một Web Application thông thường. Nó không tự động kích hoạt các Auto-Configuration của Spring Cloud Config Server (`ConfigServerAutoConfiguration`, `ConfigServerMvcConfiguration`).
- **Vì sao gây lỗi 500/404:** Khi thiếu annotation này, các REST Controllers nội bộ xử lý định tuyến cấu hình (như `/{name}/{profile}`) không được khởi tạo. Request từ `restaurant-service` tới Config Server sẽ không tìm thấy handler phù hợp hoặc bị lỗi xử lý nội bộ.
- **Cách khắc phục:** Thêm `@EnableConfigServer` từ package `org.springframework.cloud.config.server.EnableConfigServer` trên class `ConfigServerApplication`.

### Lỗi 2: Sai Cấu Hình `git.uri` và `default-label`
- **Lỗi `git.uri`:** Đường dẫn `https://github.com/foodx/config-repo` thiếu hậu tố `.git`. Mặc dù một số Git server có cơ chế tự redirect, Spring Cloud Config sử dụng JGit/Git CLI để clone/fetch repository nên chuẩn định dạng đuôi `.git` giúp đảm bảo khả năng kết nối chính xác và ổn định.
- **Lỗi `default-label`:** Cấu hình đang đặt `default-label: master`, trong khi repository thực tế đặt tên nhánh mặc định là `main`. Khi nhận request mà client không truyền label, Config Server sẽ tìm kiếm nhánh `master` trên Git repository -> Git checkout thất bại -> ném ra `NoSuchLabelException` / Internal Server Error (HTTP 500).
- **Cách khắc phục:** Sửa `uri` thành `https://github.com/foodx/config-repo.git` và `default-label` thành `main`.

---

## 2. CODE ĐÃ SỬA

### File `ConfigServerApplication.java`
```java
package com.foodx.configserver;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.config.server.EnableConfigServer;

@SpringBootApplication
@EnableConfigServer // Kích hoạt vai trò Spring Cloud Config Server
public class ConfigServerApplication {
    public static void main(String[] args) {      SpringApplication.run(ConfigServerApplication.class, args);
    }
}
```

### File `application.yml`
```yaml
server:
  port: 8888

spring:
  cloud:
    config:
      server:
        git:
          uri: https://github.com/foodx/config-repo.git
          default-label: main
```

---

## 3. MÔ TẢ LUỒNG XỬ LÝ REQUEST

Khi `restaurant-service` gửi request `GET /restaurant-service/prod` tới Config Server:

1. **Tiếp nhận Request:** Config Server tiếp nhận HTTP GET request tại đường dẫn `/restaurant-service/prod`.
2. **Phân tích Endpoint:** DispatcherServlet phân tích URI và chuyển request tới `EnvironmentController` của Config Server:
   - `{application}` = `restaurant-service`
   - `{profile}` = `prod`
   - `{label}` = `main` (mặc định lấy từ `default-label` do client không truyền label).
3. **Truy xuất Git Repository:** Config Server (thông qua JGit Environment Repository) thực hiện fetch/pull dữ liệu từ Git URL `https://github.com/foodx/config-repo.git` tại nhánh `main`.
4. **Tìm kiếm & Phối hợp File Cấu hình:** Server tìm kiếm các file trong repo khớp với quy tắc tên:
   - `restaurant-service-prod.yml` / `restaurant-service-prod.properties`
   - `restaurant-service.yml` / `restaurant-service.properties`
   - `application-prod.yml` / `application-prod.properties`
   - `application.yml` / `application.properties`
5. **Gộp Cấu hình (Property Consolidation):** Server đọc và hợp nhất các file cấu hình theo thứ tự ưu tiên (file cụ thể override file chung).
6. **Trả về Kết quả:** Config Server đóng gói dữ liệu thành đối tượng `Environment` (chứa danh sách `PropertySource`) và serialize thành định dạng JSON gửi về cho `restaurant-service` với mã HTTP 200 OK.

---

## 4. HƯỚNG DẪN KIỂM THỬ ĐỘC LẬP

### Cách 1: Chạy Script Python Kiểm Thử Giả Lập
Chạy file `main.py` đi kèm để kiểm thử luồng phản hồi REST API chuẩn của Config Server:
```bash
python main.py
```

### Cách 2: Kiểm Thử Config Server Thật bằng cURL / Browser / Postman
1. Khởi chạy ứng dụng Spring Boot Config Server.
2. Mở terminal hoặc trình duyệt và gọi API:
   ```bash
   curl -X GET http://localhost:8888/restaurant-service/prod
   ```
3. Hoặc truy cập dạng file cấu hình trực tiếp:
   ```bash
   curl -X GET http://localhost:8888/restaurant-service-prod.yml
   ```
4. Kiểm tra mã phản hồi thu được là `200 OK` và response JSON chứa thông tin cấu hình đúng.