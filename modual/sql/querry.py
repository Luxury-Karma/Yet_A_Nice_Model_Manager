"""
@Project: modual/sql/session_creator.py
@Author: Alexandre Gauvin
This file is holding the sql objects and table
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from modual.sql.session_creator import Base

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
    models = relationship("model", secondary=model_tags, back_populates="tags")