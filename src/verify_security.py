import urllib.request
import json
import urllib.error
import sys

BASE_URL = 'http://localhost:8000/api'

def post(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f'HTTP Error {e.code}: {e.read().decode()}')
        return None
    except Exception as e:
        print(f'Error: {e}')
        return None

def get(url, token=None):
    req = urllib.request.Request(url)
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except urllib.error.HTTPError as e:
        print(f'Expected HTTP Error {e.code}: {e.reason}')
        return None
    except Exception as e:
        print(f'Error: {e}')
        return None

def run_verification():
    print('--- 1. Register User (Charlie) ---')
    # Use random suffix to allow multiple runs
    import random
    suffix = random.randint(1000, 9999)
    username = f'charlie_{suffix}'
    reg_data = {
        'username': username,
        'password': 'password123',
        'first_name': 'Charlie',
        'last_name': 'Chocolate',
        'email': f'charlie_{suffix}@example.com'
    }
    user = post(f'{BASE_URL}/register/', reg_data)
    
    if not user:
        print('Registration failed')
        sys.exit(1)
        
    print(f'Registered: {user["username"]}')

    print('\n--- 2. Login ---')
    auth_data = {'username': username, 'password': 'password123'}
    tokens = post(f'{BASE_URL}/token/', auth_data)
    
    if not tokens:
        print('Login failed')
        sys.exit(1)
        
    token = tokens['access']
    print(f'Got Token: {token[:15]}...')

    print('\n--- 3. Access Customers (Authed) ---')
    customers = get(f'{BASE_URL}/customers/', token)
    if customers is not None:
        count = customers.get('count', 0) if isinstance(customers, dict) else len(customers)
        # DRF pagination returns dict with 'count', 'results'
        if isinstance(customers, dict) and 'results' in customers:
             print(f'Customers count: {customers["count"]}')
             print('Results:', json.dumps(customers['results'], indent=2))
        else:
             print(f'Customers: {customers}')
        
    print('\n--- 4. Access Customers (Unauthed) ---')
    result = get(f'{BASE_URL}/customers/')
    if result is None:
        print('SUCCESS: Unauthed access blocked')
    else:
        print('FAILURE: Unauthed access allowed!')
        sys.exit(1)

if __name__ == '__main__':
    run_verification()
