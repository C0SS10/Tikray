"""
Ejemplo de DAG de Airflow usando Hanapacha como librería.

Este DAG muestra cómo usar hanapacha en Airflow para procesar dumps
de forma programática, con mejor control de errores y manejo de recursos.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from pathlib import Path

# Importar hanapacha como librería
from hanapacha import process_ror_dumps, process_all_dumps


# Configuración por defecto del DAG
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['tu@email.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}


def process_specific_ror(**context):
    """
    Procesa dumps para un ROR ID específico.
    
    Esta función se ejecuta en un PythonOperator y usa hanapacha
    como librería importada.
    """
    ror_id = context['dag_run'].conf.get('ror_id', '03bp5hc83')
    
    print(f"🚀 Iniciando procesamiento para ROR ID: {ror_id}")
    
    try:
        result = process_ror_dumps(
            credentials_path="/path/to/token.pickle",
            parent_folder_id="your-google-drive-folder-id",
            ror_id=ror_id,
            base_dump_path=Path("/tmp/dumps"),
            project_root=Path("/opt/airflow/scienti"),
        )
        
        # Log de resultados
        print(f"✅ Procesamiento completado")
        print(f"   Carpetas procesadas: {result['folders_processed']}")
        print(f"   Exitosas: {result['folders_successful']}")
        print(f"   Fallidas: {result['folders_failed']}")
        
        # Guardar resultados en XCom para siguiente tarea
        context['task_instance'].xcom_push(key='processing_result', value=result)
        
        # Si hubo errores, logearlos pero no fallar
        if result['errors']:
            print("⚠️ Errores encontrados:")
            for error in result['errors']:
                print(f"   - {error}")
        
        # Solo fallar si ninguna carpeta se procesó exitosamente
        if result['folders_successful'] == 0:
            raise ValueError("No se pudo procesar ninguna carpeta exitosamente")
        
        return result
        
    except Exception as e:
        print(f"❌ Error en procesamiento: {e}")
        raise


def process_all_institutions(**context):
    """
    Procesa dumps de todas las instituciones.
    """
    print("🚀 Iniciando procesamiento de todas las instituciones")
    
    try:
        result = process_all_dumps(
            credentials_path="/path/to/token.pickle",
            parent_folder_id="your-google-drive-folder-id",
            base_dump_path=Path("/tmp/dumps"),
            project_root=Path("/opt/airflow/scienti"),
        )
        
        print(f"✅ Procesamiento completado")
        print(f"   Total procesado: {result['folders_processed']}")
        print(f"   Exitosas: {result['folders_successful']}")
        print(f"   Fallidas: {result['folders_failed']}")
        
        context['task_instance'].xcom_push(key='processing_result', value=result)
        
        return result
        
    except Exception as e:
        print(f"❌ Error en procesamiento: {e}")
        raise


def cleanup_resources(**context):
    """
    Limpia recursos y contenedores Docker huérfanos.
    
    Esta función se ejecuta siempre (on_success_callback y on_failure_callback)
    para asegurar que no queden contenedores corriendo.
    """
    import subprocess
    
    print("🧹 Limpiando recursos...")
    
    try:
        # Detener contenedores de scienti si están corriendo
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", "name=scienti"],
            capture_output=True,
            text=True,
        )
        
        if result.stdout.strip():
            print("   Deteniendo contenedores de scienti...")
            subprocess.run(["docker", "stop"] + result.stdout.strip().split())
            subprocess.run(["docker", "rm"] + result.stdout.strip().split())
            print("   ✅ Contenedores detenidos y eliminados")
        else:
            print("   ℹ️ No hay contenedores de scienti corriendo")
            
    except Exception as e:
        print(f"   ⚠️ Error en limpieza: {e}")


def notify_results(**context):
    """
    Notifica los resultados del procesamiento.
    """
    result = context['task_instance'].xcom_pull(
        task_ids='process_ror_task',
        key='processing_result'
    )
    
    if result:
        message = f"""
        Procesamiento Hanapacha Completado
        
        Carpetas procesadas: {result['folders_processed']}
        Exitosas: {result['folders_successful']}
        Fallidas: {result['folders_failed']}
        
        Archivos .env generados: {len(result.get('env_files', []))}
        """
        
        print(message)
        # Aquí podrías enviar a Slack, email, etc.


# Definir el DAG
with DAG(
    'hanapacha_process_ror',
    default_args=default_args,
    description='Procesar dumps de ROR específico usando Hanapacha',
    schedule_interval='0 2 * * *',  # Diario a las 2 AM
    catchup=False,
    tags=['hanapacha', 'dumps', 'oracle', 'mongodb'],
) as dag:
    
    # Tarea principal: procesar dumps
    process_task = PythonOperator(
        task_id='process_ror_task',
        python_callable=process_specific_ror,
        on_success_callback=cleanup_resources,
        on_failure_callback=cleanup_resources,
    )
    
    # Tarea de notificación
    notify_task = PythonOperator(
        task_id='notify_results',
        python_callable=notify_results,
    )
    
    # Definir dependencias
    process_task >> notify_task


# DAG alternativo para procesar todas las instituciones
with DAG(
    'hanapacha_process_all',
    default_args=default_args,
    description='Procesar dumps de todas las instituciones usando Hanapacha',
    schedule_interval='0 3 * * 0',  # Semanal, domingos a las 3 AM
    catchup=False,
    tags=['hanapacha', 'dumps', 'oracle', 'mongodb', 'batch'],
) as dag_all:
    
    process_all_task = PythonOperator(
        task_id='process_all_institutions',
        python_callable=process_all_institutions,
        on_success_callback=cleanup_resources,
        on_failure_callback=cleanup_resources,
    )
