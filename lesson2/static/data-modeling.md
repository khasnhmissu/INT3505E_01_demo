# Library Management System - Data Modeling

## Bước 1: Các entity chính gồm: Book - User - Loan (phiếu mượn)

## Bước 2: Xác định các mối quan hệ giữa các entity

Book - Loan (1:N) :  Mỗi phiếu mượn tương ứng với một sách cụ thể
User - Loan (1:N) :  Một thành viên có thể có nhiều phiếu mượn
Loan được xác định bởi ID của chính nó kết hợp id của sách và id người dùng

## Bước 3: Vẽ ERD

![ERD](diagram.png)

## Bước 4: Thiết kế resoucre

USER
users/ : liệt kê người dùng, thêm người dùng vào hệ thống
users/me: xem thông tin của bản thân
users/{id} : xem thông tin của người dùng cụ thể, update thông tin người dùng, xoá người dùng
users/{id}/loans : xem các phiếu mượn của người dùng cụ thể

BOOK
books/ : liệt kê sách, thêm sách
books/{id} : xem thông tin của sách cụ thể, update thông tin của sách, xoá sách
books/author?name=X : lọc sách theo tác giả

LOAN
loans/ : xem các phiếu mượn
loans/{id} : xem thông tin phiếu mượn cụ thể

