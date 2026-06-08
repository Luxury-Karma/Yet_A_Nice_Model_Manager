"""
@Project: modual/sql/add_models_to_db.py
@Author: Alexandre Gauvin
Handles back-end storage indexing metrics for local 3D assets.
"""
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from modual.sql.session_creator import engine, session_local, Base
from modual.sql.querry import model, tag
from modual.file_finder import find_all_stl_file_from_directory  # Using the silent crawler for the web API

def sync_directory_pipeline(target_directory: str) -> dict:
    """
    Crawls a target directory silently, filters formats, commits new database rows,
    and returns a metrics payload dictionary back to the Flask routing layer.
    """
    metrics = {"added": 0, "skipped": 0, "failed": 0}

    if not os.path.isdir(target_directory):
        return metrics

    # Ensure tables are built
    Base.metadata.create_all(bind=engine)

    # Fire up the silent file crawler to protect the web server console from tqdm crashes
    discovered_files = find_all_stl_file_from_directory(target_directory)
    if not discovered_files:
        return metrics

    db = session_local()
    try:
        # Fetch existing tags to resolve format relations smoothly
        existing_tags = {t.name.lower(): t for t in db.query(tag).all()}

        for file_path, detected_format in discovered_files.items():
            try:
                # Deduplication check
                is_duplicate = db.query(model).filter(model.file_path == file_path).first()
                if is_duplicate:
                    metrics["skipped"] += 1
                    continue

                # Extract filesystem tracking timestamps
                try:
                    stats = os.stat(file_path)
                    file_size_bytes = stats.st_size
                    time_created = datetime.fromtimestamp(stats.st_ctime)
                    time_modified = datetime.fromtimestamp(stats.st_mtime)
                except Exception:
                    file_size_bytes = 0
                    time_created = datetime.now()
                    time_modified = datetime.now()

                new_model_record = model(
                    file_name=os.path.basename(file_path),
                    file_path=file_path,
                    file_size=file_size_bytes,
                    date_created=time_created,
                    date_modified=time_modified,
                    date_added=datetime.now(),
                    dimension_x=0,
                    dimension_y=0,
                    dimension_z=0
                )

                # Link lowercase format extensions (e.g., 'stl', '3mf')
                clean_format = detected_format.lower()
                if clean_format in existing_tags:
                    new_model_record.tags.append(existing_tags[clean_format])
                elif "miniature" in existing_tags and clean_format in ["stl", "obj"]:
                    new_model_record.tags.append(existing_tags["miniature"])

                db.add(new_model_record)
                metrics["added"] += 1

            except Exception:
                metrics["failed"] += 1
                continue

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ Core sync pipeline failed: {e}")
        raise e
    finally:
        db.close()

    return metrics


def sync_directory_to_database(target_path: str):
    """Fallback wrapper to preserve backward compatibility for local testing scripts."""
    print(f"🔍 Initializing manual local fallback crawl on: {target_path}")
    results = sync_directory_pipeline(target_path)
    print("--------------------------------------------------")
    print(f"📊 Local Fallback Summary:")
    print(f"   ✨ Newly Indexed Models: {results['added']}")
    print(f"   ⏩ Skipped (Duplicates): {results['skipped']}")
    print(f"   ❌ Faulted Failures:     {results['failed']}")
    print("--------------------------------------------------")


if __name__ == "__main__":
    TEST_DIRECTORY = "D:\\wh40k"
    sync_directory_to_database(TEST_DIRECTORY)