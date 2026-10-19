"""
Inventory Service.

This service owns the item catalog and the stock count for each item.
It runs as its own process on port 5001.
Other services can only read stock data through this API.
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# Sample data. This service is the only owner of this data.
inventory = {
    "laptop": {"item_id": "laptop", "name": "Laptop", "stock": 10},
    "phone": {"item_id": "phone", "name": "Phone", "stock": 5},
    "keyboard": {"item_id": "keyboard", "name": "Keyboard", "stock": 25},
    "headphones": {"item_id": "headphones", "name": "Headphones", "stock": 0},
}


@app.get("/health")
def health():
    return jsonify({"service": "inventory", "status": "ok"}), 200


@app.get("/inventory")
def list_inventory():
    return jsonify(list(inventory.values())), 200


@app.get("/inventory/<item_id>")
def get_item(item_id):
    item = inventory.get(item_id)
    if item is None:
        return jsonify({"error": "item not found", "item_id": item_id}), 404
    return jsonify(item), 200


@app.get("/inventory/<item_id>/availability")
def check_availability(item_id):
    # This is a query. It reads stock and it does not change any data.
    item = inventory.get(item_id)
    if item is None:
        return jsonify({"error": "item not found", "item_id": item_id}), 404

    try:
        quantity = int(request.args.get("quantity", 1))
    except ValueError:
        return jsonify({"error": "quantity must be a positive integer"}), 400

    if quantity <= 0:
        return jsonify({"error": "quantity must be a positive integer"}), 400

    available = item["stock"] >= quantity
    return jsonify(
        {
            "item_id": item_id,
            "available": available,
            "stock": item["stock"],
            "requested": quantity,
        }
    ), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
