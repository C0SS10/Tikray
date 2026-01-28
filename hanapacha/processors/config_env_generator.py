from pathlib import Path
from typing import Optional


class EnvGenerator:
    @staticmethod
    def create(
        prefix: str,
        date: str,
        dump_files: list[str],
        project_root: Path,
        dump_folder: Path,
        cvlac_user: Optional[str] = None,
        gruplac_user: Optional[str] = None,
        institulac_user: Optional[str] = None,
    ):
        """
        Genera archivo config.env con variables de ambiente.
        
        Args:
            prefix: Prefijo base detectado de los dumps
            date: Fecha del dump
            dump_files: Lista de archivos .dmp
            project_root: Ruta raíz del proyecto
            dump_folder: Carpeta donde están los dumps
            cvlac_user: Usuario de CVLAC (opcional, default: {prefix}_CV)
            gruplac_user: Usuario de GRUPLAC (opcional, default: {prefix}_GR)
            institulac_user: Usuario de INSTITULAC (opcional, default: {prefix}_IN)
        
        Returns:
            Path al archivo config.env generado
        """
        dump_files_joined = ",".join(dump_files)
        dump_abs = dump_folder.as_posix()

        # Usar valores personalizados o construir con el prefijo
        cv_user = cvlac_user if cvlac_user else f"{prefix}_CV"
        gr_user = gruplac_user if gruplac_user else f"{prefix}_GR"
        in_user = institulac_user if institulac_user else f"{prefix}_IN"

        env_content = f"""#!/bin/bash

export CVLAC_USER="{cv_user}"
export GRUPLAC_USER="{gr_user}"
export INSTITULAC_USER="{in_user}"
export ORACLE_PWD="colavudea"

export DUMP_PATH="{dump_abs}"
export DUMP_DATE="{date}"
export DUMP_FILES="{dump_files_joined}"

export HUNABKU_PORT=9090
"""

        env_path = project_root / "scienti" / "config.env"
        env_path.write_text(env_content)

        print(f"📝 Archivo config.env generado en: {env_path}")
        if cvlac_user or gruplac_user or institulac_user:
            print(f"   ℹ️ Usando usuarios personalizados:")
            if cvlac_user:
                print(f"      CVLAC_USER: {cv_user}")
            if gruplac_user:
                print(f"      GRUPLAC_USER: {gr_user}")
            if institulac_user:
                print(f"      INSTITULAC_USER: {in_user}")
        
        return env_path