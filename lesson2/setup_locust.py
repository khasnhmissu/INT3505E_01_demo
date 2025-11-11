"""
Script tạo dữ liệu test cho performance testing
Chạy TRƯỚC KHI chạy Locust
"""

from app import create_app
from app.extension import db
from app.models import Book, User
from werkzeug.security import generate_password_hash

def setup_test_data():
    app = create_app(config_name='development')
    
    with app.app_context():
        # Xóa data cũ (optional)
        # db.drop_all()
        # db.create_all()
        
        # 1. Tạo admin nếu chưa có
        admin = User.query.filter_by(email="admin@test.com").first()
        if not admin:
            admin = User(
                name="Admin",
                email="admin@test.com",
                password=generate_password_hash("admin123"),
                role="admin"
            )
            db.session.add(admin)
            print("✓ Created admin user")
        else:
            print("✓ Admin already exists")
        
        # 2. Tạo một số books để test
        existing_books = Book.query.count()
        
        if existing_books < 50:
            authors = [
                "Martin Fowler", "Robert C. Martin", "Eric Evans",
                "Kent Beck", "Martin Kleppmann", "Douglas Crockford",
                "Kyle Simpson", "Dan Abramov", "John Resig", "David Flanagan"
            ]
            
            books_to_add = 50 - existing_books
            
            for i in range(books_to_add):
                book = Book(
                    title=f"Test Book {existing_books + i + 1}",
                    author=authors[i % len(authors)],
                    is_available=True
                )
                db.session.add(book)
            
            db.session.commit()
            print(f"✓ Created {books_to_add} books (Total: 50)")
        else:
            print(f"✓ Already have {existing_books} books")
        
        print("\n" + "="*50)
        print("Test data ready!")
        print("="*50)
        print(f"Admin: admin@test.com / admin123")
        print(f"Books: {Book.query.count()}")
        print("="*50)

if __name__ == "__main__":
    setup_test_data()