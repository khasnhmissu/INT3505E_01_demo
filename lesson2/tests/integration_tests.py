import unittest
import json
from app import create_app
from app.extension import db
from app.models import Book, User, Loan
from werkzeug.security import generate_password_hash

class TestAPIIntegration(unittest.TestCase):
    
    def setUp(self):
        """Setup test client và database"""
        # QUAN TRỌNG: Truyền 'testing' vào create_app
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Tạo admin user
            admin = User(
                name="Admin",
                email="admin@test.com",
                password=generate_password_hash("admin123"),
                role="admin"
            )
            # Tạo normal user
            user = User(
                name="User",
                email="user@test.com",
                password=generate_password_hash("user123"),
                role="user"
            )
            db.session.add_all([admin, user])
            db.session.commit()
    
    def tearDown(self):
        """Cleanup sau mỗi test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def login_as_admin(self):
        """Helper: đăng nhập admin và lấy token"""
        response = self.client.post('/auth/login',
            data=json.dumps({"email": "admin@test.com", "password": "admin123"}),
            content_type='application/json')
        data = json.loads(response.data)
        return data['access_token']
    
    def login_as_user(self):
        """Helper: đăng nhập user và lấy token"""
        response = self.client.post('/auth/login',
            data=json.dumps({"email": "user@test.com", "password": "user123"}),
            content_type='application/json')
        data = json.loads(response.data)
        return data['access_token']
    
    # INTEGRATION TEST - Auth Flow
    def test_register_login_flow(self):
        """Test luồng đăng ký -> đăng nhập"""
        # Đăng ký
        response = self.client.post('/auth/register',
            data=json.dumps({
                "name": "New User",
                "email": "newuser@test.com",
                "password": "password123"
            }),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
        # Đăng nhập
        response = self.client.post('/auth/login',
            data=json.dumps({
                "email": "newuser@test.com",
                "password": "password123"
            }),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
    
    def test_protected_endpoint_without_token(self):
        """Test truy cập endpoint cần auth mà không có token"""
        response = self.client.get('/users/me')
        self.assertEqual(response.status_code, 401)
    
    def test_protected_endpoint_with_token(self):
        """Test truy cập endpoint với token hợp lệ"""
        token = self.login_as_user()
        response = self.client.get('/users/me',
            headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(response.status_code, 200)
    
    # INTEGRATION TEST - Books CRUD
    def test_add_book_as_admin(self):
        """Test admin thêm sách"""
        token = self.login_as_admin()
        response = self.client.post('/books/',
            data=json.dumps({
                "title": "Test Book",
                "author": "Test Author",
                "is_available": True
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'})
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('id', data)
    
    def test_add_book_as_user_forbidden(self):
        """Test user thường không thể thêm sách"""
        token = self.login_as_user()
        response = self.client.post('/books/',
            data=json.dumps({
                "title": "Test Book",
                "author": "Test Author"
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'})
        
        self.assertEqual(response.status_code, 403)
    
    def test_get_books_pagination(self):
        """Test get books với pagination"""
        token = self.login_as_admin()
        
        # Thêm nhiều sách
        with self.app.app_context():
            for i in range(15):
                book = Book(title=f"Book {i}", author=f"Author {i}")
                db.session.add(book)
            db.session.commit()
        
        # Test page-based pagination
        response = self.client.get('/books/?type=page&page=1&per_page=10')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['data']), 10)
        self.assertTrue(data['pagination']['has_next'])
    
    # INTEGRATION TEST - Checkout & Return Flow
    def test_checkout_return_flow(self):
        """Test luồng mượn -> trả sách"""
        admin_token = self.login_as_admin()
        user_token = self.login_as_user()
        
        # Admin thêm sách
        response = self.client.post('/books/',
            data=json.dumps({
                "title": "Checkout Test Book",
                "author": "Author",
                "is_available": True
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {admin_token}'})
        book_id = json.loads(response.data)['id']
        
        # User mượn sách
        response = self.client.post('/loans/checkout',
            data=json.dumps({"book_id": book_id}),
            content_type='application/json',
            headers={'Authorization': f'Bearer {user_token}'})
        self.assertEqual(response.status_code, 201)
        loan_id = json.loads(response.data)['loan_id']
        
        # Kiểm tra sách đã không available
        with self.app.app_context():
            book = Book.query.get(book_id)
            self.assertFalse(book.is_available)
        
        # Admin trả sách
        response = self.client.put(f'/loans/return/{loan_id}',
            headers={'Authorization': f'Bearer {admin_token}'})
        self.assertEqual(response.status_code, 200)
        
        # Kiểm tra sách đã available lại
        with self.app.app_context():
            book = Book.query.get(book_id)
            self.assertTrue(book.is_available)
    
    def test_checkout_unavailable_book(self):
        """Test mượn sách đã được mượn"""
        admin_token = self.login_as_admin()
        user_token = self.login_as_user()
        
        # Thêm sách
        with self.app.app_context():
            book = Book(title="Book", author="Author", is_available=False)
            db.session.add(book)
            db.session.commit()
            book_id = book.id
        
        # Thử mượn sách không available
        response = self.client.post('/loans/checkout',
            data=json.dumps({"book_id": book_id}),
            content_type='application/json',
            headers={'Authorization': f'Bearer {user_token}'})
        
        self.assertEqual(response.status_code, 400)
    
    # INTEGRATION TEST - Token Refresh
    def test_refresh_token_flow(self):
        """Test làm mới access token bằng refresh token"""
        response = self.client.post('/auth/login',
            data=json.dumps({
                "email": "user@test.com",
                "password": "user123"
            }),
            content_type='application/json')
        data = json.loads(response.data)
        refresh_token = data['refresh_token']
        
        # Dùng refresh token để lấy access token mới
        response = self.client.post('/auth/refresh',
            data=json.dumps({"refresh_token": refresh_token}),
            content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
    
    # INTEGRATION TEST - Cache behavior
    def test_cache_get_books(self):
        """Test cache cho get books"""
        with self.app.app_context():
            book = Book(title="Cache Test", author="Author")
            db.session.add(book)
            db.session.commit()
        
        # Lần 1: cache miss
        response1 = self.client.get('/books/')
        data1 = json.loads(response1.data)
        
        # Lần 2: cache hit (nếu có cache)
        response2 = self.client.get('/books/')
        data2 = json.loads(response2.data)
        
        self.assertEqual(data1['data'], data2['data'])

if __name__ == '__main__':
    unittest.main()