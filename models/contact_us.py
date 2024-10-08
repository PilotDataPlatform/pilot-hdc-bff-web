# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.


class ContactUsForm:
    def __init__(self, event=None):
        if event:
            self._attribute_map = event
        else:
            self._attribute_map = {
                'email': '',
                'category': '',
                'description': '',
                'name': '',
                'title': '',
                'attachments': [],
            }

    @property
    def to_dict(self):
        return self._attribute_map

    @property
    def email(self):
        return self._attribute_map['email']

    @email.setter
    def email(self, email):
        self._attribute_map['email'] = email

    @property
    def category(self):
        return self._attribute_map['category']

    @category.setter
    def category(self, category):
        self._attribute_map['category'] = category

    @property
    def description(self):
        return self._attribute_map['description']

    @description.setter
    def description(self, description):
        self._attribute_map['description'] = description

    @property
    def name(self):
        return self._attribute_map['name']

    @name.setter
    def name(self, name):
        self._attribute_map['name'] = name

    @property
    def title(self):
        return self._attribute_map['title']

    @title.setter
    def title(self, title):
        self._attribute_map['title'] = title

    @property
    def attachments(self):
        return self._attribute_map.get('attachments', [])

    @attachments.setter
    def attachments(self, attachments):
        self._attribute_map['attachments'] = attachments
