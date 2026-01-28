import subprocess
from pathlib import Path
from .base_command import Command


class DockerDownCommand(Command):
    def __init__(self, compose_file: Path, env_file: Path | None = None, remove_volumes: bool = False):
        self.compose_file = compose_file
        self.env_file = env_file
        self.remove_volumes = remove_volumes

    def execute(self):
        print("🐳 Deteniendo contenedor Oracle...")
        
        # Convertir a rutas absolutas
        compose_file_abs = self.compose_file.resolve() if isinstance(self.compose_file, Path) else Path(self.compose_file).resolve()
        
        cmd = ["docker", "compose", "-f", str(compose_file_abs)]
        
        if self.env_file:
            env_file_abs = self.env_file.resolve() if isinstance(self.env_file, Path) else Path(self.env_file).resolve()
            cmd += ["--env-file", str(env_file_abs)]
        
        cmd += ["down"]
        
        if self.remove_volumes:
            cmd.append("-v")
        
        subprocess.run(cmd, check=True)