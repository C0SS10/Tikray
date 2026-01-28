from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from pathlib import Path

# Importar hanapacha como librería
from hanapacha import process_scienti_dump_by_ror, process_all_scienti_dumps


"""
Ejemplo de DAG de Airflow usando Hanapacha como librería con usuarios personalizados.

Este DAG muestra cómo usar hanapacha en Airflow para procesar dumps,
incluyendo cómo especificar usuarios personalizados cuando los nombres
de los archivos .dmp no siguen el estándar.
"""


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


def process_with_auto_detection(**context):
    """
    Procesa dumps con detección automática de usuarios.
    
    Hanapacha detectará automáticamente el prefijo de los archivos .dmp
    y construirá los usuarios como: {prefix}_CV, {prefix}_GR, {prefix}_IN
    """
    ror_id = context['dag_run'].conf.get('ror_id', '03bp5hc83')
    
    print(f"🚀 Procesando con detección automática para ROR ID: {ror_id}")
    
    result = process_scienti_dump_by_ror(
        credentials_path="/path/to/token.pickle",
        parent_folder_id="your-google-drive-folder-id",
        ror_id=ror_id,
        base_dump_path=Path("/tmp/dumps"),
        project_root=Path("/opt/airflow/scienti"),
    )
    
    print(f"✅ Resultado: {result['folders_successful']}/{result['folders_processed']} exitosas")
    context['task_instance'].xcom_push(key='result', value=result)
    
    return result


def process_with_custom_users(**context):
    """
    Procesa dumps con usuarios personalizados.
    
    Útil cuando los nombres de los archivos .dmp no siguen el estándar
    y necesitas especificar manualmente los usuarios de Oracle.
    
    Ejemplo:
    - Archivos: UDEA_CV_20220721.dmp, UDEA_GR_20220721.dmp, UDEA_IN_20220721.dmp
    - Usuarios: UDEA_CV, UDEA_GR, UDEA_IN
    """
    ror_id = context['dag_run'].conf.get('ror_id', '03bp5hc83')
    
    # Estos valores pueden venir de:
    # 1. Variables de Airflow
    # 2. Configuración del DAG
    # 3. Base de datos
    # 4. API externa
    custom_users = {
        'cvlac_user': 'UDEA_CV',
        'gruplac_user': 'UDEA_GR',
        'institulac_user': 'UDEA_IN',
    }
    
    print(f"🚀 Procesando con usuarios personalizados para ROR ID: {ror_id}")
    print(f"   Usuarios: {custom_users}")
    
    result = process_scienti_dump_by_ror(
        credentials_path="/path/to/token.pickle",
        parent_folder_id="your-google-drive-folder-id",
        ror_id=ror_id,
        base_dump_path=Path("/tmp/dumps"),
        project_root=Path("/opt/airflow/scienti"),
        **custom_users  # Desempaquetar diccionario de usuarios
    )
    
    print(f"✅ Resultado: {result['folders_successful']}/{result['folders_processed']} exitosas")
    context['task_instance'].xcom_push(key='result', value=result)
    
    return result


def process_with_partial_override(**context):
    """
    Procesa dumps con sobrescritura parcial de usuarios.
    
    Solo especifica los usuarios que necesitas sobrescribir.
    Los demás se detectarán automáticamente.
    """
    ror_id = context['dag_run'].conf.get('ror_id', '03bp5hc83')
    
    print(f"🚀 Procesando con sobrescritura parcial para ROR ID: {ror_id}")
    
    result = process_scienti_dump_by_ror(
        credentials_path="/path/to/token.pickle",
        parent_folder_id="your-google-drive-folder-id",
        ror_id=ror_id,
        base_dump_path=Path("/tmp/dumps"),
        project_root=Path("/opt/airflow/scienti"),
        cvlac_user="CUSTOM_CV",  # Solo sobrescribir CVLAC
        # gruplac_user y institulac_user se detectarán automáticamente
    )
    
    print(f"✅ Resultado: {result['folders_successful']}/{result['folders_processed']} exitosas")
    context['task_instance'].xcom_push(key='result', value=result)
    
    return result


def process_from_variable(**context):
    """
    Procesa dumps obteniendo usuarios de Airflow Variables.
    
    Útil para mantener configuración centralizada y reutilizable.
    """
    from airflow.models import Variable
    
    ror_id = context['dag_run'].conf.get('ror_id', '03bp5hc83')
    
    # Obtener usuarios de Airflow Variables
    # Ejemplo de Variable en Airflow:
    # Key: "scienti_users_03bp5hc83"
    # Value: {"cvlac_user": "UDEA_CV", "gruplac_user": "UDEA_GR", "institulac_user": "UDEA_IN"}
    
    try:
        users_config = Variable.get(f"scienti_users_{ror_id}", deserialize_json=True)
        print(f"📋 Usando configuración de Airflow Variable: {users_config}")
    except KeyError:
        print(f"ℹ️ No se encontró configuración para {ror_id}, usando detección automática")
        users_config = {}
    
    result = process_scienti_dump_by_ror(
        credentials_path="/path/to/token.pickle",
        parent_folder_id="your-google-drive-folder-id",
        ror_id=ror_id,
        base_dump_path=Path("/tmp/dumps"),
        project_root=Path("/opt/airflow/scienti"),
        **users_config
    )
    
    print(f"✅ Resultado: {result['folders_successful']}/{result['folders_processed']} exitosas")
    context['task_instance'].xcom_push(key='result', value=result)
    
    return result


def cleanup_resources(**context):
    """Limpia recursos Docker."""
    import subprocess
    
    print("🧹 Limpiando recursos...")
    
    try:
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


# DAG 1: Con detección automática
with DAG(
    'hanapacha_auto_detection',
    default_args=default_args,
    description='Procesar dumps con detección automática de usuarios',
    schedule_interval='0 2 * * *',
    catchup=False,
    tags=['hanapacha', 'auto'],
) as dag_auto:
    
    task_auto = PythonOperator(
        task_id='process_auto',
        python_callable=process_with_auto_detection,
        on_success_callback=cleanup_resources,
        on_failure_callback=cleanup_resources,
    )


# DAG 2: Con usuarios personalizados
with DAG(
    'hanapacha_custom_users',
    default_args=default_args,
    description='Procesar dumps con usuarios personalizados',
    schedule_interval='0 3 * * *',
    catchup=False,
    tags=['hanapacha', 'custom'],
) as dag_custom:
    
    task_custom = PythonOperator(
        task_id='process_custom',
        python_callable=process_with_custom_users,
        on_success_callback=cleanup_resources,
        on_failure_callback=cleanup_resources,
    )


# DAG 3: Desde Airflow Variables
with DAG(
    'hanapacha_from_variables',
    default_args=default_args,
    description='Procesar dumps usando configuración de Airflow Variables',
    schedule_interval='0 4 * * *',
    catchup=False,
    tags=['hanapacha', 'variables'],
) as dag_variables:
    
    task_variables = PythonOperator(
        task_id='process_from_variables',
        python_callable=process_from_variable,
        on_success_callback=cleanup_resources,
        on_failure_callback=cleanup_resources,
    )