from flask import Flask, request, jsonify
import uuid
from datetime import datetime

app = Flask(__name__)

# In-memory storage for demo purposes
transactions = []


@app.route('/api/v1/payments', methods=['POST'])
def create_payment_v1():
    """
    Payment API v1 - Create Payment
    
    REQUEST BODY:
    {
        "amount": 100.50,
        "currency": "USD",
        "card_number": "4111111111111111"  # SECURITY ISSUE: Plain card number
    }
    
    RESPONSE:
    {
        "transaction_id": "uuid",
        "status": "success",
        "amount": 100.50,
        "currency": "USD",
        "timestamp": "2025-11-19T10:30:00Z"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['amount', 'currency', 'card_number']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate data types
        if not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
            return jsonify({
                'error': 'Amount must be a positive number'
            }), 400
        
        if not isinstance(data['currency'], str) or len(data['currency']) != 3:
            return jsonify({
                'error': 'Currency must be a 3-letter code (e.g., USD, VND)'
            }), 400
        
        if not isinstance(data['card_number'], str):
            return jsonify({
                'error': 'Card number must be a string'
            }), 400
        
        # ⚠️ SECURITY CONCERN: We're accepting card_number directly
        # This is a design flaw that will require a breaking change in v2
        # In production, we should NEVER handle raw card numbers
        # v2 will use payment_token instead
        
        # Create mock transaction
        transaction = {
            'transaction_id': str(uuid.uuid4()),
            'status': 'success',
            'amount': data['amount'],
            'currency': data['currency'],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            # Note: We don't store the full card number (PCI-DSS compliance)
            'card_last4': data['card_number'][-4:] if len(data['card_number']) >= 4 else '****'
        }
        
        # Store transaction (in-memory for demo)
        transactions.append(transaction)
        
        return jsonify(transaction), 201
    
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/api/v1/payments/<transaction_id>', methods=['GET'])
def get_payment_v1(transaction_id):
    """
    Get payment details by transaction ID
    """
    for transaction in transactions:
        if transaction['transaction_id'] == transaction_id:
            return jsonify(transaction), 200
    
    return jsonify({
        'error': 'Transaction not found'
    }), 404


@app.route('/api/v1/payments', methods=['GET'])
def list_payments_v1():
    """
    List all transactions (for demo purposes)
    """
    return jsonify({
        'version': 'v1',
        'total': len(transactions),
        'transactions': transactions
    }), 200


@app.route('/api/v1/health', methods=['GET'])
def health_check_v1():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'version': 'v1',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@app.route('/', methods=['GET'])
def index():
    """
    API documentation endpoint
    """
    return jsonify({
        'api_name': 'Payment API',
        'version': 'v1',
        'endpoints': {
            'POST /api/v1/payments': 'Create a payment',
            'GET /api/v1/payments/<id>': 'Get payment details',
            'GET /api/v1/payments': 'List all payments',
            'GET /api/v1/health': 'Health check'
        },
        'warning': '⚠️ This version accepts card_number directly - security concern!',
        'note': 'Version 2 will use payment tokens instead of raw card numbers'
    }), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)