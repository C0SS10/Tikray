# 🚀 Hanapacha

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD--3--Clause-yellow.svg)](https://opensource.org/licenses/BSD-3-Clause)

**Automation tool for downloading and processing Oracle dumps from Google Drive for Oracle → MongoDB conversion.**

Hanapacha automating the entire workflow of downloading Scienti dumps from Google Drive, preparing them, and executing the Oracle to MongoDB conversion.

---

## 📋 Description

Hanapacha automates the complete process of:

- 📥 **Downloading folders from Google Drive** with automatic authentication
- 🎯 **Smart ZIP selection** - always picks the most recent file
- 📦 **Automatic extraction** of compressed files
- 🔍 **Intelligent dump detection** - finds `.dmp` files even with non-standard naming
- ⚙️ **Configuration generation** for Docker containers
- 🐳 **Docker orchestration** for Oracle → MongoDB conversion (optional)

---

## ✨ Features

- ✅ **Intelligent selection**: Automatically chooses the most recent ZIP file by parsing timestamps
- ✅ **ROR ID filtering**: Process specific institutions by Research Organization Registry ID
- ✅ **Flexible dump detection**: Handles both standard and non-standard `.dmp` file naming conventions
- ✅ **Dual interface**: Use as CLI tool or Python library
- ✅ **Airflow integration**: Built for workflow orchestration
- ✅ **Custom user mapping**: Override auto-detected Oracle usernames when needed
- ✅ **Bundled Docker Compose**: Includes pre-configured `docker-compose.yml` for easy setup
- ✅ **Descriptive logging**: Know exactly what's happening at every step

---

## 🚀 Installation

### From PyPI

```bash
pip install hanapacha
```

### From source

```bash
git clone https://github.com/colav/hanapacha.git
cd hanapacha
pip install -e .
```

---

## 📖 Usage

### As CLI (Command Line Interface)

```bash
# Process all folders
hanapacha --credentials ./token.pickle --parent-id YOUR_FOLDER_ID

# Process specific institution by ROR ID
hanapacha --credentials ./token.pickle --parent-id YOUR_FOLDER_ID --ror 03bp5hc83

# With Docker execution (uses bundled docker-compose.yml)
hanapacha --credentials ./token.pickle --parent-id YOUR_FOLDER_ID --ror 03bp5hc83 --run-docker

# With custom docker-compose.yml
hanapacha --credentials ./token.pickle --parent-id YOUR_FOLDER_ID --ror 03bp5hc83 \
  --run-docker --docker-compose /path/to/docker-compose.yml

# With custom Oracle users (when dump files have non-standard names)
hanapacha --credentials ./token.pickle --parent-id YOUR_FOLDER_ID --ror 03bp5hc83 \
  --cvlac-user UDEA_CV --gruplac-user UDEA_GR --institulac-user UDEA_IN

# See all options
hanapacha --help
```

### As Python Library (for Airflow)

```python
from hanapacha import process_scienti_dump_by_ror, process_all_scienti_dumps
from pathlib import Path

# Process a specific ROR ID (uses bundled docker-compose.yml)
result = process_scienti_dump_by_ror(
    credentials_path="token.pickle",
    parent_folder_id="your-google-drive-folder-id",
    ror_id="03bp5hc83",
    run_docker=True
)

# With custom docker-compose.yml
result = process_scienti_dump_by_ror(
    credentials_path="token.pickle",
    parent_folder_id="your-google-drive-folder-id",
    ror_id="03bp5hc83",
    run_docker=True,
    docker_compose_file=Path("/opt/scienti/docker-compose.yml")
)

# With custom Oracle users
result = process_scienti_dump_by_ror(
    credentials_path="token.pickle",
    parent_folder_id="your-google-drive-folder-id",
    ror_id="03bp5hc83",
    cvlac_user="UDEA_CV",
    gruplac_user="UDEA_GR",
    institulac_user="UDEA_IN"
)

# Check results
if result["success"]:
    print(f"✅ Processed: {result['folders_successful']} folders")
    print(f"📝 Config files: {len(result['env_files'])}")
else:
    print(f"❌ Errors: {result['errors']}")

# Process all institutions
result = process_all_scienti_dumps(
    credentials_path="token.pickle",
    parent_folder_id="your-google-drive-folder-id",
    run_docker=True
)
```

### Airflow Integration Example

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from hanapacha import process_scienti_dump_by_ror

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def process_dumps(**context):
    """Process Scienti dumps for a specific institution"""
    result = process_scienti_dump_by_ror(
        credentials_path="/path/to/token.pickle",
        parent_folder_id="abc123",
        ror_id=context['dag_run'].conf.get('ror_id', '03bp5hc83'),
        run_docker=True
    )

    if not result["success"]:
        raise ValueError(f"Processing failed: {result['errors']}")

    return result

with DAG('hanapacha_scienti_processing',
         default_args=default_args,
         schedule_interval='0 2 * * *',
         catchup=False) as dag:

    process_task = PythonOperator(
        task_id='process_scienti_dumps',
        python_callable=process_dumps,
    )
```

See [complete DAG examples](./airflow_dag_example.py)

---

## 📁 File Naming Conventions

### Folders in Google Drive

```
{ror_id}_{institutionName}
Example: 03bp5hc83_Universidad-de-Antioquia
```

### ZIP Files

```
{TYPE}_{ROR}_{YYYY-MM-DD}_{HH-MM}.zip
Examples:
  - scienti_03bp5hc83_2026-01-10_08-30.zip
  - CV_03bp5hc83_2024-01-15_14-30.zip
```

### Dump Files (.dmp)

```
{PREFIX}_{CV|GR|IN}_{YYYYMMDD}.dmp
Examples:
  - UDEA_CV_20220721.dmp
  - 03bp5hc83_GR_20240115.dmp
```

**Note**: Hanapacha includes flexible detection that handles non-standard naming patterns.

---

## ⚙️ Configuration

### Google Drive Authentication

1. Create a Google Cloud project
2. Enable Google Drive API
3. Download OAuth 2.0 credentials
4. Generate `token.pickle` using the OAuth flow

See [Google Drive API documentation](https://developers.google.com/drive/api/guides/about-auth) for details.

### Environment Variables (Optional)

```bash
# .env file
GOOGLE_CREDENTIALS=/path/to/token.pickle
GOOGLE_PARENT_ID=your-google-drive-folder-id
```

### Docker Configuration

Hanapacha includes a pre-configured `docker-compose.yml` that works with [KayPacha's Oracle Docker image](https://github.com/colav/oracle-docker).

Default configuration:

- MongoDB 8.0
- Oracle XE with KayPacha
- Automatic environment variable injection
- Resource limits: 8GB RAM reservation

To use a custom `docker-compose.yml`, pass it via `--docker-compose` (CLI) or `docker_compose_file` (library).

---

## 🔧 API Reference

### `process_scienti_dump_by_ror()`

Process dumps for a specific ROR ID.

**Parameters:**

- `credentials_path` (str): Path to Google credentials file (`token.pickle`)
- `parent_folder_id` (str): Google Drive parent folder ID
- `ror_id` (str): Research Organization Registry ID to process
- `base_dump_path` (Path, optional): Path to save dumps (default: `~/dump`)
- `project_root` (Path, optional): Project root path (default: current directory)
- `cvlac_user` (str, optional): Custom CVLAC Oracle user (default: auto-detected)
- `gruplac_user` (str, optional): Custom GRUPLAC Oracle user (default: auto-detected)
- `institulac_user` (str, optional): Custom INSTITULAC Oracle user (default: auto-detected)
- `run_docker` (bool): Execute docker-compose up/down (default: False)
- `docker_compose_file` (Path, optional): Custom docker-compose.yml path
- `docker_work_dir` (Path, optional): Docker working directory

**Returns:**

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

### `process_all_scienti_dumps()`

Process dumps for all folders in Google Drive.

**Parameters:** Same as `process_scienti_dump_by_ror()` except `ror_id`

**Returns:** Same structure as `process_scienti_dump_by_ror()`

---

## 🎯 Use Cases

### 1. Manual Processing

Download and prepare dumps without Docker execution:

```bash
hanapacha --credentials ./token.pickle --parent-id ABC123 --ror 03bp5hc83
```

### 2. Automated Processing with Docker

Full automation including Oracle → MongoDB conversion:

```bash
hanapacha --credentials ./token.pickle --parent-id ABC123 --ror 03bp5hc83 --run-docker
```

### 3. Airflow Orchestration

Integrate into data pipelines:

```python
from hanapacha import process_scienti_dump_by_ror

result = process_scienti_dump_by_ror(
    credentials_path="token.pickle",
    parent_folder_id="ABC123",
    ror_id="03bp5hc83",
    run_docker=True
)
```

### 4. Batch Processing with Custom Users

Process multiple institutions with non-standard dump naming:

```python
from hanapacha import process_all_scienti_dumps

institutions_config = {
    '03bp5hc83': {'cv': 'UDEA_CV', 'gr': 'UDEA_GR', 'in': 'UDEA_IN'},
    '02xtwpk10': {'cv': 'UEC_CV', 'gr': 'UEC_GR', 'in': 'UEC_IN'},
}

for ror_id, users in institutions_config.items():
    result = process_scienti_dump_by_ror(
        credentials_path="token.pickle",
        parent_folder_id="ABC123",
        ror_id=ror_id,
        cvlac_user=users['cv'],
        gruplac_user=users['gr'],
        institulac_user=users['in'],
        run_docker=True
    )
```

---

## 🐛 Troubleshooting

### Error: "Credentials not found"

**Solution:**

```bash
# Verify file exists
ls -la token.pickle

# Or specify full path
hanapacha --credentials /full/path/to/token.pickle --parent-id ABC123
```

### Error: "No dumps found with prefix"

**Cause:** Dump files have non-standard naming.

**Solution:** Use flexible detection (automatic) or specify custom users:

```bash
hanapacha --ror 03bp5hc83 --cvlac-user CUSTOM_CV --gruplac-user CUSTOM_GR --institulac-user CUSTOM_IN
```

### Orphaned Docker Containers

**Solution:** Use Airflow callbacks for cleanup:

```python
def cleanup_docker(**context):
    import subprocess
    subprocess.run(["docker-compose", "-f", "/path/to/docker-compose.yml", "down"])

task = PythonOperator(
    task_id='process',
    python_callable=process_dumps,
    on_success_callback=cleanup_docker,
    on_failure_callback=cleanup_docker,
)
```

### Error: "docker-compose.yml not found"

**Cause:** Using `--run-docker` without access to bundled compose file.

**Solution:** Hanapacha includes a docker-compose.yml by default. If error persists, verify installation:

```bash
pip show hanapacha | grep Location
# Check if resources/docker-compose.yml exists in that location
```

---

## 📊 Example Output

```
🔧 Configuration:
   Modo Docker: ✅ Habilitado
   Docker Compose: Incluido en hanapacha

🔍 Procesando carpetas con ROR ID: 03bp5hc83

📁 Carpeta: 03bp5hc83_Universidad-de-Antioquia
  📦 Se encontraron 2 archivos ZIP, seleccionando el más reciente...
    - scienti_03bp5hc83_2026-01-01_18-30.zip → 2026-01-01 18:30
    - scienti_03bp5hc83_2026-01-10_08-30.zip → 2026-01-10 08:30
  ✅ Seleccionado: scienti_03bp5hc83_2026-01-10_08-30.zip (más reciente por nombre)
  ⬇️ Descargando ZIP más reciente: scienti_03bp5hc83_2026-01-10_08-30.zip
  100%...
  📦 Extraído: /home/user/dump/03bp5hc83_Universidad-de-Antioquia
  🔍 No se encontraron dumps con prefijo '03bp5hc83', buscando con cualquier prefijo...
  ✅ Encontrados 3 dumps con prefijo 'UDEA': UDEA_CV_20220721.dmp, UDEA_GR_20220721.dmp, UDEA_IN_20220721.dmp
  📝 Archivo config.env generado en: /home/user/dump/03bp5hc83_Universidad-de-Antioquia/config.env
  🐳 Ejecutando Docker Compose...
  ✅ Kaypacha terminó exitosamente

============================================================

🎉 Proceso completado.
📊 Carpetas procesadas: 1
✅ Exitosas: 1
❌ Fallidas: 0
```

---

## 🔄 Workflow Integration

Hanapacha is designed to work seamlessly with:

1. **[KayPacha](https://github.com/colav/KayPacha)**: Oracle → MongoDB data extraction
2. **[UkuPacha](https://github.com/colav/UkuPacha)**: MongoDB data processing
3. **Airflow**: Workflow orchestration
4. **Google Drive**: Source data storage

### Typical Workflow

```
Google Drive (raw dumps)
    ↓
Hanapacha (download + prepare)
    ↓
KayPacha (Oracle → MongoDB)
    ↓
UkuPacha (data processing)
    ↓
Final MongoDB (processed data)
```

---

## 📝 Changelog

### 0.1.8 (2026-01-28)

- ✨ Initial public release
- 🎯 Automatic selection of most recent ZIP files
- 🔍 ROR ID filtering
- 📦 Flexible dump detection with auto-prefix discovery
- 🐳 Docker integration with bundled docker-compose.yml
- 👤 Custom Oracle user mapping
- 🚀 Airflow support with example DAGs
- 📋 Comprehensive CLI interface
- 📚 Complete API for library usage

---

## 📄 License

This project is licensed under the BSD 3-Clause License. See [LICENSE](LICENSE) for details.

---

## 👥 Authors

- **Esteban Cossio** - _Initial development_ - [C0SS10](https://github.com/C0SS10)

### Contributors

See the list of [contributors](https://github.com/colav/hanapacha/contributors) who participated in this project.

---

## 🙏 Acknowledgments

- **Colav Team** - Research group at Universidad de Antioquia
- **ImpactU Project** - Funding and support

---

## 🔗 Links

- **KayPacha**: https://github.com/colav/KayPacha
- **UkuPacha**: https://github.com/colav/UkuPacha
- **Oracle Docker**: https://github.com/colav/oracle-docker

---

**Developed with ❤️ by Colav to automate scientific database processing**
