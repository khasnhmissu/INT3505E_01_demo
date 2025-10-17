from app.extension import db
from datetime import datetime

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    theater_id = db.Column(db.Integer, db.ForeignKey('theaters.id'))
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    seat_number = db.Column(db.String(10))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'theater_id': self.theater_id,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'seat_number': self.seat_number
        }