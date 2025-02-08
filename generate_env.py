import json
import os

# Cargar el archivo de configuración
config_path = 'config.json'

if os.path.exists(config_path):
    with open(config_path, 'r') as file:
        config = json.load(file)
else:
    raise FileNotFoundError(f"El archivo {config_path} no existe.")

# Crear un archivo .env
with open('.env', 'w') as env_file:
    for key, value in config.items():
        env_file.write(f"{key}={value}\n")

print(".env file creado con éxito.")
