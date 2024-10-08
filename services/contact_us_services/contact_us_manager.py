# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from config import ConfigClass
from models.contact_us import ContactUsForm
from models.service_meta_class import MetaService
from services.notifier_services.email_service import SrvEmail


class SrvContactUsManager(metaclass=MetaService):
    async def send_contact_us_email(self, contact_us_form: ContactUsForm):
        email_sender = SrvEmail()

        await email_sender.async_send(
            ConfigClass.EMAIL_CONTACT_US_SUBJECT,
            [ConfigClass.EMAIL_SUPPORT],
            msg_type='html',
            attachments=contact_us_form.attachments,
            template='contact_us/support_email.html',
            template_kwargs={
                'title': contact_us_form.title,
                'category': contact_us_form.category,
                'description': contact_us_form.description,
                'user_email': contact_us_form.email,
            },
        )

        await email_sender.async_send(
            ConfigClass.EMAIL_CONTACT_US_CONFIRMATION_SUBJECT,
            [contact_us_form.email],
            msg_type='html',
            attachments=contact_us_form.attachments,
            template='contact_us/confirm_email.html',
            template_kwargs={
                'title': contact_us_form.title,
                'category': contact_us_form.category,
                'description': contact_us_form.description,
                'email': ConfigClass.EMAIL_SUPPORT,
            },
        )
