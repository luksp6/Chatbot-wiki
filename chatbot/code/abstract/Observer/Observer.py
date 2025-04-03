from abc import ABC, abstractmethod

class Observer(ABC):

    
    @abstractmethod
    async def notify(self):
        pass