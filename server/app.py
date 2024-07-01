#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json_encoder.compact = False  # Ensure JSON is not compacted

migrate = Migrate(app, db)
db.init_app(app)

api = Api(app)

def restaurant_to_dict(restaurant):
    return {
        'id': restaurant.id,
        'name': restaurant.name,
        'address': restaurant.address
    }

def restaurant_with_pizzas_to_dict(restaurant):
    return {
        'id': restaurant.id,
        'name': restaurant.name,
        'address': restaurant.address,
        'restaurant_pizzas': [restaurant_pizza_to_dict(rp) for rp in restaurant.restaurant_pizzas]
    }

def pizza_to_dict(pizza):
    return {
        'id': pizza.id,
        'name': pizza.name,
        'ingredients': pizza.ingredients
    }

def restaurant_pizza_to_dict(restaurant_pizza):
    return {
        'id': restaurant_pizza.id,
        'price': restaurant_pizza.price,
        'restaurant_id': restaurant_pizza.restaurant_id,
        'pizza_id': restaurant_pizza.pizza_id,
        'pizza': pizza_to_dict(restaurant_pizza.pizza)
    }

class RestaurantListResource(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return jsonify([restaurant_to_dict(restaurant) for restaurant in restaurants])

class RestaurantResource(Resource):
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant is None:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        return jsonify(restaurant_with_pizzas_to_dict(restaurant))

    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant is None:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        db.session.delete(restaurant)
        db.session.commit()
        return '', 204

class PizzaListResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return jsonify([pizza_to_dict(pizza) for pizza in pizzas])

class RestaurantPizzaResource(Resource):
    def post(self):
        data = request.get_json()
        if not all(key in data for key in ['restaurant_id', 'pizza_id', 'price']):
            return make_response(jsonify({"error": "Missing data"}), 400)

        try:
            restaurant_id = data['restaurant_id']
            pizza_id = data['pizza_id']
            price = data['price']

            restaurant_pizza = RestaurantPizza(
                restaurant_id=restaurant_id,
                pizza_id=pizza_id,
                price=price
            )
            db.session.add(restaurant_pizza)
            db.session.commit()
        except Exception as e:
            return make_response(jsonify({"error": str(e)}), 400)
        return jsonify(restaurant_pizza_to_dict(restaurant_pizza)), 201

# Error handling
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({"error": "Resource not found"}), 404)

api.add_resource(RestaurantListResource, '/restaurants')
api.add_resource(RestaurantResource, '/restaurants/<int:id>')
api.add_resource(PizzaListResource, '/pizzas')
api.add_resource(RestaurantPizzaResource, '/restaurant_pizzas')

if __name__ == '__main__':
    app.run(debug=True)
