from abstract.Observer.Observer import Observer

class Observable:
    

    _observers = None


    def __init__(self):
        self._observers = []
        pass


    def add_observer(self, observer:Observer):
        self._observers.append(observer)


    def remove_observer(self, observer:Observer):
        self._observers.remove(observer)


    async def notify_observers(self):
        for observer in self._observers:
            await observer.notify()