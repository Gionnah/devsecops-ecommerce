from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import db, Product, Customer, Order, OrderItem, SalesAnalyticsSummary

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')

# ==========================================
# UI ROUTES (WEB TEMPLATES)
# ==========================================

@main_bp.route('/')
def index():
    """Page d'accueil du site e-commerce avec statistiques rapides"""
    products_count = Product.query.count()
    orders_count = Order.query.count()
    total_sales = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0.0
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(6).all()
    latest_analytics = SalesAnalyticsSummary.query.order_by(SalesAnalyticsSummary.report_date.desc()).first()

    return render_template(
        'index.html',
        products_count=products_count,
        orders_count=orders_count,
        total_sales=round(total_sales, 2),
        recent_products=recent_products,
        latest_analytics=latest_analytics
    )

# --- PRODUITS (CRUD) ---
@main_bp.route('/products')
def products():
    category_filter = request.args.get('category')
    search_query = request.args.get('q')

    query = Product.query
    if category_filter:
        query = query.filter_by(category=category_filter)
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))

    products_list = query.order_by(Product.id.asc()).all()
    categories = [c[0] for c in db.session.query(Product.category).distinct().all() if c[0]]

    return render_template('products.html', products=products_list, categories=categories, selected_category=category_filter)

@main_bp.route('/products/new', methods=['GET', 'POST'])
def product_create():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price', 0))
        stock = int(request.form.get('stock', 0))
        category = request.form.get('category', 'General')
        image_url = request.form.get('image_url')

        if not name or price <= 0:
            flash("Le nom et un prix positif sont obligatoires.", "danger")
            return render_template('product_form.html', product=None)

        new_product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category=category,
            image_url=image_url or "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500"
        )
        db.session.add(new_product)
        db.session.commit()
        flash(f"Produit '{name}' créé avec succès !", "success")
        return redirect(url_for('main.products'))

    return render_template('product_form.html', product=None)

@main_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price', 0))
        product.stock = int(request.form.get('stock', 0))
        product.category = request.form.get('category', 'General')
        product.image_url = request.form.get('image_url')

        db.session.commit()
        flash(f"Produit '{product.name}' mis à jour !", "success")
        return redirect(url_for('main.products'))

    return render_template('product_form.html', product=product)

@main_bp.route('/products/<int:product_id>/delete', methods=['POST'])
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f"Produit '{name}' supprimé avec succès.", "info")
    return redirect(url_for('main.products'))

# --- COMMANDES (COMMANDES & SIMULATION ACHATS) ---
@main_bp.route('/orders')
def orders():
    orders_list = Order.query.order_by(Order.created_at.desc()).all()
    customers_list = Customer.query.all()
    products_list = Product.query.filter(Product.stock > 0).all()
    return render_template('orders.html', orders=orders_list, customers=customers_list, products=products_list)

@main_bp.route('/orders/new', methods=['POST'])
def order_create():
    customer_id = request.form.get('customer_id')
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))

    if not customer_id or not product_id:
        flash("Sélectionnez un client et un produit.", "warning")
        return redirect(url_for('main.orders'))

    product = Product.query.get_or_404(int(product_id))
    if product.stock < quantity:
        flash(f"Stock insuffisant ({product.stock} disponibles).", "danger")
        return redirect(url_for('main.orders'))

    # Décrémenter le stock
    product.stock -= quantity
    total_amount = round(product.price * quantity, 2)

    order = Order(
        customer_id=int(customer_id),
        total_amount=total_amount,
        status='COMPLETED'
    )
    db.session.add(order)
    db.session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=quantity,
        unit_price=product.price
    )
    db.session.add(item)
    db.session.commit()

    flash(f"Commande #{order.id} validée pour un total de {total_amount} € !", "success")
    return redirect(url_for('main.orders'))

# --- ANALYTICS (RÉSULTATS DE L'ETL AIRFLOW) ---
@main_bp.route('/analytics')
def analytics():
    reports = SalesAnalyticsSummary.query.order_by(SalesAnalyticsSummary.report_date.desc()).all()
    total_revenue_overall = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0.0
    total_orders_overall = Order.query.count()
    low_stock_products = Product.query.filter(Product.stock <= 5).all()

    return render_template(
        'analytics.html',
        reports=reports,
        total_revenue_overall=round(total_revenue_overall, 2),
        total_orders_overall=total_orders_overall,
        low_stock_products=low_stock_products
    )

# ==========================================
# REST API ROUTES (POUR AIRFLOW ETL & SERVICES)
# ==========================================

@api_bp.route('/products', methods=['GET'])
def api_get_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])

@api_bp.route('/orders', methods=['GET'])
def api_get_orders():
    orders = Order.query.all()
    return jsonify([o.to_dict() for o in orders])

@api_bp.route('/customers', methods=['GET'])
def api_get_customers():
    customers = Customer.query.all()
    return jsonify([c.to_dict() for c in customers])

@api_bp.route('/analytics/summary', methods=['GET', 'POST'])
def api_analytics_summary():
    if request.method == 'POST':
        data = request.get_json(force=True)
        report_date_str = data.get('report_date', str(date.today()))
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()

        # Update or create summary for date
        summary = SalesAnalyticsSummary.query.filter_by(report_date=report_date).first()
        if not summary:
            summary = SalesAnalyticsSummary(report_date=report_date)
            db.session.add(summary)

        summary.total_revenue = float(data.get('total_revenue', 0.0))
        summary.total_orders = int(data.get('total_orders', 0))
        summary.total_items_sold = int(data.get('total_items_sold', 0))
        summary.avg_order_value = float(data.get('avg_order_value', 0.0))
        summary.top_category = data.get('top_category', 'N/A')
        summary.top_product_name = data.get('top_product_name', 'N/A')
        summary.low_stock_alerts_count = int(data.get('low_stock_alerts_count', 0))
        summary.calculated_at = datetime.utcnow()

        db.session.commit()
        return jsonify({'status': 'success', 'summary': summary.to_dict()}), 201

    summaries = SalesAnalyticsSummary.query.order_by(SalesAnalyticsSummary.report_date.desc()).all()
    return jsonify([s.to_dict() for s in summaries])

