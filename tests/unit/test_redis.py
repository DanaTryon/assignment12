import pytest
from unittest.mock import AsyncMock, MagicMock
from app.auth import redis as redis_utils

@pytest.mark.asyncio
async def test_get_redis_initializes(monkeypatch):
    fake_redis = MagicMock()
    monkeypatch.setattr(redis_utils.aioredis, "from_url", lambda url: fake_redis)

    # Clear cached redis client
    if hasattr(redis_utils.get_redis, "redis"):
        delattr(redis_utils.get_redis, "redis")

    client = await redis_utils.get_redis()

    assert client is fake_redis
    assert redis_utils.get_redis.redis is fake_redis

@pytest.mark.asyncio
async def test_add_to_blacklist(monkeypatch):
    mock_redis = AsyncMock()
    monkeypatch.setattr(redis_utils, "get_redis", AsyncMock(return_value=mock_redis))

    jti = "test-jti"
    exp = 60

    await redis_utils.add_to_blacklist(jti, exp)

    mock_redis.set.assert_awaited_once_with(f"blacklist:{jti}", "1", ex=exp)

@pytest.mark.asyncio
async def test_is_blacklisted_true(monkeypatch):
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = True
    monkeypatch.setattr(redis_utils, "get_redis", AsyncMock(return_value=mock_redis))

    jti = "test-jti"
    result = await redis_utils.is_blacklisted(jti)

    mock_redis.exists.assert_awaited_once_with(f"blacklist:{jti}")
    assert result is True

@pytest.mark.asyncio
async def test_is_blacklisted_false(monkeypatch):
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = False
    monkeypatch.setattr(redis_utils, "get_redis", AsyncMock(return_value=mock_redis))

    jti = "test-jti"
    result = await redis_utils.is_blacklisted(jti)

    mock_redis.exists.assert_awaited_once_with(f"blacklist:{jti}")
    assert result is False
