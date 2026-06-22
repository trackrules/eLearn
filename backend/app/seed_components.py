from slugify import slugify
from .db import get_conn

COMPONENTS = {
    "radiator fan": ["cooling fan", "engine cooling fan", "fan motor", "radiator cooling fan"],
    "coolant temperature sensor": ["coolant sensor", "engine coolant temperature sensor", "temperature sender", "water temperature sensor"],
    "ABS pump": ["ABS hydraulic unit", "ABS control unit", "brake hydraulic unit"],
    "engine ECU": ["engine control unit", "injection ECU", "ECM", "powertrain control module"],
    "fuel pump": ["electric fuel pump", "fuel delivery pump", "petrol pump"],
    "crank sensor": ["crankshaft sensor", "rpm sensor", "engine speed sensor"],
    "heater blower": ["blower motor", "heater fan", "interior fan", "ventilation fan"],
    "lambda sensor": ["oxygen sensor", "O2 sensor", "exhaust oxygen sensor"],
    "starter motor": ["starter", "starting motor"],
    "alternator": ["generator", "charging generator"],
}

def seed():
    with get_conn() as conn:
        vehicle = conn.execute("SELECT id FROM vehicles WHERE source_code='186'").fetchone()
        if not vehicle:
            vehicle = conn.execute("INSERT INTO vehicles(make, model, source_code) VALUES('Fiat','Multipla','186') RETURNING id").fetchone()
        count = 0
        for name, aliases in COMPONENTS.items():
            comp = conn.execute("""
                INSERT INTO components(vehicle_id, name, slug)
                VALUES (%s, %s, %s)
                ON CONFLICT (vehicle_id, slug) DO UPDATE SET name=EXCLUDED.name, updated_at=now()
                RETURNING id
            """, (vehicle["id"], name, slugify(name))).fetchone()
            for alias in aliases:
                conn.execute("INSERT INTO component_aliases(component_id, alias) VALUES(%s, %s) ON CONFLICT DO NOTHING", (comp["id"], alias))
            count += 1
    return {"seeded_components": count}

if __name__ == "__main__":
    print(seed())
