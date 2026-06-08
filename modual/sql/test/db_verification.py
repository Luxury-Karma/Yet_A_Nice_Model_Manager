"""
@Project: modual/sql/view_db.py
@Author: Alexandre Gauvin
Quick inspection utility to view data inside library.db
"""
import os
import sys

# Ensure Python can see the parent workspace components
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from modual.sql.session_creator import session_local
from modual.sql.querry import model, tag, model_tags


def inspect_database_contents():
    db = session_local()
    try:
        print("\n=== 🏷️  AVAILABLE BASELINE TAGS ===")
        tags = db.query(tag).all()
        for t in tags:
            print(f"  ID {t.id}: [{t.name}]")

        print("\n=== 📦 SAMPLE DISCOVERED MODELS (FIRST 5) ===")
        # Grab the first 5 entries to inspect their columns and many-to-many tag relations
        models_sample = db.query(model).limit(5).all()

        for m in models_sample:
            # Flatten out the relational tag objects attached to this file entry
            model_tag_names = [t.name for t in m.tags]

            print(f"🔹 Model ID: {m.id}")
            print(f"   📄 Name:     {m.file_name}")
            print(f"   📁 Path:     {m.file_path}")
            print(f"   ⚖️  Size:     {m.file_size:,} bytes")
            print(f"   📅 Added:    {m.date_added}")
            print(f"   🏷️ Tags:     {model_tag_names}")
            print(f"   📐 Box Size: {m.dimension_x}x{m.dimension_y}x{m.dimension_z}")
            print("-" * 50)

        # Print out raw counts to confirm total indexing metrics matches your script output
        total_models = db.query(model).count()
        total_associations = db.query(model_tags).count()
        print(f"\n📊 Quick Metrics: {total_models} models indexed across {total_associations} tag associations.")

    finally:
        db.close()


if __name__ == "__main__":
    inspect_database_contents()