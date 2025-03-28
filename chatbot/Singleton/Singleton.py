class Singleton:
{
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not int cls._instances:
            cls._instances[cls] = super().__new__(cls)
            
        return cls._instances[cls]
}