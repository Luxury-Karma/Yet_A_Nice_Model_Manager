# TODO: This should handle all of the modual at once and be the base launch
from modual.sql.session_creator import engine,  Base, session_local
from modual.sql.querry import model, tag, create_tag, add_rule_to_tag


def start_db() -> None:
    """
    Start db connection and ensure basic tags are present for the user
    :return: None
    """
    print("🤖 Connecting to SQLite database engine...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables initialized successfully!")
    db = session_local()
    try:
        if db.query(tag).count() == 0:
            print("🌱 Database is empty. Seeding baseline category tags...")
            list_of_base_tags:list[str] = ['Miniature', 'Figurine', 'Functional', 'FDM', 'Resin']
            for e in list_of_base_tags:
                create_tag(e)
            add_rule_to_tag(list_of_base_tags[3], "type", "3mf", False)
            add_rule_to_tag(list_of_base_tags[4], "type", "stl", False)
            db.add_all([tag(name=tag_name) for tag_name in list_of_base_tags])
            db.commit()
            print("🌱 Seeding complete.")
        db.close()
    finally:
        db.close()
 

def main():
    # Start DB and ensure basic options are present
    start_db()


if __name__ == "__main__":
    main()