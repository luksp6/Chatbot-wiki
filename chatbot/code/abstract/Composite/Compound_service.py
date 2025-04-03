from abstract.Composite.Service import Service

class Compound_service(Service):
    

    def __init__(self, services_to_wait=[]):
        super().__init__()
        self._services_to_wait = services_to_wait


    def set_services_to_wait(self, services=[]):
        self._services_to_wait = services


    async def connect(self):
        """Sobrescribe el método connect para esperar a todos los servicios."""
        # Conecta todos los servicios primero
        for service in self._services_to_wait:
            await service.wait_for_connection()  # Espera a que cada servicio se conecte

        await super().connect()

    async def wait_for_connection(self):
        """Sobrescribe wait_for_connection para esperar que todos los servicios estén listos."""
        for service in self._services_to_wait:
            await service.wait_for_connection()

        await super().wait_for_connection()