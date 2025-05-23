import json
import os

FILE = "pvp_record.json"

def load_records():
    if not os.path.exists(FILE):
        with open(FILE, "w") as f:
            json.dump({}, f)
    with open(FILE, "r") as f:
        return json.load(f)

def save_records(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

def record_result(winner_id, loser_id):
    data = load_records()
    for uid in [winner_id, loser_id]:
        if uid not in data:
            data[uid] = {"win": 0, "lose": 0}
    data[winner_id]["win"] += 1
    data[loser_id]["lose"] += 1
    save_records(data)

def get_record(user_id):
    data = load_records()
    return data.get(str(user_id), {"win": 0, "lose": 0})
