import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from modual.sql.session_creator import engine, session_local, Base
from modual.sql.querry import tag, create_tag, get_all_tags, add_rule_to_tag, remove_rule_to_tag, get_tag_id_by_name


def add_tag_condition_db(tag_name:str, rule_type:str, rule_value:str, is_reverse:bool, is_auto:bool):
    """
    Add a condition to meet inside of the tag DB
    :param condition: condition to add to a specific tag
    :return:
    """
    db = session_local()

    if tag_name not in get_all_tags():
        # tag does not exist lets create it
        create_tag(name=tag_name, rule_type=rule_type, rule_value=rule_value, is_auto=is_auto)


    add_rule_to_tag(tag_name, rule_type, rule_value, is_reverse)



def remove_condition_db(rule_id: int):
    """
    Remove a condition to meet inside of the tag DB
    :param condition: condition to remove to a specific tag
    :return:
    """
    # TODO : instead send the tag id over network when removed will be easier
    remove_rule_to_tag(rule_id)
