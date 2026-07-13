import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from modual.sql.session_creator import engine, session_local, Base
from modual.sql.querry import tag, create_tag, get_all_tags, add_rule_to_tag, remove_rule_to_tag, get_tag_id_by_name, \
    rule, model

import re

def get_all_rules_for_tag(tag_name:str) -> list[rule]:
    """
    returns a list of rules belonging to a tag
    :param tag_name: name of the tag
    :return: list of rules
    """
    db = session_local()
    return db.query(tag).filter(tag.tag_name == tag_name).all()

def make_rule_to_action(rule_id:int, tag_name:str, model_evaluated:model ) -> bool:
    """
    Take a rule from the DB, convert it to a python condition.
    then test the rule on a model's information and return if the
    tag belong

    :param rule_id: rule to test
    :return: Boolean of whether the rule belongs
    """

    db = session_local()
    r:rule = db.query(rule).filter(rule.id == rule_id).first()
    name:tag = db.query(tag).filter(tag.tag_name == tag_name).first()
    match str(r.type).lower():
        case "regex":
            if not re.match(r.value, name.name):
                return False
        case "contain":
            if r.value not in name.name:
                return False
        case "type":
            # TODO : add the model type the type of the file inside of the DB
            if model_evaluated.
        case _:
            print("not a valid format")
            return False

    return True