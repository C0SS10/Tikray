import subprocess
from pathlib import Path
from .base_command import Command


class DockerUpCommand(Command):
    def __init__(self, compose_file: Path, env_file: Path):
        self.compose_file = compose_file
        self.env_file = env_file

    def execute(self):
        print("🐳 Iniciando contenedor Oracle con docker-compose...")
        
        # Convertir a rutas absolutas
        compose_file_abs = self.compose_file.resolve() if isinstance(self.compose_file, Path) else Path(self.compose_file).resolve()
        env_file_abs = self.env_file.resolve() if isinstance(self.env_file, Path) else Path(self.env_file).resolve()
        
        print(f"   Compose file: {compose_file_abs}")
        print(f"   Env file: {env_file_abs}")
        
        subprocess.run(
            [
                "docker", "compose",
                "-f", str(compose_file_abs),
                "--env-file", str(env_file_abs),
                "up", "-d"
            ],
            check=True,
        )