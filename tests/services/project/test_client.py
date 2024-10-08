# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.


class TestProjectServiceClient:
    async def test_convert_project_codes_into_ids_returns_list_of_project_ids(
        self, fake, project_factory, project_service_client
    ):
        project_1 = project_factory.mock_retrieval_by_code()
        project_2 = project_factory.mock_retrieval_by_code()

        received_project_ids = await project_service_client.convert_project_codes_into_ids(
            [project_1.code, project_2.code]
        )

        assert received_project_ids == [project_1.id, project_2.id]
