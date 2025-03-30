import asyncio
from abc import ABC, abstractmethod

class Service(ABC):
    def __init__(self):
        self._connected = asyncio.Event()
        self._connection_task = None
        self._service = None
        self._service_name = type(self).__name__

    async def connect(self):
        """Inicia la conexión al servicio si aún no está conectado."""
        if not self._connected.is_set() and self._connection_task is None:
            self._connection_task = asyncio.create_task(self._connect())
            print(f"Iniciando conexión con {self._service_name}...")
            await self._connection_task
            print(f"Conexion a {self._service_name} establecida.")

    async def disconnect(self):
        """Desconecta del servicio si está conectado."""
        if self._connected.is_set():
            print(f"Finalizando conexión con {self._service_name}...")
            await self._disconnect()
            self._connected.clear()
            print(f"Conexion con {self._service_name} finalizada.")

    async def wait_for_connection(self):
        """Espera a que la conexión al servicio esté lista."""
        await self._connected.wait()

    @abstractmethod
    async def _connect(self):
        """Método abstracto que las subclases deben implementar para conectarse al servicio."""
        pass

    @abstractmethod
    async def _disconnect(self):
        """Método abstracto que las subclases deben implementar para desconectarse del servicio."""
        pass