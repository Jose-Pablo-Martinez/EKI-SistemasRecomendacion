"""
Orquestador de Tareas en Segundo Plano (Jobs Runner).

Este módulo es responsable de gestionar y ejecutar tareas pesadas (jobs) de forma asíncrona,
para evitar bloquear el hilo principal de FastAPI. Proporciona un mecanismo de bloqueo (Locks)
para garantizar que un mismo tipo de tarea no se ejecute concurrentemente, protegiendo así
la integridad de la base de datos y los recursos del sistema.

Implementa el principio Abierto/Cerrado (OCP) de SOLID al usar un registro centralizado
donde nuevos jobs pueden agregarse fácilmente sin modificar la lógica principal de ejecución.
"""

import threading
import logging
import argparse
from typing import Callable, Dict, Optional, Any
from backend.database import SessionLocal

#Registro de Jobs (Patrón Registry para cumplir con OCP de SOLID)

# En lugar de hardcodear los diccionearios en múltiples funciones, lo que se hizo
# fue definir un registro global que lanza el nombre del job con su función

_job_registry: Dict[str, Optional[Callable]] = {}
_job_locks: Dict[str, threading.Lock] = {}

def register_job(name: str, func: Optional[Callable]) -> None:
    """Registra una función de job en el orquestador."""
    _job_registry[name] = func
    _job_locks[name] = threading.Lock()

# Importación dinámica y registro. Si el job aún no se ha creado,
# se registra como None y se manejará el error al intentar llamarlo.
try:
    from backend.jobs.clustering import ejecutar_clustering
    register_job("clustering", ejecutar_clustering)
except ImportError:
    register_job("clustering", None)

try:
    from backend.jobs.generador_recomendaciones import ejecutar_generacion
    register_job("recomendaciones", ejecutar_generacion)
except ImportError:
    register_job("recomendaciones", None)

try:
    from backend.jobs.metricas import ejecutar_metricas
    register_job("metricas", ejecutar_metricas)
except ImportError:
    register_job("metricas", None)

try:
    from backend.jobs.nlp_pipeline import ejecutar_nlp
    register_job("nlp", ejecutar_nlp)
except ImportError:
    register_job("nlp", None)

try:
    from backend.jobs.archivado import ejecutar_archivado
    register_job("archivado", ejecutar_archivado)
except ImportError:
    register_job("archivado", None)


logger = logging.getLogger(__name__)

#Funciones principales

def run_job(job_name: str, db_session_factory: Callable = SessionLocal) -> Dict[str, str]:
    """
    Despacha la ejecución del job especificado en un hilo en segundo plano (daemon thread).

    Verifica si el job está registrado y si no está siendo ejecutado actualmente
    (mediante un Lock no bloqueante). Si todo es correcto, inicia el hilo y 
    retorna inmediatamente.

    Args:
        job_name (str): Identificador del job a ejecutar (ej. "clustering").
        db_session_factory (Callable): Función o clase que retorna una sesión de BD.

    Returns:
        Dict[str, str]: Diccionario con el estado de la operación (enqueued, already_running, error).
    """
    if job_name not in _job_registry:
        raise ValueError(f"Job no reconocido en el registro: {job_name}")

    job_function = _job_registry[job_name]
    if job_function is None:
        logger.error("La función para el job '%s' no ha sido implementada aún.", job_name)
        return {"status": "error", "job": job_name, "note": "Módulo no encontrado"}

    job_lock = _job_locks[job_name]
    
    # Intenta adquirir el lock sin bloquear. Si retorna False, el job ya corre.
    is_lock_acquired = job_lock.acquire(blocking=False)
    if not is_lock_acquired:
        logger.warning("El job '%s' ya se encuentra en ejecución.", job_name)
        return {"status": "already_running", "job": job_name}

    def _execute_in_background() -> None:
        """Wrapper interno ejecutado por el hilo."""
        db_session = None
        try:
            db_session = db_session_factory()
            logger.info("Iniciando procesamiento del job '%s'.", job_name)
            job_function(db_session)
            logger.info("Procesamiento del job '%s' finalizado con éxito.", job_name)
        except Exception as error:
            logger.error("Fallo crítico durante el job '%s': %s", job_name, error)
        finally:
            job_lock.release()
            if db_session:
                db_session.close()

    daemon_thread = threading.Thread(target=_execute_in_background, daemon=True)
    daemon_thread.start()
    
    return {"status": "enqueued", "job": job_name}


def get_job_status(job_name: str) -> dict:
    """
    Consulta el estado actual de un job registrado.
    
    Usa el Lock como fuente de verdad: si se puede adquirir sin bloqueo, 
    el job está disponible (idle). Si no se puede, significa que el job 
    sigue corriendo en un hilo de fondo.
    
    Returns:
        Dict con 'status': 'running' | 'idle' | 'unknown'
    """
    if job_name not in _job_locks:
        return {"status": "unknown", "job": job_name}

    job_lock = _job_locks[job_name]
    acquired = job_lock.acquire(blocking=False)
    if acquired:
        # Pudimos adquirirlo → el job no está corriendo → lo liberamos inmediatamente
        job_lock.release()
        return {"status": "idle", "job": job_name}
    else:
        # No pudimos adquirirlo → el job está corriendo
        return {"status": "running", "job": job_name}


#Interaccion con la linea de comandos (CLI)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    cli_parser = argparse.ArgumentParser(description="Ejecutar jobs offline de EkiSystem de forma manual.")
    cli_parser.add_argument("--job", type=str, required=True, help="Identificador del job a despachar.")
    cli_args = cli_parser.parse_args()
    
    target_job = cli_args.job
    if target_job not in _job_registry:
        logger.error("El job '%s' no existe en el sistema.", target_job)
    else:
        # En modo consola, la ejecución es sincrónica, pero respetamos el Lock
        cli_lock = _job_locks[target_job]
        
        if not cli_lock.acquire(blocking=False):
            logger.warning("El job '%s' está siendo ejecutado actualmente por otro proceso.", target_job)
        else:
            db_session = None
            try:
                db_session = SessionLocal()
                job_function = _job_registry[target_job]
                
                if job_function is not None:
                    logger.info("Despachando job '%s' sincrónicamente desde CLI...", target_job)
                    job_function(db_session)
                    logger.info("Job '%s' completado desde CLI.", target_job)
                else:
                    logger.error("El código del job '%s' aún no está disponible.", target_job)
            finally:
                cli_lock.release()
                if db_session:
                    db_session.close()
