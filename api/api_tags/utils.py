# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.


def get_new_tags(operation: str, entity: dict, new_tags: list):
    if operation == 'add':
        new_tags = entity['extended']['extra']['tags'] + new_tags
    else:
        new_tags = [i for i in entity['extended']['extra']['tags'] if i not in new_tags]
    return list(set(new_tags))
