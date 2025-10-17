from flask import jsonify
from werkzeug.exceptions import HTTPException

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': {
                'code': 404,
                'message': str(error),
                'status': 'NOT_FOUND'
            }
        }), 404
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': {
                'code': 400,
                'message': str(error),
                'status': 'BAD_REQUEST'
            }
        }), 400
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': {
                'code': 403,
                'message': str(error),
                'status': 'FORBIDDEN'
            }
        }), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': {
                'code': 500,
                'message': 'Internal server error',
                'status': 'INTERNAL_SERVER_ERROR'
            }
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        if isinstance(error, HTTPException):
            return jsonify({
                'error': {
                    'code': error.code,
                    'message': error.description,
                    'status': error.name.upper().replace(' ', '_')
                }
            }), error.code
        
        return jsonify({
            'error': {
                'code': 500,
                'message': str(error),
                'status': 'INTERNAL_SERVER_ERROR'
            }
        }), 500