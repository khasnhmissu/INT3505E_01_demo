# run.py
from routes import create_app

# Tạo Flask app từ factory
app = create_app()

if __name__ == '__main__':    
    app.run(debug=True, port=5000, host='0.0.0.0')