from pathlib import Path
from typing import Optional, Dict, List, Any

from .drive.drive_service import DriveService
from .workflows.folder_workflow import FolderWorkflow
from .processors.dump_metadata import DumpMetadata
from .processors.config_env_generator import EnvGenerator
from .processors.zip_processor import ZipProcessor

"""
Hanapacha - Automatización para descarga y procesamiento de dumps desde Google Drive

Esta librería permite:
- Descargar carpetas de Google Drive
- Seleccionar automáticamente el ZIP más reciente
- Procesar dumps de Oracle (CV, GR, IN)
- Generar configuración para contenedores Docker
- Ejecutar conversión Oracle a MongoDB

Uso como librería (para Airflow):
    from hanapacha import process_scienti_dump_by_ror, process_all_scienti_dumps
    
    # Procesar un ROR específico (usa docker-compose.yml incluido)
    result = process_scienti_dump_by_ror(
        credentials_path="token.pickle",
        parent_folder_id="your-folder-id",
        ror_id="03bp5hc83",
        run_docker=True
    )
    
    # Con docker-compose.yml personalizado
    result = process_scienti_dump_by_ror(
        credentials_path="token.pickle",
        parent_folder_id="your-folder-id",
        ror_id="03bp5hc83",
        run_docker=True,
        docker_compose_file=Path("/path/to/docker-compose.yml")
    )
    
    # Con usuarios personalizados
    result = process_scienti_dump_by_ror(
        credentials_path="token.pickle",
        parent_folder_id="your-folder-id",
        ror_id="03bp5hc83",
        cvlac_user="CUSTOM_CV",
        gruplac_user="CUSTOM_GR",
        institulac_user="CUSTOM_IN"
    )

Uso como CLI:
    hanapacha --ror 03bp5hc83 --run-docker
    hanapacha --ror 03bp5hc83 --run-docker --docker-compose /path/to/docker-compose.yml
"""

__version__ = "0.1.9"
__author__ = "Esteban Cossio"

# Exportar API pública
__all__ = [
    "process_scienti_dump_by_ror",
    "process_all_scienti_dumps",
    "DriveService",
    "FolderWorkflow",
    "DumpMetadata",
    "EnvGenerator",
    "ZipProcessor",
]


def process_scienti_dump_by_ror(
    credentials_path: str,
    parent_folder_id: str,
    ror_id: str,
    base_dump_path: Optional[Path] = None,
    project_root: Optional[Path] = None,
    cvlac_user: Optional[str] = None,
    gruplac_user: Optional[str] = None,
    institulac_user: Optional[str] = None,
    run_docker: bool = False,
    docker_compose_file: Optional[Path] = None,
    docker_work_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Procesa dumps para un ROR ID específico.

    Args:
        credentials_path: Ruta al archivo de credenciales de Google (token.pickle)
        parent_folder_id: ID de la carpeta padre en Google Drive
        ror_id: ID del ROR a procesar (ej: "03bp5hc83")
        base_dump_path: Ruta donde guardar los dumps (default: ~/dump)
        project_root: Ruta raíz del proyecto (default: directorio actual)
        cvlac_user: Usuario personalizado para CVLAC (opcional, default: {prefix}_CV)
        gruplac_user: Usuario personalizado para GRUPLAC (opcional, default: {prefix}_GR)
        institulac_user: Usuario personalizado para INSTITULAC (opcional, default: {prefix}_IN)
        run_docker: Si True, ejecuta docker-compose up/down (default: False)
        docker_compose_file: Ruta al docker-compose.yml personalizado (opcional, usa el incluido si no se especifica)
        docker_work_dir: Directorio de trabajo para Docker (default: project_root)

    Returns:
        Dict con información del resultado:
        {
            "success": bool,
            "ror_id": str,
            "folders_processed": int,
            "folders_successful": int,
            "folders_failed": int,
            "errors": List[str],
            "env_files": List[Path]
        }

    Raises:
        ValueError: Si el ROR ID no es válido o no se encuentran carpetas
        FileNotFoundError: Si las credenciales no existen

    Example:
        >>> from hanapacha import process_scienti_dump_by_ror
        >>> from pathlib import Path
        >>> 
        >>> # Con docker-compose incluido
        >>> result = process_scienti_dump_by_ror(
        ...     credentials_path="token.pickle",
        ...     parent_folder_id="abc123",
        ...     ror_id="03bp5hc83",
        ...     run_docker=True
        ... )
        >>> 
        >>> # Con docker-compose personalizado
        >>> result = process_scienti_dump_by_ror(
        ...     credentials_path="token.pickle",
        ...     parent_folder_id="abc123",
        ...     ror_id="03bp5hc83",
        ...     run_docker=True,
        ...     docker_compose_file=Path("/opt/scienti/docker-compose.yml")
        ... )
    """
    if base_dump_path is None:
        base_dump_path = Path.home() / "dump"

    if project_root is None:
        project_root = Path.cwd()

    # Inicializar servicio de Drive
    drive_service = DriveService(credentials_path)

    # Obtener todas las carpetas
    all_folders = drive_service.get_folders(parent_folder_id)

    if not all_folders:
        raise ValueError("No se encontraron carpetas en Google Drive")

    # Filtrar por ROR ID
    folders = _filter_folders_by_ror_id(all_folders, ror_id)

    if not folders:
        raise ValueError(f"No se encontraron carpetas con ROR ID '{ror_id}'")

    # Procesar carpetas
    return _process_folders(
        folders=folders,
        drive_service=drive_service,
        base_dump_path=base_dump_path,
        project_root=project_root,
        ror_id=ror_id,
        cvlac_user=cvlac_user,
        gruplac_user=gruplac_user,
        institulac_user=institulac_user,
        run_docker=run_docker,
        docker_compose_file=docker_compose_file,
        docker_work_dir=docker_work_dir,
    )


def process_all_scienti_dumps(
    credentials_path: str,
    parent_folder_id: str,
    base_dump_path: Optional[Path] = None,
    project_root: Optional[Path] = None,
    cvlac_user: Optional[str] = None,
    gruplac_user: Optional[str] = None,
    institulac_user: Optional[str] = None,
    run_docker: bool = False,
    docker_compose_file: Optional[Path] = None,
    docker_work_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Procesa dumps de todas las carpetas en Google Drive.

    Args:
        credentials_path: Ruta al archivo de credenciales de Google (token.pickle)
        parent_folder_id: ID de la carpeta padre en Google Drive
        base_dump_path: Ruta donde guardar los dumps (default: ~/dump)
        project_root: Ruta raíz del proyecto (default: directorio actual)
        cvlac_user: Usuario personalizado para CVLAC (opcional, default: {prefix}_CV)
        gruplac_user: Usuario personalizado para GRUPLAC (opcional, default: {prefix}_GR)
        institulac_user: Usuario personalizado para INSTITULAC (opcional, default: {prefix}_IN)
        run_docker: Si True, ejecuta docker-compose up/down (default: False)
        docker_compose_file: Ruta al docker-compose.yml personalizado (opcional, usa el incluido si no se especifica)
        docker_work_dir: Directorio de trabajo para Docker (default: project_root)

    Returns:
        Dict con información del resultado

    Example:
        >>> from hanapacha import process_all_scienti_dumps
        >>> result = process_all_scienti_dumps(
        ...     credentials_path="token.pickle",
        ...     parent_folder_id="abc123",
        ...     run_docker=True
        ... )
    """
    if base_dump_path is None:
        base_dump_path = Path.home() / "dump"

    if project_root is None:
        project_root = Path.cwd()

    # Inicializar servicio de Drive
    drive_service = DriveService(credentials_path)

    # Obtener todas las carpetas
    folders = drive_service.get_folders(parent_folder_id)

    if not folders:
        raise ValueError("No se encontraron carpetas en Google Drive")

    # Procesar todas las carpetas
    return _process_folders(
        folders=folders,
        drive_service=drive_service,
        base_dump_path=base_dump_path,
        project_root=project_root,
        cvlac_user=cvlac_user,
        gruplac_user=gruplac_user,
        institulac_user=institulac_user,
        run_docker=run_docker,
        docker_compose_file=docker_compose_file,
        docker_work_dir=docker_work_dir,
    )


def _filter_folders_by_ror_id(folders: List[Dict], ror_id: str) -> List[Dict]:
    """Filtra carpetas que coincidan con el ror_id."""
    filtered = []
    for folder in folders:
        folder_name = folder["name"]
        if "_" in folder_name:
            folder_ror_id = folder_name.split("_")[0]
            if folder_ror_id == ror_id:
                filtered.append(folder)
    return filtered


def _process_folders(
    folders: List[Dict],
    drive_service: DriveService,
    base_dump_path: Path,
    project_root: Path,
    ror_id: Optional[str] = None,
    cvlac_user: Optional[str] = None,
    gruplac_user: Optional[str] = None,
    institulac_user: Optional[str] = None,
    run_docker: bool = False,
    docker_compose_file: Optional[Path] = None,
    docker_work_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Procesa una lista de carpetas."""
    workflow = FolderWorkflow(
        drive=drive_service,
        base_dump=base_dump_path,
        project_root=project_root,
        cvlac_user=cvlac_user,
        gruplac_user=gruplac_user,
        institulac_user=institulac_user,
        run_docker=run_docker,
        docker_compose_file=docker_compose_file,
        docker_work_dir=docker_work_dir,
    )

    successful = 0
    failed = 0
    errors = []
    env_files = []

    for folder in folders:
        try:
            result = workflow.process_folder(folder)
            if result:
                successful += 1
                env_files.append(result)
            else:
                failed += 1
                errors.append(f"Carpeta '{folder['name']}' sin .env generado")
        except Exception as e:
            failed += 1
            error_msg = f"Error en carpeta '{folder['name']}': {str(e)}"
            errors.append(error_msg)

    return {
        "success": failed == 0,
        "ror_id": ror_id,
        "folders_processed": len(folders),
        "folders_successful": successful,
        "folders_failed": failed,
        "errors": errors,
        "env_files": env_files,
    }