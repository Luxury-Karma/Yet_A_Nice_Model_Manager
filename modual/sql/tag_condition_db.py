import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from modual.sql.session_creator import engine, session_local, Base
from modual.sql.querry import tag, create_tag, get_all_tags, add_rule_to_tag, remove_rule_to_tag, get_tag_id_by_name
from modual.tags.tags_conditions import TagsConditions

def add_tag_condition_db(condition:TagsConditions):
    """
    Add a condition to meet inside of the tag DB
    :param condition: condition to add to a specific tag
    :return:
    """
    db = session_local()

    if condition.tag not in get_all_tags():
        # tag does not exist lets create it
        create_tag(condition.tag)
    tag_id:int = get_tag_id_by_name(condition.tag)
    rule_type = condition.rule
    rule_value = condition.rule_value
    is_reverse = condition.is_reverse
    add_rule_to_tag(tag_id, rule_type, rule_value, is_reverse)


def remove_condition_db(condition:TagsConditions):
    """
    Remove a condition to meet inside of the tag DB
    :param condition: condition to remove to a specific tag
    :return:
    """
    # TODO : instead send the tag id over network when removed will be easier
    remove_rule_to_tag(condition.tag)
