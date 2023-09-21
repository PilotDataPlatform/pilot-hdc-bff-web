# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json

import aioredis
import jwt
from fastapi import Request
from httpx import AsyncClient

from app.logger import logger
from config import ConfigClass


async def jwt_required(request: Request):
    current_identity = await get_current_identity(request)
    if not current_identity:
        raise Exception("couldn't get user from jwt")
    return current_identity


async def get_token(request: Request):
    token = request.headers.get('Authorization')
    if not token:
        return None
    return token.split()[-1]


async def check_cache(username):
    if ConfigClass.ENABLE_USER_CACHE:
        try:
            redis = await aioredis.from_url(ConfigClass.REDIS_URL)
            user_key = f'current_identity-{username}'
            if await redis.exists(user_key):
                return json.loads(await (redis.get(user_key)))
        except Exception as e:
            logger.error(f"Couldn't connect to redis, skipping cache: {e}")
    return False


async def set_cache(username, result):
    if ConfigClass.ENABLE_USER_CACHE:
        try:
            redis = await aioredis.from_url(ConfigClass.REDIS_URL)
            user_key = f'current_identity-{username}'
            await redis.set(user_key, json.dumps(result), ConfigClass.USER_CACHE_EXPIRY)
        except Exception as e:
            logger.error(f"Couldn't connect to redis, skipping cache: {e}")
    return False


async def get_current_identity(request: Request):
    token = await get_token(request)
    payload = jwt.decode(token, options={'verify_signature': False})
    username: str = payload.get('preferred_username')

    if not username:
        return None

    data = {
        'username': username,
        'exact': True,
    }
    cached_result = await check_cache(username)
    if cached_result:
        return cached_result

    async with AsyncClient(timeout=ConfigClass.SERVICE_CLIENT_TIMEOUT) as client:
        response = await client.get(ConfigClass.AUTH_SERVICE + 'admin/user', params=data)
        if response.status_code != 200:
            raise Exception(f'Error getting user {username} from auth service: ' + response.json())

    user = response.json()['result']
    if not user:
        return None

    if user['attributes'].get('status') != 'active':
        return None

    user_id = user['id']
    email = user['email']
    first_name = user['first_name']
    last_name = user['last_name']
    role = None
    if 'role' in user:
        role = user['role']

    try:
        realm_roles = payload['realm_access']['roles']
    except Exception as e:
        logger.error(f"Couldn't get realm roles: {e}")
        realm_roles = []
    result = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'realm_roles': realm_roles,
    }
    await set_cache(username, result)
    return result
