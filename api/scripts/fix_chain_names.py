"""Fix inconsistent chain names in the database."""
from app.db.session import get_session
from app.db.models import Store

# Chain name normalization mapping
CHAIN_NORMALIZATION = {
    "super_liquor": "Super Liquor",
    "big_barrel": "Big Barrel",
    "black_bull": "Black Bull",
    "bottle_o": "Bottle O",
    "countdown": "Countdown",
    "glengarry": "Glengarry",
    "liquor_centre": "Liquor Centre",
    "liquorland": "Liquorland",
    "new_world": "New World",
    "paknsave": "PAK'nSAVE",
    "thirsty_liquor": "Thirsty Liquor",
}

with get_session() as db:
    for old_name, new_name in CHAIN_NORMALIZATION.items():
        stores = db.query(Store).filter(Store.chain == old_name).all()
        if stores:
            print(f"Updating {len(stores)} stores from '{old_name}' to '{new_name}'")
            for store in stores:
                store.chain = new_name
            db.commit()

    print("\nDone!")
