from flask import Flask, request, jsonify, make_response
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)

# In-memory storage for demo purposes
transactions = []

# ============================================================================
# DEPRECATION POLICY CONFIGURATION
# ============================================================================
# Based on IETF draft: Deprecation HTTP Header
V1_DEPRECATION_DATE = datetime(2026, 1, 1)  # When v1 became deprecated
V1_SUNSET_DATE = datetime(2026, 6, 1)        # When v1 will be turned off
V1_SUCCESSOR_PATH = "/api/v2/payments"


def add_deprecation_headers(response):
    """
    Add deprecation headers to v1 responses
    
    Based on IETF draft standards:
    - Deprecation: Indicates the API is deprecated
    - Sunset: When the API will be shut down
    - Link: Points to the successor version
    - Warning: Human-readable deprecation message
    
    Purpose: Make deprecation visible in client logs and monitoring tools
    """
    response.headers['Deprecation'] = V1_DEPRECATION_DATE.strftime('%a, %d %b %Y %H:%M:%S GMT')
    response.headers['Sunset'] = V1_SUNSET_DATE.strftime('%a, %d %b %Y %H:%M:%S GMT')
    response.headers['Link'] = f'<{V1_SUCCESSOR_PATH}>; rel="successor-version"'
    response.headers['Warning'] = f'299 - "Deprecated API. Migrate to v2 before {V1_SUNSET_DATE.strftime("%Y-%m-%d")}. See {V1_SUCCESSOR_PATH}"'
    
    return response

@app.route('/api/v1/payments', methods=['POST'])
def create_payment_v1():
    """
    Payment API v1 - Create Payment (DEPRECATED)
    
    ⚠️ DEPRECATION NOTICE:
    - This endpoint is DEPRECATED as of 2026-01-01
    - Will be shut down on 2026-06-01
    - Please migrate to POST /api/v2/payments
    
    SECURITY ISSUE:
    - Accepts plain 'card_number' (violates PCI-DSS)
    - This is why we need v2 (Breaking Change)
    
    REQUEST BODY (v1):
    {
        "amount": 100.50,
        "currency": "USD",
        "card_number": "4111111111111111"  ❌ Security flaw
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields (v1 schema)
        required_fields = ['amount', 'currency', 'card_number']
        for field in required_fields:
            if field not in data:
                response = make_response(jsonify({
                    'error': f'Missing required field: {field}',
                    'migration_note': 'v2 uses payment_method object instead of card_number'
                }), 400)
                return add_deprecation_headers(response)
        
        # Validate data types
        if not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
            response = make_response(jsonify({
                'error': 'Amount must be a positive number'
            }), 400)
            return add_deprecation_headers(response)
        
        if not isinstance(data['currency'], str) or len(data['currency']) != 3:
            response = make_response(jsonify({
                'error': 'Currency must be a 3-letter code (e.g., USD, VND)'
            }), 400)
            return add_deprecation_headers(response)
        
        # Create transaction (v1 logic)
        transaction = {
            'transaction_id': str(uuid.uuid4()),
            'status': 'success',
            'amount': data['amount'],
            'currency': data['currency'],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'card_last4': data['card_number'][-4:] if len(data['card_number']) >= 4 else '****',
            'api_version': 'v1',
            # Add deprecation info in response body for UI visibility
            '_deprecation': {
                'deprecated': True,
                'sunset_date': V1_SUNSET_DATE.isoformat() + 'Z',
                'successor': V1_SUCCESSOR_PATH,
                'reason': 'Security improvement: v2 uses tokenized payment method'
            }
        }
        
        transactions.append(transaction)
        
        # Create response with deprecation headers
        response = make_response(jsonify(transaction), 201)
        return add_deprecation_headers(response)
    
    except Exception as e:
        response = make_response(jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500)
        return add_deprecation_headers(response)


@app.route('/api/v1/payments/<transaction_id>', methods=['GET'])
def get_payment_v1(transaction_id):
    """
    Get payment details by transaction ID (v1 - DEPRECATED)
    """
    for transaction in transactions:
        if transaction['transaction_id'] == transaction_id:
            response = make_response(jsonify(transaction), 200)
            return add_deprecation_headers(response)
    
    response = make_response(jsonify({
        'error': 'Transaction not found'
    }), 404)
    return add_deprecation_headers(response)


@app.route('/api/v1/payments', methods=['GET'])
def list_payments_v1():
    """
    List all transactions (v1 - DEPRECATED)
    """
    response = make_response(jsonify({
        'version': 'v1',
        'status': 'deprecated',
        'total': len(transactions),
        'transactions': transactions,
        '_deprecation_notice': f'This API will be shut down on {V1_SUNSET_DATE.strftime("%Y-%m-%d")}'
    }), 200)
    return add_deprecation_headers(response)

@app.route('/api/v2/payments', methods=['POST'])
def create_payment_v2():
    """
    Payment API v2 - Create Payment (CURRENT VERSION)
    
    ✅ IMPROVEMENTS in v2:
    - Uses tokenized payment_method (PCI-DSS compliant)
    - No raw card numbers
    - Better security and structure
    
    BREAKING CHANGE:
    - Schema changed: 'card_number' → 'payment_method' object
    - This is why v1 and v2 must coexist during migration
    
    REQUEST BODY (v2):
    {
        "amount": 100.50,
        "currency": "USD",
        "payment_method": {              ✅ New nested structure
            "type": "credit_card",       ✅ Payment type
            "token": "tok_1A2B3C4D5E6F"  ✅ Tokenized (secure)
        }
    }
    
    RESPONSE:
    {
        "transaction_id": "uuid",
        "status": "success",
        "amount": 100.50,
        "currency": "USD",
        "payment_method": {
            "type": "credit_card",
            "last4": "1234"
        },
        "timestamp": "2025-11-19T10:30:00Z",
        "api_version": "v2"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields (v2 schema)
        required_fields = ['amount', 'currency', 'payment_method']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'schema_version': 'v2',
                    'migration_guide': 'Replace card_number with payment_method object'
                }), 400
        
        # Validate nested payment_method object
        payment_method = data.get('payment_method', {})
        if not isinstance(payment_method, dict):
            return jsonify({
                'error': 'payment_method must be an object'
            }), 400
        
        required_pm_fields = ['type', 'token']
        for field in required_pm_fields:
            if field not in payment_method:
                return jsonify({
                    'error': f'Missing required field in payment_method: {field}',
                    'example': {
                        'type': 'credit_card',
                        'token': 'tok_1A2B3C4D5E6F'
                    }
                }), 400
        
        # Validate amount and currency
        if not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
            return jsonify({
                'error': 'Amount must be a positive number'
            }), 400
        
        if not isinstance(data['currency'], str) or len(data['currency']) != 3:
            return jsonify({
                'error': 'Currency must be a 3-letter code (e.g., USD, VND)'
            }), 400
        
        # Validate payment method type
        valid_types = ['credit_card', 'debit_card', 'digital_wallet']
        if payment_method['type'] not in valid_types:
            return jsonify({
                'error': f'Invalid payment type. Allowed: {valid_types}'
            }), 400
        
        # Create transaction (v2 logic with new structure)
        transaction = {
            'transaction_id': str(uuid.uuid4()),
            'status': 'success',
            'amount': data['amount'],
            'currency': data['currency'],
            'payment_method': {
                'type': payment_method['type'],
                # In production, we'd decrypt token to get last4
                # For demo, we'll extract from token
                'last4': payment_method['token'][-4:] if len(payment_method['token']) >= 4 else '****'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'api_version': 'v2'
        }
        
        transactions.append(transaction)
        
        return jsonify(transaction), 201
    
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/api/v2/payments/<transaction_id>', methods=['GET'])
def get_payment_v2(transaction_id):
    """
    Get payment details by transaction ID (v2)
    """
    for transaction in transactions:
        if transaction['transaction_id'] == transaction_id:
            return jsonify(transaction), 200
    
    return jsonify({
        'error': 'Transaction not found'
    }), 404


@app.route('/api/v2/payments', methods=['GET'])
def list_payments_v2():
    """
    List all transactions (v2)
    """
    return jsonify({
        'version': 'v2',
        'status': 'current',
        'total': len(transactions),
        'transactions': transactions
    }), 200

@app.route('/api/migration-guide', methods=['GET'])
def migration_guide():
    """
    Provides migration guide from v1 to v2
    This is REQUIRED in deprecation policy
    """
    return jsonify({
        'title': 'Migration Guide: v1 → v2',
        'deprecation': {
            'v1_deprecated_since': V1_DEPRECATION_DATE.isoformat(),
            'v1_sunset_date': V1_SUNSET_DATE.isoformat(),
            'days_remaining': (V1_SUNSET_DATE - datetime.utcnow()).days
        },
        'breaking_changes': {
            'schema_change': {
                'field_removed': 'card_number',
                'field_added': 'payment_method',
                'reason': 'PCI-DSS compliance - no raw card numbers'
            }
        },
        'migration_steps': [
            '1. Integrate with payment tokenization service (e.g., Stripe, PayPal)',
            '2. Replace card_number with payment_method.token in your requests',
            '3. Update your code to use /api/v2/payments endpoint',
            '4. Test thoroughly in staging environment',
            '5. Deploy to production before sunset date'
        ],
        'example_v1': {
            'url': 'POST /api/v1/payments',
            'body': {
                'amount': 100.50,
                'currency': 'USD',
                'card_number': '4111111111111111'
            }
        },
        'example_v2': {
            'url': 'POST /api/v2/payments',
            'body': {
                'amount': 100.50,
                'currency': 'USD',
                'payment_method': {
                    'type': 'credit_card',
                    'token': 'tok_1A2B3C4D5E6F'
                }
            }
        },
        'support': {
            'documentation': 'https://api.example.com/docs/v2',
            'contact': 'api-support@example.com'
        }
    }), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint (version-agnostic)
    """
    return jsonify({
        'status': 'healthy',
        'supported_versions': ['v1 (deprecated)', 'v2 (current)'],
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


@app.route('/', methods=['GET'])
def index():
    """
    API documentation endpoint
    """
    return jsonify({
        'api_name': 'Payment API',
        'versions': {
            'v1': {
                'status': 'deprecated',
                'deprecated_since': V1_DEPRECATION_DATE.isoformat(),
                'sunset_date': V1_SUNSET_DATE.isoformat(),
                'endpoints': [
                    'POST /api/v1/payments',
                    'GET /api/v1/payments/<id>',
                    'GET /api/v1/payments'
                ],
                'warning': '⚠️ Will be shut down soon. Migrate to v2!'
            },
            'v2': {
                'status': 'current',
                'endpoints': [
                    'POST /api/v2/payments',
                    'GET /api/v2/payments/<id>',
                    'GET /api/v2/payments'
                ],
                'improvements': [
                    'Tokenized payment method (secure)',
                    'Better data structure',
                    'PCI-DSS compliant'
                ]
            }
        },
        'migration_guide': '/api/migration-guide'
    }), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)