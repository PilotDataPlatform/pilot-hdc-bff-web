# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

class MetaAPI(type):
    def __new__(cls, name: str, bases, namespace, **kwargs):
        if not name.startswith('API'):
            raise TypeError('[Fatal] Invalid API Statement: class name should start with "API"', name)
        if 'api_registry' not in namespace:
            raise TypeError('[Fatal] Invalid API Statement: Function api_registry Not Found ', name)
        return super().__new__(cls, name, bases, namespace, **kwargs)
