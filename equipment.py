import json
import os

FILE_NAME = "equipment.json"

def load_equipment():
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, "w") as f:
            json.dump({}, f)
    with open(FILE_NAME, "r") as f:
        return json.load(f)

def save_equipment(data):
    with open(FILE_NAME, "w") as f:
        json.dump(data, f, indent=4)

def get_equipment(user_id):
    data = load_equipment()
    return data.get(str(user_id), {
        "weapon": None,
        "armor": None,
        "item": None
    })

def set_equipment(user_id, slot, item_name):
    data = load_equipment()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"weapon": None, "armor": None, "item": None}
    data[uid][slot] = item_name
    save_equipment(data)
