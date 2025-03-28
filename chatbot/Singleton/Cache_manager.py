import aioredis
import json
import os

class Cache_manager(Singleton, Observer):
{
    self._redis = None

    async def __init__(self):
        await start()

    async def start(self)
        const = Constants_manager()
        self._redis_url = const.REDIS_URL
        await connect()

    async def connect(self):
    """Conectar a Redis de forma asíncrona"""
        self._redis = await aioredis.from_url(self._redis_url, decode_responses=True)

    async def set_cache(self, key, value, expiration=3600):
    """Guardar en caché una respuesta"""
        if self._redis:
            await self._redis.set(key, json.dumps(value), ex=expiration)

    async def get_cache(self, key):
    """Obtener un valor desde la caché"""
        if self._redis:
            cached_value = await self._redis.get(key)
            return json.loads(cached_value) if cached_value else None

    async def close(self):
    """Cerrar conexión con Redis"""
        if self._redis:
            await self._redis.close()

    async def notify(self):
        await close()
        await start()
}