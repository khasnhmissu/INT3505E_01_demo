## Client–Server
**Nguyên tắc:**  
Tách biệt giữa client (giao diện người dùng) và server (xử lý dữ liệu và logic nghiệp vụ), cho phép client và server phát triển độc lập

Chạy server
![server]("./lesson2/static/demo/server.jpg")
Dùng Postman như client để test
![client]("./lesson2/static/demo/client.jpg")

## Uniform Interface
**Nguyên tắc:** 
Giao diện chung cho toàn hệ thống, giúp tương tác giữa các thành phần nhất quán, giúp người phát triển dễ hiểu và phát triển hệ thống

Thiết kế tên resource, API theo nguyên tắc
![uniform_interface]("./lesson2/static/demo/uniform_interface.jpg")

## Stateless
**Nguyên tắc:**
Mỗi request từ client đến server phải tự chứa đủ thông tin để server hiểu và xử lý mà không cần nhớ trạng thái trước đó, giúp hệ thống dễ scale, đơn giản và tránh phụ thuộc trạng thái phiên làm việc.

Sử dụng token để lưu trữ phiên người dùng, sử dụng trong các request để server biết mà server không cần lưu thông tin
![stateless1]("./lesson2/static/demo/stateless1.jpg")
Ví dụ xem thông tin thì gửi token của phiên đăng nhập
![stateless2]("./lesson2/static/demo/stateless2.jpg")
Nếu không có sẽ thông báo lỗi
![stateless3]("./lesson2/static/demo/stateless3.jpg")


## Cacheable
**Nguyên tắc:**
Phản hồi từ server có thể được lưu tạm (cache) để tăng hiệu suất và giảm tải, giúp giảm thời gian phản hồi và tiết kiệm băng thông.

Các request sử dụng tham số để cache hit
![cacheable1]("./lesson2/static/demo/cacheable1.jpg")
![cacheable2]("./lesson2/static/demo/cacheable2.jpg")
Server sẽ xử lí và trả về cache để các cache có thể lưu lại
![cacheable3]("./lesson2/static/demo/cacheable3.jpg")
![cacheable4]("./lesson2/static/demo/cacheable4.jpg")
![cacheable5]("./lesson2/static/demo/cacheable5.jpg")
