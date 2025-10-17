from app.extension import db

class Movie(db.Model):
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(50))
    duration = db.Column(db.Integer)
    
    bookings = db.relationship('Booking', backref='movie', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'genre': self.genre,
            'duration': self.duration
        }