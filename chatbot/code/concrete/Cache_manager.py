from abstract.Singleton.Singleton import Singleton
from abstract.Observer.Observer import Observer
from abstract.Composite.Compound_service import Compound_service

from concrete.Constants_manager import Constants_manager
from concrete.DB_manager import DB_manager

from redis import Redis
from langchain_redis import RedisSemanticCache
from langchain_core.outputs import Generation

import json

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

        
    async def get_cached_answer(self, prompt: str, model_config) -> dict | None:
        """Devuelve un diccionario con 'answer' y 'sources' desde la caché."""
        if self._cache:
            try:
                cached_result = await self._cache.alookup(prompt=prompt, llm_string=model_config)
                if cached_result:
                    try:
                        return json.loads(cached_result[0].text)
                    except Exception as e:
                        print(f"[Cache] Error al decodificar JSON desde cache: {e}")
            except Exception as e:
                print(f"[Cache] Error al obtener cache: {e}")
        return None


    async def set_cached_answer(self, prompt: str, model_config, json_answer):
        """Guarda un diccionario en la caché con la respuesta y sus fuentes."""
        if self._cache:
            try:   
                await self._cache.aupdate(prompt=prompt, llm_string=model_config, return_val=[Generation(text=json.dumps(json_answer))])
            except Exception as e:
                print(f"[Cache] Error al guardar en cache: {e}")