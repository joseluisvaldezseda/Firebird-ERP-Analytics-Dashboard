import papermill as pm
import os
import logging
from datetime import datetime

# Configuración de Rutas
BASE_DIR = r"C:\Users\JOSE\Downloads\Streamlit App"
NOTEBOOKS_DIR = os.path.join(BASE_DIR, "lectura_informacion")
LOG_FILE = os.path.join(BASE_DIR, "ejecucion_log.txt")

# Configurar Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def ejecutar_notebook(nombre_notebook):
    path_input = os.path.join(NOTEBOOKS_DIR, nombre_notebook)
    # Crea una versión ejecutada para auditoría (opcional)
    path_output = os.path.join(NOTEBOOKS_DIR, f"Ejecutado_{nombre_notebook}")
    
    try:
        print(f"Ejecutando: {nombre_notebook}...")
        pm.execute_notebook(
            path_input,
            path_output,
            cwd=NOTEBOOKS_DIR # Asegura que el notebook vea sus carpetas locales
        )
        logging.info(f"ÉXITO: {nombre_notebook} ejecutado correctamente.")
        return True
    except Exception as e:
        logging.error(f"ERROR en {nombre_notebook}: {str(e)}")
        print(f"Error crítico en {nombre_notebook}. Revisa el log.")
        return False

def main():
    # Orden de ejecución definido por ti
    pipeline = [
        "Conexion_Base_Tienda1.ipynb",
        "Conexion_Base_Tienda2.ipynb",
        "Conexion_Base_Tienda3.ipynb",
        "Conexion_Base_Tienda4.ipynb"
    ]
    
    start_time = datetime.now()
    logging.info("--- Iniciando proceso de actualización semanal ---")
    
    for notebook in pipeline:
        success = ejecutar_notebook(notebook)
        if not success:
            logging.error("Pipeline detenido debido a un error previo.")
            break
    else:
        logging.info("--- Pipeline finalizado con éxito total ---")
        print("Proceso completado exitosamente.")

if __name__ == "__main__":
    main()