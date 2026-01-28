from pathlib import Path
from datetime import datetime
from typing import Optional

from hanapacha.commands.wait_for_complete_command import WaitForKaypachaCommand
from hanapacha.commands.docker_down_command import DockerDownCommand
from hanapacha.commands.docker_up_command import DockerUpCommand
from hanapacha.orchestrator.command_executor import CommandExecutor
from hanapacha.drive.drive_service import DriveService
from hanapacha.processors.config_env_generator import EnvGenerator
from hanapacha.processors.dump_metadata import DumpMetadata
from hanapacha.processors.zip_processor import ZipProcessor
from hanapacha.utils.docker_resources import get_docker_compose_path, copy_docker_compose_to_dir


class FolderWorkflow:
    def __init__(
        self,
        drive: DriveService,
        base_dump: Path,
        project_root: Path,
        cvlac_user: Optional[str] = None,
        gruplac_user: Optional[str] = None,
        institulac_user: Optional[str] = None,
        run_docker: bool = False,
        docker_compose_file: Optional[Path] = None,
        docker_work_dir: Optional[Path] = None,
    ):
        """
        Inicializa el workflow de procesamiento de carpetas.
        
        Args:
            drive: Servicio de Google Drive
            base_dump: Ruta base para guardar dumps
            project_root: Ruta raíz del proyecto
            cvlac_user: Usuario personalizado para CVLAC (opcional)
            gruplac_user: Usuario personalizado para GRUPLAC (opcional)
            institulac_user: Usuario personalizado para INSTITULAC (opcional)
            run_docker: Si True, ejecuta docker-compose up/down (default: False)
            docker_compose_file: Ruta al docker-compose.yml personalizado (opcional)
            docker_work_dir: Directorio de trabajo para Docker (default: project_root)
        """
        self.drive = drive
        self.base_dump = base_dump
        self.project_root = project_root
        self.cvlac_user = cvlac_user
        self.gruplac_user = gruplac_user
        self.institulac_user = institulac_user
        self.run_docker = run_docker
        self.docker_work_dir = docker_work_dir or project_root
        
        # Determinar qué docker-compose.yml usar
        if docker_compose_file:
            # Usuario proporcionó su propio docker-compose.yml
            if not docker_compose_file.exists():
                raise FileNotFoundError(f"Archivo docker-compose.yml no encontrado: {docker_compose_file}")
            self.docker_compose_file = docker_compose_file
            self.docker_compose_dir = docker_compose_file.parent
        elif run_docker:
            # Usar el docker-compose.yml incluido en la librería
            # Copiarlo al directorio de trabajo
            self.docker_compose_dir = self.docker_work_dir
            self.docker_compose_file = copy_docker_compose_to_dir(self.docker_compose_dir)
            print(f"  📋 Usando docker-compose.yml de hanapacha en: {self.docker_compose_file}")
        else:
            self.docker_compose_file = None
            self.docker_compose_dir = None

    def parse_zip_date(self, filename: str) -> datetime | None:
        """Extrae la fecha del nombre del archivo ZIP."""
        try:
            name_without_ext = filename.replace(".zip", "")
            parts = name_without_ext.split("_")

            if len(parts) >= 4:
                date_part = parts[-2]
                time_part = parts[-1]
                datetime_str = f"{date_part} {time_part.replace('-', ':')}"
                return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        except (ValueError, IndexError) as e:
            print(f"  ⚠️ No se pudo parsear fecha del archivo '{filename}': {e}")
            return None
        return None

    def get_most_recent_zip(self, files: list) -> dict | None:
        """Selecciona el archivo ZIP más reciente."""
        zip_files = [f for f in files if f["name"].endswith(".zip")]

        if not zip_files:
            return None

        if len(zip_files) == 1:
            return zip_files[0]

        print(f"  📦 Se encontraron {len(zip_files)} archivos ZIP, seleccionando el más reciente...")

        files_with_dates = []
        for zip_file in zip_files:
            parsed_date = self.parse_zip_date(zip_file["name"])
            if parsed_date:
                files_with_dates.append((zip_file, parsed_date))
                print(f"    - {zip_file['name']} → {parsed_date.strftime('%Y-%m-%d %H:%M')}")

        if files_with_dates:
            most_recent = max(files_with_dates, key=lambda x: x[1])
            print(f"  ✅ Seleccionado: {most_recent[0]['name']} (más reciente por nombre)")
            return most_recent[0]

        print("  ⚠️ No se pudo extraer fecha de los nombres, usando createdTime de Drive")
        most_recent = max(zip_files, key=lambda x: x.get("createdTime", ""))
        print(f"  ✅ Seleccionado: {most_recent['name']} (más reciente por createdTime)")
        return most_recent

    def process_folder(self, folder):
        """Procesa una carpeta: descarga, descomprime, detecta dumps y genera config."""
        folder_name = folder["name"]
        folder_id = folder["id"]

        local_folder = self.base_dump / folder_name
        local_folder.mkdir(exist_ok=True)

        print(f"\n📁 Carpeta: {folder_name}")

        files = self.drive.get_files(folder_id)
        if not files:
            print("  ⚠️ Vacía.")
            return None

        most_recent_zip_file = self.get_most_recent_zip(files)

        if not most_recent_zip_file:
            print("  ⚠️ No hay archivos ZIP → no se genera .config.env")
            return None

        zip_path = local_folder / most_recent_zip_file["name"]
        print(f"  ⬇️ Descargando ZIP más reciente: {most_recent_zip_file['name']}")
        self.drive.download_file(most_recent_zip_file["id"], zip_path)

        ZipProcessor.unzip(zip_path, local_folder)

        prefix, date = DumpMetadata.extract(zip_path.name)
        dump_files, detected_prefix = DumpMetadata.detect_dump_files(prefix, date, local_folder)

        # Generar config.env en el directorio de docker-compose
        env_file = EnvGenerator.create(
            prefix=detected_prefix,
            date=date,
            dump_files=dump_files,
            dump_folder=local_folder,
            docker_compose_dir=self.docker_compose_dir if self.run_docker else None,
            cvlac_user=self.cvlac_user,
            gruplac_user=self.gruplac_user,
            institulac_user=self.institulac_user,
        )

        if self.run_docker and env_file:
            print("  🐳 Ejecutando Docker Compose...")
            assert self.docker_compose_file is not None
            executor = CommandExecutor()

            executor.add(DockerUpCommand(compose_file=self.docker_compose_file, env_file=env_file))
            executor.add(WaitForKaypachaCommand(container_name="scienti-oracle-docker-1"))
            executor.add(DockerDownCommand(compose_file=self.docker_compose_file, env_file=env_file))

            executor.run()
        elif env_file:
            print("  ℹ️ Docker deshabilitado - solo se generó config.env")

        return env_file