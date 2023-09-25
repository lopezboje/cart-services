import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://carts_products_service_user:gHUTZN3ntf8giUDIU6V5lEj8SyOU6cUA@dpg-ck8fquo8elhc7388rmhg-a.oregon-postgres.render.com/carts_products_service'
db = SQLAlchemy(app)

# Cart Model
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_items = db.relationship('Cart_Item', backref='cart', lazy=True)
    total_price = db.Column(db.Integer, nullable=False)

class Cart_Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    product_quantity = db.Column(db.Integer, nullable=False)

# Endpoint 1: Get all products
@app.route('/cart/<int:cart_id>', methods=['GET'])
def get_cart(cart_id):
    cart = Cart.query.get(cart_id)
    if cart:
        cart_items = cart.cart_items
        cart_list = []

        for item in cart_items:
            response = requests.get(f'https://product-services-rkq8.onrender.com/products/{item.product_id}')
            
            if response.status_code == 200:
                product = response.json()
                name = product['name']
                price = product['price']
                quantity = item.product_quantity
                cart_list.append({"name": name, "price": price, "quantity": quantity})
        return jsonify({"cart": cart_list})
    else:
        new_cart = Cart(id=cart_id, total_price=0)
        db.session.add(new_cart)
        db.session.commit()
        return jsonify({"message": "Created new cart. Add items!", "cart": []})

# Endpoint 2: Add a new product
@app.route('/cart/<int:cart_id>/add/<int:product_id>', methods=['POST'])
def add_product(cart_id, product_id):
    cart = Cart.query.get(cart_id)
    if cart:
        response = requests.get(f'https://product-services-rkq8.onrender.com/products/{product_id}')

        if response.status_code == 200:
            product = response.json()
            name = product['name']
            price = product['price']
            if(product['quantity'] <= 1):
                quantity = 1
            else:
                return jsonify({"error": "Product out of stock"}), 400
            new_cart_item = Cart_Item(cart_id=cart_id, product_id=product_id, product_quantity=quantity)
            db.session.add(new_cart_item)
            db.session.commit()
            return jsonify({"message": "Product added to cart", "product": {"name": name, "price": price, "quantity": quantity}}), 201
    else:
        return jsonify({"error": "Cart not found"}), 404

# Endpoint 3: Remove a product
@app.route('/cart/<int:cart_id>/remove/<int:product_id>', methods=['POST'])
def remove_product(cart_id, product_id):
    cart = Cart.query.get(cart_id)
    if cart:
        cart_items = cart.cart_items
        for item in cart_items:
            if item.product_id == product_id:
                db.session.delete(item)
                db.session.commit()
                return jsonify({"message": "Product removed from cart"}), 201
        return jsonify({"error": "Product not found in cart"}), 404
    else:
        return jsonify({"error": "Cart not found"}), 404

if __name__ == '__main__':
    with app.app_context():
        inspector = inspect(db.engine)
        if not inspector.has_table('cart'):
            print("Creating table")
            db.create_all()
    app.run(debug=True)
