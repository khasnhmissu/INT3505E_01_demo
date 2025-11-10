import unittest
from app import create_app
from app.extension import db
from app.models import Book, User, Loan
from datetime import date

class TestModels(unittest.TestCase):
    
    def setUp(self):
        """Chạy trước mỗi test"""
        # QUAN TRỌNG: Truyền 'testing' vào create_app để dùng TestConfig
        self.app = create_app(config_name='testing')
        
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        # Tạo tables trong test database
        db.create_all()
    
    def tearDown(self):
        """Chạy sau mỗi test"""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
    
    # UNIT TEST cho Book Model
    def test_book_creation(self):
        """Test tạo sách"""
        book = Book(title="Python 101", author="John Doe", is_available=True)
        db.session.add(book)
        db.session.commit()
        
        self.assertIsNotNone(book.id)
        self.assertEqual(book.title, "Python 101")
        self.assertEqual(book.author, "John Doe")
        self.assertTrue(book.is_available)
    
    def test_book_default_availability(self):
        """Test giá trị mặc định is_available"""
        book = Book(title="Test Book", author="Test Author")
        db.session.add(book)
        db.session.commit()
        
        self.assertTrue(book.is_available)
    
    # UNIT TEST cho User Model
    def test_user_creation(self):
        """Test tạo user"""
        user = User(
            name="Alice",
            email="alice@test.com",
            password="hashed_password",
            role="user"
        )
        db.session.add(user)
        db.session.commit()
        
        self.assertIsNotNone(user.id)
        self.assertEqual(user.name, "Alice")
        self.assertEqual(user.email, "alice@test.com")
        self.assertEqual(user.role, "user")
        self.assertEqual(user.token_version, 0)
    
    def test_user_default_role(self):
        """Test role mặc định là user"""
        user = User(name="Bob", email="bob@test.com", password="pass")
        db.session.add(user)
        db.session.commit()
        
        self.assertEqual(user.role, "user")
    
    def test_user_email_unique(self):
        """Test email phải unique"""
        user1 = User(name="User1", email="same@test.com", password="pass1")
        user2 = User(name="User2", email="same@test.com", password="pass2")
        
        db.session.add(user1)
        db.session.commit()
        
        db.session.add(user2)
        with self.assertRaises(Exception):
            db.session.commit()
    
    # UNIT TEST cho Loan Model
    def test_loan_creation(self):
        """Test tạo giao dịch mượn sách"""
        book = Book(title="Test Book", author="Author")
        user = User(name="User", email="user@test.com", password="pass")
        db.session.add_all([book, user])
        db.session.commit()
        
        loan = Loan(
            book_id=book.id,
            user_id=user.id,
            checkout_date=date.today()
        )
        db.session.add(loan)
        db.session.commit()
        
        self.assertIsNotNone(loan.loan_id)
        self.assertEqual(loan.book_id, book.id)
        self.assertEqual(loan.user_id, user.id)
        self.assertIsNone(loan.return_date)
    
    def test_loan_relationship(self):
        """Test relationship giữa Loan, Book, User"""
        book = Book(title="Python Book", author="Author")
        user = User(name="Reader", email="reader@test.com", password="pass")
        db.session.add_all([book, user])
        db.session.commit()
        
        loan = Loan(book_id=book.id, user_id=user.id, checkout_date=date.today())
        db.session.add(loan)
        db.session.commit()
        
        # Test relationship
        self.assertEqual(loan.book.title, "Python Book")
        self.assertEqual(loan.user.name, "Reader")
        self.assertEqual(len(book.loans), 1)
        self.assertEqual(len(user.loans), 1)

if __name__ == '__main__':
    unittest.main()