from sqlalchemy import text
from app.db.session import engine

queries = [
    "DELETE FROM inventory_movements WHERE deleted_at IS NOT NULL",
    "DELETE FROM expenses WHERE deleted_at IS NOT NULL",
    "DELETE FROM phones WHERE deleted_at IS NOT NULL",
    "DELETE FROM shipments WHERE deleted_at IS NOT NULL",
    "DELETE FROM inventory_items WHERE deleted_at IS NOT NULL",
]

with engine.begin() as conn:
    for query in queries:
        conn.execute(text(query))

print("Deleted all soft-deleted rows from database.")