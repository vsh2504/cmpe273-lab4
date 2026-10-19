"""
Notification Service.

This service owns the record of notifications that were sent.
It runs as its own process on port 5002.
It receives an event after an order is created and it records a notice.
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# Sample data. This service is the only owner of this data.
notifications = []


@app.get("/health")
def health():
    return jsonify({"service": "notification", "status": "ok"}), 200


@app.post("/notify")
def notify():
    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id")
    customer = data.get("customer")
    item_id = data.get("item_id")

    if not order_id or not customer or not item_id:
        return jsonify({"error": "order_id, customer and item_id are required"}), 400

    message = f"Order {order_id} was created for {customer}. Item: {item_id}."
    record = {"order_id": order_id, "customer": customer, "message": message}
    notifications.append(record)
    print(f"Notification sent: {message}")
    return jsonify({"status": "sent", "notification": record}), 201


@app.get("/notifications")
def list_notifications():
    return jsonify(notifications), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002)
