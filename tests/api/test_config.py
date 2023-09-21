# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

class TestSettings:
    def test_project_name_var_is_replaced_in_contact_us_template_subjects(self, settings):
        assert '{project_name}' not in settings.EMAIL_CONTACT_US_SUBJECT
        assert '{project_name}' not in settings.EMAIL_CONTACT_US_CONFIRMATION_SUBJECT
