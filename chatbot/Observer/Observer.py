import ABC, abstracmethod

class Observer(ABC):
{
    @abstractmethod
    def notify(self):
        pass
}