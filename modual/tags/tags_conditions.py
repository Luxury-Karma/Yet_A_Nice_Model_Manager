"""
@Project: modual/tags/tags_condition.py
@Author: Alexandre Gauvin
Handles conditional tags that can be created by the user
"""


class TagsConditions(object):
    def __init__(self):
        self.tag:str = ''
        self.rule:str = ''
        self.rule_value:str = ''
        self.is_reverse:bool = False


    def save_object(self):
        """
        Save the condition for a specific tag
        :return:
        """
        pass

    def delete_object(self):
        """
        Delete the condition for a specific tag
        :return:
        """

    def create_condition(self):
        """
        Create the condition a tag need to meet
        """
        pass