import json
import os

DATA_FILE = "balances.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_balance(user_id):
    data = load_data()
    return data.get(user_id, 0)

def add_balance(user_id, amount):
    data = load_data()
    data[user_id] = data.get(user_id, 0) + amount
    save_data(data)

def subtract_balance(user_id, amount):
    data = load_data()
    if data.get(user_id, 0) >= amount:
        data[user_id] -= amount
        save_data(data)
        return True
    return False
    def get_all_balances():
    return load_data()