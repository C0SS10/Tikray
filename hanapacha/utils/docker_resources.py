from pathlib import Path
import shutil
import importlib.resources as pkg_resources


def get_docker_compose_path() -> Path:
    """
    Obtiene la ruta al archivo docker-compose.yml incluido en la librería.
    
    Returns:
        Path al archivo docker-compose.yml
    """
    try:
        # Python 3.9+
        if hasattr(pkg_resources, 'files'):
            resources = pkg_resources.files('hanapacha.resources')
            compose_file = resources / 'docker-compose.yml'
            return Path(str(compose_file))
        else:
            # Python 3.7-3.8 fallback
            import pkg_resources as old_pkg
            compose_path = old_pkg.resource_filename('hanapacha.resources', 'docker-compose.yml')
            return Path(compose_path)
    except Exception as e:
        raise FileNotFoundError(
            f"No se pudo encontrar docker-compose.yml en los recursos de hanapacha: {e}"
        )


def copy_docker_compose_to_dir(target_dir: Path) -> Path:
    """
    Copia el docker-compose.yml incluido en la librería a un directorio específico.
    
    Args:
        target_dir: Directorio donde copiar el archivo
    
    Returns:
        Path al archivo copiado
    """
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    source = get_docker_compose_path()
    target = target_dir / 'docker-compose.yml'
    
    shutil.copy2(source, target)
    return target


def get_config_env_path(docker_compose_dir: Path) -> Path:
    """
    Obtiene la ruta donde debe estar el config.env (mismo directorio que docker-compose.yml).
    
    Args:
        docker_compose_dir: Directorio donde está el docker-compose.yml
    
    Returns:
        Path donde debe crearse el config.env
    """
    return Path(docker_compose_dir) / 'config.env'