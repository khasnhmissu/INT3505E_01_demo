from app import create_app
from app.models import User, Book, Loan
from app.extension import db
from werkzeug.security import generate_password_hash
from datetime import date, timedelta
import random

def seed_database():
    app = create_app()
    
    with app.app_context():
        print("🗑️  Xóa dữ liệu cũ...")
        Loan.query.delete()
        Book.query.delete()
        User.query.delete()
        db.session.commit()
        
        print("👤 Tạo Admin...")
        admin = User(
            name="Admin",
            email="admin@example.com",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        
        print("👥 Tạo 100 Users...")
        users = []
        for i in range(1, 101):
            user = User(
                name=f"User {i}",
                email=f"user{i}@example.com",
                password=generate_password_hash("123456"),
                role="user"
            )
            users.append(user)
            db.session.add(user)
        
        db.session.commit()
        print(f"✅ Đã tạo {len(users)} users")
        
        print("📚 Tạo 500 Books...")
        authors = [
            "Robert C. Martin", "Martin Fowler", "Eric Evans", 
            "Gang of Four", "Kent Beck", "Uncle Bob",
            "Joshua Bloch", "Erich Gamma", "Andrew Hunt",
            "David Thomas", "Steve McConnell", "Michael Feathers",
            "Vaughn Vernon", "Sam Newman", "Greg Young"
        ]
        
        book_prefixes = [
            "Clean", "Design Patterns", "Refactoring", "The Art of",
            "Introduction to", "Advanced", "Modern", "Practical",
            "Mastering", "Learning", "Professional", "Essential"
        ]
        
        book_topics = [
            "Code", "Architecture", "Programming", "Software",
            "Algorithms", "Data Structures", "Testing", "DevOps",
            "Microservices", "Domain-Driven Design", "Agile", "Databases"
        ]
        
        books = []
        for i in range(1, 501):
            prefix = random.choice(book_prefixes)
            topic = random.choice(book_topics)
            author = random.choice(authors)
            
            book = Book(
                title=f"{prefix} {topic} Vol.{i}",
                author=author,
                is_available=random.choice([True, True, True, False])
            )
            books.append(book)
            db.session.add(book)
        
        db.session.commit()
        print(f"✅ Đã tạo {len(books)} books")
        
        print("📖 Tạo 1000 Loans...")
        loans = []
        start_date = date.today() - timedelta(days=365)
        
        for i in range(1, 1001):
            user = random.choice(users)
            book = random.choice(books)
            
            checkout_date = start_date + timedelta(days=random.randint(0, 365))
            
            # 60% loans đã trả, 40% chưa trả
            has_returned = random.random() < 0.6
            return_date = None
            
            if has_returned:
                days_borrowed = random.randint(1, 30)
                return_date = checkout_date + timedelta(days=days_borrowed)
            
            loan = Loan(
                book_id=book.id,
                user_id=user.id,
                checkout_date=checkout_date,
                return_date=return_date
            )
            loans.append(loan)
            db.session.add(loan)
            
            # Update book availability
            if not has_returned:
                book.is_available = False
        
        db.session.commit()
        print(f"✅ Đã tạo {len(loans)} loans")
        
        print("\n" + "="*50)
        print("📊 THỐNG KÊ DATABASE")
        print("="*50)
        print(f"👥 Users: {User.query.count()}")
        print(f"📚 Books: {Book.query.count()}")
        print(f"   - Available: {Book.query.filter_by(is_available=True).count()}")
        print(f"   - On loan: {Book.query.filter_by(is_available=False).count()}")
        print(f"📖 Loans: {Loan.query.count()}")
        print(f"   - Active (chưa trả): {Loan.query.filter(Loan.return_date == None).count()}")
        print(f"   - Returned (đã trả): {Loan.query.filter(Loan.return_date != None).count()}")
        print("="*50)
        print("\n✅ SEED DATABASE HOÀN TẤT!")
        print("\n🔑 Login credentials:")
        print("   Admin: admin@example.com / admin123")
        print("   Users: user1@example.com / password123")
        print("          user2@example.com / password123")
        print("          ... user100@example.com / password123")

if __name__ == "__main__":
    seed_database()