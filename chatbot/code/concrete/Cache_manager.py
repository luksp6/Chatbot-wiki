from abstract.Singleton.Singleton import Singleton
from abstract.Observer.Observer import Observer
from abstract.Composite.Compound_service import Compound_service

from concrete.Constants_manager import Constants_manager
from concrete.DB_manager import DB_manager

from redis import Redis
from langchain_redis import RedisSemanticCache

class Cache_manager(Singleton, Observer, Compound_service):
    

    def __init__(self, services_to_wait=[]):
        Compound_service.__init__(self, services_to_wait)
        self._cache = None


    async def notify(self):
        await self.clear_cache()
        await self.disconnect()
        await self.connect()
        await self.wait_for_connection()


    async def _connect(self):
        """Conectar a Redis de forma asíncrona."""
        if self._service is None:
            const = Constants_manager.get_instance(Constants_manager)
            db = DB_manager.get_instance(DB_manager)
            self._service = Redis(host=const.REDIS_HOST, port=const.REDIS_PORT)
            self._cache = RedisSemanticCache(
                redis_client=self._service,
                embeddings= db.get_embeddings(),
                distance_threshold=const.CACHE_THRESHOLD,
                ttl=const.CACHE_TTL
            )
            self._connected.set()


    async def _disconnect(self):
        """Cerrar conexión con Redis"""
        if self._service:
            await self._service.close()
            self._service = None
            self._cache = None


    async def clear_cache(self):
        """Limpiar cache"""
        if self._cache:
            await self._cache.aclear()        


    def get_cache_instance(self):
        """Devuelve la instancia de RedisSemanticCache."""
        if not self._service:
            raise ValueError("CacheManager aún no está conectado. Espera un momento e intenta de nuevo.")
        if not self._cache:
            raise ValueError("SemanticCache aún no está conectado. Espera un momento e intenta de nuevo.")
        return self._cache