"""
Tikray - Automatización para descarga y procesamiento de dumps desde Google Drive

Esta librería permite:
- Descargar carpetas de Google Drive
- Seleccionar automáticamente el ZIP más reciente
- Procesar dumps de Oracle (CV, GR, IN)
- Generar configuración para contenedores Docker
- Ejecutar conversión Oracle a MongoDB

Uso como librería (para Airflow):
    from tikray import process_ror_dumps, process_all_dumps
    
    # Procesar un ROR específico
    result = process_ror_dumps(
        credentials_path="token.pickle",
        parent_folder_id="your-folder-id",
        ror_id="03bp5hc83"
    )
    
    # Procesar todas las carpetas
    results = process_all_dumps(
        credentials_path="token.pickle",
        parent_folder_id="your-folder-id"
    )

Uso como CLI:
    tikray --ror 03bp5hc83
    tikray  # procesa todas las carpetas
"""

from pathlib import Path
from typing import Optional, Dict, List, Any

from .drive.drive_service import DriveService
from .workflows.folder_workflow import FolderWorkflow
from .processors.dump_metadata import DumpMetadata
from .processors.config_env_generator import EnvGenerator
from .processors.zip_processor import ZipProcessor

__version__ = "0.1.3"
__author__ = "Esteban Cossio"

# Exportar API pública
__all__ = [
    "process_ror_dumps",
    "process_all_dumps",
    "DriveService",
    "FolderWorkflow",
    "DumpMetadata",
    "EnvGenerator",
    "ZipProcessor",
]


def process_ror_dumps(
    credentials_path: str,
    parent_folder_id: str,
    ror_id: str,
    base_dump_path: Optional[Path] = None,
    project_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Procesa dumps para un ROR ID específico.
    
    Esta es la función principal para usar en Airflow cuando quieres
    procesar una institución específica.
    
    Args:
        credentials_path: Ruta al archivo de credenciales de Google (token.pickle)
        parent_folder_id: ID de la carpeta padre en Google Drive
        ror_id: ID del ROR a procesar (ej: "03bp5hc83")
        base_dump_path: Ruta donde guardar los dumps (default: ~/dump)
        project_root: Ruta raíz del proyecto (default: directorio actual)
    
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
        >>> from tikray import process_ror_dumps
        >>> result = process_ror_dumps(
        ...     credentials_path="token.pickle",
        ...     parent_folder_id="abc123",
        ...     ror_id="03bp5hc83"
        ... )
        >>> if result["success"]:
        ...     print(f"Procesado exitosamente: {result['folders_successful']} carpetas")
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
    )


def process_all_dumps(
    credentials_path: str,
    parent_folder_id: str,
    base_dump_path: Optional[Path] = None,
    project_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Procesa dumps de todas las carpetas en Google Drive.
    
    Esta función procesa todas las instituciones sin filtrar por ROR ID.
    
    Args:
        credentials_path: Ruta al archivo de credenciales de Google (token.pickle)
        parent_folder_id: ID de la carpeta padre en Google Drive
        base_dump_path: Ruta donde guardar los dumps (default: ~/dump)
        project_root: Ruta raíz del proyecto (default: directorio actual)
    
    Returns:
        Dict con información del resultado:
        {
            "success": bool,
            "folders_processed": int,
            "folders_successful": int,
            "folders_failed": int,
            "errors": List[str],
            "env_files": List[Path]
        }
    
    Example:
        >>> from tikray import process_all_dumps
        >>> result = process_all_dumps(
        ...     credentials_path="token.pickle",
        ...     parent_folder_id="abc123"
        ... )
        >>> print(f"Total procesado: {result['folders_processed']}")
        >>> print(f"Exitoso: {result['folders_successful']}")
        >>> print(f"Fallido: {result['folders_failed']}")
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
    )


def _filter_folders_by_ror_id(folders: List[Dict], ror_id: str) -> List[Dict]:
    """
    Filtra carpetas que coincidan con el ror_id.
    
    Función interna (privada) para filtrado.
    
    Args:
        folders: Lista de carpetas de Drive
        ror_id: ID del ROR a buscar
    
    Returns:
        Lista filtrada de carpetas
    """
    filtered = []
    for folder in folders:
        folder_name = folder['name']
        if '_' in folder_name:
            folder_ror_id = folder_name.split('_')[0]
            if folder_ror_id == ror_id:
                filtered.append(folder)
    return filtered


def _process_folders(
    folders: List[Dict],
    drive_service: DriveService,
    base_dump_path: Path,
    project_root: Path,
    ror_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Procesa una lista de carpetas.
    
    Función interna (privada) para procesamiento.
    
    Args:
        folders: Lista de carpetas a procesar
        drive_service: Instancia de DriveService
        base_dump_path: Ruta base para dumps
        project_root: Ruta raíz del proyecto
        ror_id: ID del ROR (opcional, solo para logs)
    
    Returns:
        Diccionario con resultados del procesamiento
    """
    workflow = FolderWorkflow(
        drive=drive_service,
        base_dump=base_dump_path,
        project_root=project_root
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