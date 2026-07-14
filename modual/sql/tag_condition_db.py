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

# TODO: We should also allowed search on every information from a model insted. Or maybe add an advance search
def make_rule_to_action(rule_id:int, tag_name:str, model_evaluated:model ) -> bool:
    """
    Take the rules from the DB make them in python, then action them
    :param rule_id: id of the rule
    :param tag_name: name of the tag
    :param model_evaluated: model evaluated
    :return:
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
            if model_evaluated.type != r.value:
                return False
        case "directory":
            if r.value in model_evaluated.director :
                return False
        case _:
            print("not a valid format")
            return False

    return True

def test_all_models_on_tags() -> dict[str,int]:
    """
    Update all models to apply a rule
    :return:
    """
    db = session_local()
    model_updated:dict = {}
    try:
        for m in db.query(model).all():
            for t in db.query(tag).all():

                if t in m.tags:
                    continue

                for r in get_all_rules_for_tag(t.tag_name):
                    if not  make_rule_to_action(r.id, t.name, m):
                        continue
                    m.tags.append(t)
                    db.refresh(m)
                    db.commit()  # TODO: verify if commiting every time is slower then once
                    model_updated[t.name] = model_updated[t.name] + 1 if model_updated.keys().__contains__(t.name) else 1
    finally:
        db.close()
    return model_updated
