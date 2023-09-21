# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

def get_admin_policy(project_code):
    template = '''
    {
        "Version": "2012-10-17",
        "Statement": [
            {
            "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
            "Effect": "Allow",
            "Resource": ["arn:aws:s3:::gr-%s", "arn:aws:s3:::core-%s"]
            },
            {
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Effect": "Allow",
            "Resource": ["arn:aws:s3:::gr-%s/*", "arn:aws:s3:::core-%s/*"]
            }
        ]
    }
    ''' % (  # noqa: FS001
        project_code,
        project_code,
        project_code,
        project_code,
    )
    return template


def get_collaborator_policy(project_code):
    template = '''
    {
        "Version": "2012-10-17",
        "Statement": [
            {
            "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
            "Effect": "Allow",
            "Resource": ["arn:aws:s3:::gr-%s", "arn:aws:s3:::core-%s"]
            },
            {
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Effect": "Allow",
            "Resource": ["arn:aws:s3:::gr-%s/${jwt:preferred_username}/*", "arn:aws:s3:::core-%s/*"]
            }
        ]
    }
    ''' % (  # noqa: FS001
        project_code,
        project_code,
        project_code,
        project_code,
    )
    return template


def get_contributor_policy(project_code):
    template = '''
    {
        "Version": "2012-10-17",
        "Statement": [
            {
            "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
            "Effect": "Allow",
            "Resource": ["arn:aws:s3:::gr-%s", "arn:aws:s3:::core-%s"]
            },
            {
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Effect": "Allow",
            "Resource": [
                "arn:aws:s3:::gr-%s/${jwt:preferred_username}/*",
                "arn:aws:s3:::core-%s/${jwt:preferred_username}/*"
            ]
            }
        ]
    }
    ''' % (  # noqa: FS001
        project_code,
        project_code,
        project_code,
        project_code,
    )
    return template
