# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common.project.project_client import ProjectObject

from api.api_container.api_container_user import send_email_user


def test_send_email_user_sends_request_to_notification_service_with_expected_payload(requests_mocker, settings):
    post_mock = requests_mocker.post(f'{settings.NOTIFY_SERVICE}/v1/email/', json={})

    recipient_email = 'recipient@test'
    user = {'email': recipient_email}
    project = ProjectObject({'name': 'project_name', 'code': 'project_code'}, None)
    current_identity = {'username': 'inviter_name', 'email': 'inviter_email'}

    send_email_user(user, project, 'recipient_name', 'admin', 'subject', 'template_name', current_identity)

    assert post_mock.called_once is True

    post_payload = post_mock.last_request.json()

    expected_payload = {
        'subject': 'subject',
        'sender': settings.EMAIL_SUPPORT_REPLY_TO,
        'receiver': [recipient_email],
        'msg_type': 'html',
        'attachments': [],
        'template': 'template_name',
        'template_kwargs': {
            'username': 'recipient_name',
            'admin_name': 'inviter_name',
            'inviter_name': 'inviter_name',
            'inviter_email': 'inviter_email',
            'project_name': 'project_name',
            'project_code': 'project_code',
            'project_role': 'Project Administrator',
            'role': 'Project Administrator',
            'user_email': recipient_email,
            'login_url': settings.INVITATION_URL_LOGIN,
            'register_url': settings.EMAIL_PROJECT_REGISTER_URL,
            'admin_email': settings.EMAIL_ADMIN,
            'support_email': settings.EMAIL_SUPPORT,
            'support_url': settings.EMAIL_PROJECT_SUPPORT_URL,
        },
    }

    assert post_payload == expected_payload
