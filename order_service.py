"""
Order Service.

This service owns order records and the order status.
It runs as its own process on port 5000.
It asks the Inventory Service before it creates an order.
It does not read the inventory data directly.
"""

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

INVENTORY_URL = "http://127.0.0.1:5001"
NOTIFICATION_URL = "http://127.0.0.1:5002"
TIMEOUT_SECONDS = 2

# Sample data. This service is the only owner of this data.
orders = {}
next_order_number = 1


@app.get("/health")
def health():
    return jsonify({"service": "order", "status": "ok"}), 200


@app.get("/orders")
def list_orders():
    return jsonify(list(orders.values())), 200


@app.get("/orders/<order_id>")
def get_order(order_id):
    order = orders.get(order_id)
    if order is None:
        return jsonify({"error": "order not found", "order_id": order_id}), 404
    return jsonify(order), 200


def send_order_created_event(order):
    # This is an event. It states a fact that already happened.
    # A failure here does not cancel the order, so we only log it.
    payload = {
        "event": "OrderCreated",
        "order_id": order["order_id"],
        "customer": order["customer"],
        "item_id": order["item_id"],
        "quantity": order["quantity"],
    }
    try:
        requests.post(f"{NOTIFICATION_URL}/notify", json=payload, timeout=TIMEOUT_SECONDS)
    except requests.RequestException:
        print(f"Notification Service is not reachable for order {order['order_id']}.")


@app.post("/orders")
def create_order():
    global next_order_number

    data = request.get_json(silent=True) or {}
    customer = data.get("customer")
    item_id = data.get("item_id")
    quantity = data.get("quantity", 1)

    if not customer or not item_id:
        return jsonify({"error": "customer and item_id are required"}), 400

    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "quantity must be a positive integer"}), 400

    # Query the Inventory Service for the current stock.
    try:
        response = requests.get(
            f"{INVENTORY_URL}/inventory/{item_id}/availability",
            params={"quantity": quantity},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        # The dependency failed. We return a clear error and stay running.
        return jsonify(
            {
                "error": "Inventory Service is unavailable. "
                "The order was not created. Please try again later."
            }
        ), 503

    if response.status_code == 404:
        return jsonify({"error": "item not found", "item_id": item_id}), 404

    if response.status_code != 200:
        return jsonify({"error": "Inventory Service returned an error."}), 502

    result = response.json()
    if not result.get("available"):
        return jsonify(
            {
                "error": "item is not available in the requested quantity",
                "item_id": item_id,
                "stock": result.get("stock"),
                "requested": quantity,
            }
        ), 409

    order_id = f"ORD-{next_order_number}"
    next_order_number += 1

    order = {
        "order_id": order_id,
        "customer": customer,
        "item_id": item_id,
        "quantity": quantity,
        "status": "CONFIRMED",
    }
    orders[order_id] = order

    send_order_created_event(order)

    return jsonify(order), 201


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
