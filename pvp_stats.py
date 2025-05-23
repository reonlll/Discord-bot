def weapon_power(weapon_name):
    power_table = {
        "木の剣": 1,
        "鉄の剣": 2,
        "炎の剣": 3,
    }
    return power_table.get(weapon_name, 1)

def armor_defense(armor_name):
    defense_table = {
        "布の服": 1,
        "鉄の鎧": 2,
        "ドラゴンアーマー": 3,
    }
    return defense_table.get(armor_name, 1)
