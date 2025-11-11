from locust import HttpUser, task, between
import random

class LibraryUser(HttpUser):
    """
    Mô phỏng hành vi người dùng thư viện
    """
    # Thời gian chờ giữa các request (giây)
    wait_time = between(1, 3)
    
    def on_start(self):
        """
        Chạy 1 lần khi user bắt đầu
        - Tạo user mới
        - Login để lấy token
        """
        # Tạo email random để tránh conflict
        self.email = f"user_{random.randint(1000, 9999)}@test.com"
        
        # Register
        response = self.client.post("/auth/register", json={
            "name": "Test User",
            "email": self.email,
            "password": "password123"
        })
        
        if response.status_code == 201:
            # Login để lấy token
            response = self.client.post("/auth/login", json={
                "email": self.email,
                "password": "password123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.headers = {'Authorization': f'Bearer {self.token}'}
            else:
                self.token = None
                self.headers = {}
        else:
            self.token = None
            self.headers = {}
    
    @task(5)  # Weight = 5 (chạy nhiều nhất)
    def get_books(self):
        """Test GET /books với pagination"""
        page = random.randint(1, 3)
        self.client.get(f"/books/?type=page&page={page}&per_page=10")
    
    @task(3)  # Weight = 3
    def get_book_detail(self):
        """Test GET /books/{id}"""
        book_id = random.randint(1, 50)  # Giả sử có 50 books
        self.client.get(f"/books/{book_id}")
    
    @task(2)  # Weight = 2
    def search_books(self):
        """Test search books by author"""
        authors = ["Martin", "John", "Jane", "Test"]
        author = random.choice(authors)
        self.client.get(f"/books/author?name={author}&page=1&per_page=5")
    
    @task(1)  # Weight = 1 (ít nhất)
    def get_my_info(self):
        """Test GET /users/me (cần auth)"""
        if self.token:
            self.client.get("/users/me", headers=self.headers)


class AdminUser(HttpUser):
    """
    Mô phỏng hành vi admin
    """
    wait_time = between(2, 5)
    
    def on_start(self):
        """Login as admin"""
        # Giả sử đã có admin account
        response = self.client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "admin123"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('access_token')
            self.headers = {'Authorization': f'Bearer {self.token}'}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def get_all_loans(self):
        """Test GET /loans (admin only)"""
        if self.token:
            self.client.get("/loans/", headers=self.headers)
    
    @task(2)
    def get_all_users(self):
        """Test GET /users (admin only)"""
        if self.token:
            self.client.get("/users/", headers=self.headers)
    
    @task(1)
    def add_book(self):
        """Test POST /books (admin only)"""
        if self.token:
            book_id = random.randint(1000, 9999)
            self.client.post("/books/", 
                json={
                    "title": f"Book {book_id}",
                    "author": "Test Author",
                    "is_available": True
                },
                headers=self.headers
            )


# =====================================
# ADVANCED: Custom test scenarios
# =====================================

from locust import LoadTestShape

# class StepLoadShape(LoadTestShape):
#     def __init__(self):
#         super().__init__()
#         print(">>> ĐANG CHẠY KIỂU TẢI: StepLoadShape")
        
#     step_time = 60  # Mỗi bước kéo dài 60s
#     step_load = 50  # Tăng 50 users mỗi bước
#     spawn_rate = 20  # Tạo 20 users/giây
#     time_limit = 240  # Tổng thời gian test 4 phút
    
#     def tick(self):
#         run_time = self.get_run_time()
        
#         if run_time > self.time_limit:
#             return None
        
#         current_step = run_time // self.step_time
#         return (int(current_step + 1) * self.step_load, self.spawn_rate)


class SpikeLoadShape(LoadTestShape):
    def __init__(self):
        super().__init__()
        print(">>> ĐANG CHẠY KIỂU TẢI: SpikeLoadShape")
        
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time < 60:
            # Giai đoạn 1: 10 users
            return (10, 10)
        elif run_time < 120:
            # Giai đoạn 2: SPIKE lên 200 users
            return (200, 20)
        elif run_time < 180:
            # Giai đoạn 3: Giảm về 10 users
            return (10, 10)
        else:
            return None