import logging
import sys
import os
from pythonjsonlogger import jsonlogger
from flask import request, g
import time
from logging.handlers import RotatingFileHandler

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter to add request context"""
    
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = self.formatTime(record, self.datefmt)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        
        # Add request context if available
        try:
            if request:
                log_record['method'] = request.method
                log_record['path'] = request.path
                log_record['ip'] = request.remote_addr
                log_record['user_agent'] = request.headers.get('User-Agent', '')
                
                # FIX: Use 'name' instead of 'username'
                if hasattr(g, 'current_user') and g.current_user:
                    log_record['user_id'] = g.current_user.get('id')
                    log_record['user_name'] = g.current_user.get('name')
        except RuntimeError:
            # Outside request context
            pass

def setup_logging(app):
    """Configure structured logging"""
    
    # Create logs directory if not exists
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"✅ Created logs directory: {log_dir}")
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(app.config.get('LOG_LEVEL', 'INFO'))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Determine formatter based on config
    if app.config.get('LOG_FORMAT') == 'json':
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # 1. Console handler (stdout) - để xem log real-time
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)  # Show all levels in console
    logger.addHandler(console_handler)
    
    # 2. File handler - lưu tất cả logs vào file
    app_log_file = os.path.join(log_dir, 'app.log')
    file_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    # 3. Error log file - chỉ lưu ERROR và CRITICAL
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)
    
    # 4. Audit logger - riêng cho business events
    audit_logger = logging.getLogger('audit')
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False  # Không gửi lên parent logger
    
    # Clear any existing handlers
    audit_logger.handlers = []
    
    # Audit log file
    audit_log_file = os.path.join(log_dir, 'audit.log')
    audit_handler = RotatingFileHandler(
        audit_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    audit_handler.setFormatter(formatter)
    audit_logger.addHandler(audit_handler)
    
    # Audit cũng in ra console
    audit_console = logging.StreamHandler(sys.stdout)
    audit_console.setFormatter(formatter)
    audit_logger.addHandler(audit_console)
    
    # Test log to confirm setup
    logger.info(f"✅ Logging configured successfully. Logs directory: {log_dir}")
    logger.info(f"✅ Log level: {app.config.get('LOG_LEVEL', 'INFO')}")
    logger.info(f"✅ Log format: {app.config.get('LOG_FORMAT', 'standard')}")
    
    return logger, audit_logger

def log_audit_event(action, resource_type, resource_id, details=None, user_info=None):
    """
    Log audit events for critical business actions
    
    Args:
        action: Action performed (CREATE, UPDATE, DELETE, etc.)
        resource_type: Type of resource (Book, User, Loan, etc.)
        resource_id: ID of the resource
        details: Additional details dict
        user_info: Dict with user info {'id': 1, 'name': 'admin'} or pass current_user from decorator
    """
    audit_logger = logging.getLogger('audit')
    
    audit_data = {
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'details': details or {}
    }
    
    # FIX: Use 'name' instead of 'username'
    if user_info:
        if isinstance(user_info, dict):
            audit_data['user_id'] = user_info.get('id')
            audit_data['user_name'] = user_info.get('name')
        else:
            # If user_info is the User object from current_user parameter
            audit_data['user_id'] = getattr(user_info, 'id', None)
            audit_data['user_name'] = getattr(user_info, 'name', None)
    # Fallback: try to get from g if available
    elif hasattr(g, 'current_user') and g.current_user:
        audit_data['user_id'] = g.current_user.get('id')
        audit_data['user_name'] = g.current_user.get('name')
    
    audit_logger.info(f"AUDIT: {action} on {resource_type}", extra=audit_data)