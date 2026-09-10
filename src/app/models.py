import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='General')
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'category': self.category,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship('Order', backref='customer', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(30), default='COMPLETED', nullable=False) # PENDING, COMPLETED, CANCELLED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else 'Inconnu',
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)

    product = db.relationship('Product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Produit supprimé',
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': round(self.quantity * self.unit_price, 2)
        }


class SalesAnalyticsSummary(db.Model):
    """Table de destination pour le pipeline ETL Apache Airflow"""
    __tablename__ = 'sales_analytics_summary'

    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.Date, nullable=False, index=True)
    total_revenue = db.Column(db.Float, nullable=False)
    total_orders = db.Column(db.Integer, nullable=False)
    total_items_sold = db.Column(db.Integer, nullable=False)
    avg_order_value = db.Column(db.Float, nullable=False)
    top_category = db.Column(db.String(50), nullable=True)
    top_product_name = db.Column(db.String(120), nullable=True)
    low_stock_alerts_count = db.Column(db.Integer, default=0)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'report_date': self.report_date.strftime('%Y-%m-%d'),
            'total_revenue': self.total_revenue,
            'total_orders': self.total_orders,
            'total_items_sold': self.total_items_sold,
            'avg_order_value': self.avg_order_value,
            'top_category': self.top_category,
            'top_product_name': self.top_product_name,
            'low_stock_alerts_count': self.low_stock_alerts_count,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }

