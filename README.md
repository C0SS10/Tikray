# 🚀 Tikray

Automatización para descarga y procesamiento de dumps desde Google Drive para conversión Oracle a MongoDB.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Descripción

Tikray es una herramienta que automatiza el proceso completo de:

- 📥 Descarga de carpetas desde Google Drive
- 🎯 Selección automática del archivo ZIP más reciente
- 📦 Descompresión de archivos
- 🔍 Detección inteligente de archivos dump (.dmp)
- ⚙️ Generación de configuración para contenedores Docker
- 🐳 Ejecución de conversión Oracle → MongoDB

## ✨ Características

- ✅ **Selección inteligente**: Siempre toma el ZIP más reciente
- ✅ **Filtrado por ROR ID**: Procesa instituciones específicas
- ✅ **Detección flexible**: Encuentra dumps con diferentes prefijos
- ✅ **Doble interfaz**: Úsala como CLI o como librería
- ✅ **Logs descriptivos**: Sabe exactamente qué está pasando

## 🚀 Instalación

### Desde PyPI

```bash
pip install tikray
```

### Desde código fuente

```bash
git clone https://github.com/C0SS10/tikray.git
cd tikray
pip install -e .
```

## 📖 Uso

### Como CLI (Línea de Comandos)

```bash
# Procesar todas las carpetas
tikray

# Procesar carpeta específica por ROR ID
tikray --ror 03bp5hc83

# Especificar credenciales y carpeta padre
tikray --credentials ./token.pickle --parent-id abc123xyz

# Ver ayuda
tikray --help
```

### Como Librería (para Airflow)

```python
from tikray import process_ror_dumps, process_all_dumps

# Procesar un ROR específico
result = process_ror_dumps(
    credentials_path="token.pickle",
    parent_folder_id="your-google-drive-folder-id",
    ror_id="03bp5hc83"
)

if result["success"]:
    print(f"✅ Procesado: {result['folders_successful']} carpetas")
    print(f"📝 Archivos .env: {len(result['env_files'])}")
else:
    print(f"❌ Errores: {result['errors']}")

# Procesar todas las instituciones
result = process_all_dumps(
    credentials_path="token.pickle",
    parent_folder_id="your-google-drive-folder-id"
)
```

### Ejemplo en Airflow DAG

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from tikray import process_ror_dumps

def process_dumps(**context):
    result = process_ror_dumps(
        credentials_path="/path/to/token.pickle",
        parent_folder_id="abc123",
        ror_id="03bp5hc83"
    )

    if not result["success"]:
        raise ValueError(f"Procesamiento falló: {result['errors']}")

    return result

with DAG('tikray_dag', ...) as dag:
    task = PythonOperator(
        task_id='process_ror',
        python_callable=process_dumps,
    )
```

Ver [ejemplo completo de DAG](./airflow_dag_example.py)

## 📁 Formato de Nombres

### Carpetas

```
{ror_id}_{nombreInstitucion}
Ejemplo: 03bp5hc83_Universidad-de-Antioquia
```

### Archivos ZIP

```
{TIPO}_{ROR}_{YYYY-MM-DD}_{HH-MM}.zip
Ejemplos:
  - scienti_03bp5hc83_2026-01-10_08-30.zip
  - CV_03bp5hc83_2024-01-15_14-30.zip
```

### Archivos DMP

```
{PREFIJO}_{CV|GR|IN}_{YYYYMMDD}.dmp
Ejemplos:
  - UDEA_CV_20220721.dmp
  - 03bp5hc83_GR_20240115.dmp
```

## ⚙️ Configuración

### Variables de Entorno

Crea un archivo `.env` o configura estas variables:

```bash
GOOGLE_CREDENTIALS=/path/to/token.pickle
GOOGLE_PARENT_ID=your-google-drive-folder-id
```

### Archivo `config/settings.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_CREDENTIALS: str
    GOOGLE_PARENT_ID: str

    class Config:
        env_file = ".env"

settings = Settings()
```

## 🔧 API Reference

### `process_ror_dumps()`

Procesa dumps para un ROR ID específico.

**Parámetros:**

- `credentials_path` (str): Ruta al archivo de credenciales de Google
- `parent_folder_id` (str): ID de la carpeta padre en Google Drive
- `ror_id` (str): ID del ROR a procesar
- `base_dump_path` (Path, opcional): Ruta para guardar dumps (default: `~/dump`)
- `project_root` (Path, opcional): Ruta raíz del proyecto (default: directorio actual)

**Retorna:**

```python
{
    "success": bool,
    "ror_id": str,
    "folders_processed": int,
    "folders_successful": int,
    "folders_failed": int,
    "errors": List[str],
    "env_files": List[Path]
}
```

### `process_all_dumps()`

Procesa dumps de todas las carpetas.

**Parámetros:** Igual que `process_ror_dumps()` excepto `ror_id`

**Retorna:** Misma estructura que `process_ror_dumps()`

## 🎯 Casos de Uso

### 1. Procesamiento Manual

```bash
tikray --ror 03bp5hc83
```

### 2. Orquestación en Airflow

```python
from tikray import process_ror_dumps

result = process_ror_dumps(...)
```

### 3. Script Automatizado

```python
from tikray import process_all_dumps

results = process_all_dumps(
    credentials_path="token.pickle",
    parent_folder_id="abc123"
)

for error in results["errors"]:
    send_alert(error)
```

## 🐛 Troubleshooting

### Error: "No se encontraron credenciales"

```bash
# Asegúrate de que el archivo existe
ls -la token.pickle

# O especifica la ruta
tikray --credentials /ruta/completa/token.pickle
```

### Error: "No se encontraron dumps válidos"

El sistema busca dumps con formato `PREFIJO_CV/GR/IN_FECHA.dmp`. Si tus archivos tienen otro formato, se usará búsqueda flexible.

### Contenedores Docker huérfanos

```python
# En Airflow, usa callbacks para limpiar
def cleanup(**context):
    import subprocess
    subprocess.run(["docker", "stop", "scienti-oracle-docker-1"])

task = PythonOperator(
    ...,
    on_success_callback=cleanup,
    on_failure_callback=cleanup,
)
```

## 📊 Ejemplo de Salida

```
🔍 Procesando carpetas con ROR ID: 03bp5hc83
✅ Se encontraron 1 carpeta(s) con el ROR ID especificado

============================================================

📁 Carpeta: 03bp5hc83_Universidad-de-Antioquia
📦 Se encontraron 3 archivos ZIP, seleccionando el más reciente...
  - scienti_03bp5hc83_2026-01-01_18-30.zip → 2026-01-01 18:30
  - scienti_03bp5hc83_2026-01-10_08-30.zip → 2026-01-10 08:30
✅ Seleccionado: scienti_03bp5hc83_2026-01-10_08-30.zip (más reciente por nombre)
⬇️ Descargando ZIP más reciente: scienti_03bp5hc83_2026-01-10_08-30.zip
100%...
📦 Extraído: /home/user/dump/03bp5hc83_Universidad-de-Antioquia
✅ Encontrados 3 dumps con prefijo 'UDEA': UDEA_CV_20220721.dmp, ...
📝 Archivo config.env generado
✅ Carpeta procesada exitosamente

============================================================

🎉 Proceso completado.
✅ Exitosas: 1
❌ Fallidas: 0
```

## 📝 Changelog

### 0.1.3 (2026-01-27)

- ✨ Primera versión pública
- 🎯 Selección automática del ZIP más reciente
- 🔍 Filtrado por ROR ID
- 📦 Detección flexible de dumps
- 🐳 Integración con Docker
- 🚀 Soporte para Airflow

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 👥 Autores

- **Esteban Cossio** - _Desarrollo inicial_ - [C0SS10](https://github.com/C0SS10)

## 🙏 Agradecimientos

- Equipo de desarrollo
- ImpactU - Colav

---

**Desarrollado con ❤️ para automatizar el procesamiento de dumps científicos**
