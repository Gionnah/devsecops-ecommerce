import os
import sys
import unittest
import json

# Add src to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from app.app import create_app
from app.models import db, Product, Customer, Order, OrderItem, SalesAnalyticsSummary

class EcommerceAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key-2026'
        })
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_healthz_endpoint(self):
        """Test Kubernetes liveness probe"""
        response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'healthy')

    def test_ready_endpoint(self):
        """Test Kubernetes readiness probe"""
        response = self.client.get('/ready')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data['status'], 'ready')

    def test_homepage(self):
        """Test home page rendering"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Plateforme E-Commerce CRUD", response.data)

    def test_products_crud(self):
        """Test Products listing, creation and deletion"""
        # Read list
        resp = self.client.get('/products')
        self.assertEqual(resp.status_code, 200)

        # Create new product
        post_resp = self.client.post('/products/new', data={
            'name': 'Ecran 4K UltraWide 34"',
            'description': 'Ecran IPS 144Hz',
            'price': '499.99',
            'stock': '8',
            'category': 'Informatique',
            'image_url': 'https://example.com/screen.jpg'
        }, follow_redirects=True)
        self.assertEqual(post_resp.status_code, 200)
        self.assertIn(b"Ecran 4K UltraWide 34", post_resp.data)

        # Check API
        api_resp = self.client.get('/api/products')
        self.assertEqual(api_resp.status_code, 200)
        products = json.loads(api_resp.data.decode('utf-8'))
        self.assertTrue(any(p['name'] == 'Ecran 4K UltraWide 34"' for p in products))

    def test_orders_creation(self):
        """Test creating an order and stock deduction"""
        customer = Customer.query.first()
        product = Product.query.first()
        initial_stock = product.stock

        resp = self.client.post('/orders/new', data={
            'customer_id': str(customer.id),
            'product_id': str(product.id),
            'quantity': '1'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        
        # Verify stock decreased
        updated_product = Product.query.get(product.id)
        self.assertEqual(updated_product.stock, initial_stock - 1)

    def test_airflow_analytics_api(self):
        """Test API endpoints used by Airflow ETL pipeline"""
        payload = {
            'report_date': '2026-08-30',
            'total_revenue': 2500.75,
            'total_orders': 8,
            'total_items_sold': 14,
            'avg_order_value': 312.59,
            'top_category': 'Informatique',
            'top_product_name': 'Ordinateur Portable Pro 15"',
            'low_stock_alerts_count': 1
        }
        post_res = self.client.post('/api/analytics/summary', json=payload)
        self.assertEqual(post_res.status_code, 201)

        get_res = self.client.get('/api/analytics/summary')
        self.assertEqual(get_res.status_code, 200)
        summaries = json.loads(get_res.data.decode('utf-8'))
        self.assertGreaterEqual(len(summaries), 1)
        self.assertEqual(summaries[0]['total_revenue'], 2500.75)


if __name__ == '__main__':
    unittest.main()

