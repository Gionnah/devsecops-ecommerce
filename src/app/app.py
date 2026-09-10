import os
from datetime import datetime, date, timedelta
from flask import Flask, jsonify
from app.models import db, Product, Customer, Order, OrderItem, SalesAnalyticsSummary
from app.routes import main_bp, api_bp

def create_app(test_config=None):
    app = Flask(__name__)

    # Configuration par défaut
    db_user = os.environ.get('POSTGRES_USER', 'ecommerce_user')
    db_password = os.environ.get('POSTGRES_PASSWORD', 'ecommerce_pass123')
    db_host = os.environ.get('POSTGRES_HOST', 'localhost')
    db_port = os.environ.get('POSTGRES_PORT', '5432')
    db_name = os.environ.get('POSTGRES_DB', 'ecommerce_db')

    default_db_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    # Fallback to SQLite if PostgreSQL not specified or during unit tests
    database_uri = os.environ.get('DATABASE_URL', default_db_uri)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devsecops-super-secure-key-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    # Enregistrer les Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Observabilité & Healthchecks pour Kubernetes
    @app.route('/healthz')
    def healthz():
        """Kubernetes Liveness Probe"""
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200

    @app.route('/ready')
    def ready():
        """Kubernetes Readiness Probe"""
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({'status': 'ready', 'database': 'connected'}), 200
        except Exception as e:
            return jsonify({'status': 'unready', 'error': str(e)}), 503

    @app.route('/metrics')
    def metrics():
        """Prometheus Metrics Endpoint"""
        try:
            prod_count = Product.query.count()
            order_count = Order.query.count()
            metrics_data = (
                f"# HELP ecommerce_products_total Total number of products\n"
                f"# TYPE ecommerce_products_total gauge\n"
                f"ecommerce_products_total {prod_count}\n"
                f"# HELP ecommerce_orders_total Total number of orders\n"
                f"# TYPE ecommerce_orders_total counter\n"
                f"ecommerce_orders_total {order_count}\n"
            )
            return metrics_data, 200, {'Content-Type': 'text/plain; version=0.0.4'}
        except Exception:
            return "ecommerce_up 0\n", 200, {'Content-Type': 'text/plain; version=0.0.4'}

    # Initialisation de la BDD et Seeding des données initiales
    with app.app_context():
        try:
            db.create_all()
            seed_initial_data()
        except Exception as e:
            app.logger.warning(f"Database initialization deferred or failed: {e}")

    return app


def seed_initial_data():
    """Insère des données d'exemple pour simuler un site e-commerce actif"""
    if Product.query.first():
        return # Déjà initialisé

    # 1. Clients d'exemple
    customers = [
        Customer(name="Alice Dupont", email="alice@example.com", address="12 Rue de Rivoli, Paris"),
        Customer(name="Bob Martin", email="bob@example.com", address="45 Avenue Jean Jaurès, Lyon"),
        Customer(name="Clara Bernard", email="clara@example.com", address="8 Boulevard Victor Hugo, Marseille"),
        Customer(name="David Rakoto", email="david@example.com", address="101 Route Circulaire, Antananarivo")
    ]
    db.session.add_all(customers)
    db.session.flush()

    # 2. Produits d'exemple
    products = [
        Product(
            name="Ordinateur Portable Pro 15\"",
            description="Processeur M-Series 16 Go RAM 512 Go SSD écran Retina",
            price=1299.99,
            stock=15,
            category="Informatique",
            image_url="https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500"
        ),
        Product(
            name="Casque Audio Sans Fil Réduction de Bruit",
            description="Autonomie 30h, son spatialisé HD et micro intégré",
            price=199.99,
            stock=30,
            category="Audio",
            image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500"
        ),
        Product(
            name="Montre Connectée Sport Pro",
            description="GPS, capteur cardiaque, étanche 50m, autonomie 7 jours",
            price=249.50,
            stock=4, # Stock faible pour alerte
            category="Accessoires",
            image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500"
        ),
        Product(
            name="Clavier Mécanique RGB Sans Fil",
            description="Switches silencieux, châssis aluminium brossé",
            price=89.90,
            stock=22,
            category="Informatique",
            image_url="https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500"
        ),
        Product(
            name="Souris Ergonomique Haute Précision",
            description="Capteur 4000 DPI, connectivité Bluetooth & 2.4GHz",
            price=49.99,
            stock=3, # Stock faible
            category="Informatique",
            image_url="https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500"
        )
    ]
    db.session.add_all(products)
    db.session.flush()

    # 3. Commandes d'exemple
    orders_data = [
        (customers[0], [(products[0], 1), (products[1], 1)]),
        (customers[1], [(products[2], 1)]),
        (customers[2], [(products[3], 2), (products[4], 1)]),
        (customers[3], [(products[1], 2)])
    ]

    for cust, items in orders_data:
        total = sum(p.price * qty for p, qty in items)
        order = Order(customer_id=cust.id, total_amount=round(total, 2), status='COMPLETED')
        db.session.add(order)
        db.session.flush()
        for p, qty in items:
            item = OrderItem(order_id=order.id, product_id=p.id, quantity=qty, unit_price=p.price)
            db.session.add(item)

    # 4. Rapport Analytics initial d'exemple
    initial_summary = SalesAnalyticsSummary(
        report_date=date.today() - timedelta(days=1),
        total_revenue=2338.87,
        total_orders=4,
        total_items_sold=7,
        avg_order_value=584.72,
        top_category="Informatique",
        top_product_name="Ordinateur Portable Pro 15\"",
        low_stock_alerts_count=2,
        calculated_at=datetime.utcnow()
    )
    db.session.add(initial_summary)
    db.session.commit()


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

