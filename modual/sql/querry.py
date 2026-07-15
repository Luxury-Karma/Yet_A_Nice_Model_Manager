"""
@Project: modual/sql/session_creator.py
@Author: Alexandre Gauvin
This file is holding the sql objects and table
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from modual.sql.session_creator import Base
from sqlalchemy.orm import Session
from modual.sql.session_creator import session_local


model_tags = Table(
    "model_tags",
    Base.metadata,
    Column("model_id", Integer, ForeignKey("models.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)

class model(Base):
    __tablename__ = "models"
    # file information
    id = Column(Integer, primary_key=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # TODO: will be shown for upload and download
    date_created = Column(DateTime, nullable=False)
    date_modified = Column(DateTime, nullable=False)
    date_added = Column(DateTime, nullable=False)
    file_type = Column(String, nullable=False)  # TODO: add this to the creation of the object
    # model information
    dimension_x = Column(Integer, nullable=False)  # TODO: need to ensure its always either in imperial or metric. Not both
    dimension_y = Column(Integer, nullable=False)  # probably by using some conversion unit or verifying.
    dimension_z = Column(Integer, nullable=False)  # I have not yet look how they look
    # tags information
    tags = relationship("tag", secondary=model_tags, back_populates="models")


class tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # Relationship: One tag -> Many rules
    rules = relationship("rule", back_populates="tag", cascade="all, delete-orphan")
    models = relationship("model", secondary=model_tags, back_populates="tags")

class rule(Base):
    __tablename__ = "rules"
    id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"))

    # Dictionary-like attributes
    type = Column(String, nullable=False)  # e.g., "contains", "regex"
    value = Column(String, nullable=False)  # e.g., "test"
    is_reverse = Column(Boolean, default=False)

    tag = relationship("tag", back_populates="rules")

# region : helper
def get_all_tags() -> list:
    """Returns a list of all tag objects from
    the database."""
    db: Session = session_local()
    try:
        all_tags = db.query(tag).all()
        return all_tags
    finally:
        db.close()


def create_tag(name: str):
    """
    Creates and saves a new tag to the database.
    """
    db = session_local()
    try:
        new_tag = tag(name=name)
        db.add(new_tag)
        db.commit()
        db.refresh(new_tag)
        return new_tag
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def add_rule_to_tag(tag_name: str, rule_type: str, rule_value: str, is_reverse: bool = False):
    """
    adds a rule to the tag with the given name.
    :param tag_name: name of the tag to be given the rule
    :param rule_type: type of the rule to be added [ Regex, type, contain, directory ]
    :param rule_value: what is the value of the rule [ * , "stl", "test", "/C"
    :param is_reverse: is the rule reversed or not
    :return: Boolean if rule was successfully added
    """
    db = session_local()
    try:
        target_tag = db.query(tag).filter(tag.name == tag_name).first()
        if not target_tag:
            return False

        new_rule = rule(
            type=rule_type,
            value=rule_value,
            is_reverse=is_reverse,
            tag_id=target_tag.id
        )

        db.add(new_rule)
        db.commit()
        return True
    finally:
        db.close()


def remove_rule_to_tag(rule_id: int):
    """
    Remove a rule from the tag with the given id.
    :param rule_id: id of the rule to remove
    :return: Boolean if rule was successfully removed
    """
    db = session_local()
    try:
        # 1. Locate the specific rule
        rule_to_delete = db.query(rule).filter(rule.id == rule_id).first()

        if rule_to_delete:
            db.delete(rule_to_delete)
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_tag_id_by_name(name: str) -> int:
    """
    Returns the id of the tag with the given name.
    :param name: name of the tag
    :return: id of the tag or -1 if not found
    """
    db = session_local()
    try:
        result = db.query(tag).filter(tag.name == name).first()
        if result:
            return result.id
        return -1
    finally:
        db.close()


# endregion