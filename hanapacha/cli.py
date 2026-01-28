import argparse
import sys
from pathlib import Path

from hanapacha import process_scienti_dump_by_ror, process_all_scienti_dumps


"""
Interfaz de línea de comandos (CLI) para Hanapacha.

Este módulo proporciona la funcionalidad CLI que se ejecuta cuando
se usa el comando 'hanapacha' en la terminal.
"""


def parse_arguments():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Hanapacha - Automatización de descarga y procesamiento de dumps desde Google Drive',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  hanapacha                                    Procesa todas las carpetas
  hanapacha --ror 03bp5hc83                   Procesa solo carpetas con ROR ID específico
  hanapacha --ror 03bp5hc83 --cvlac-user UDEA_CV --gruplac-user UDEA_GR

Variables de entorno:
  GOOGLE_CREDENTIALS    Ruta a las credenciales de Google
  GOOGLE_PARENT_ID      ID de la carpeta padre en Drive
        """
    )
    
    parser.add_argument(
        '--ror',
        type=str,
        help='ID del ROR para filtrar carpetas específicas (ej: 03bp5hc83)',
        default=None
    )
    
    parser.add_argument(
        '--credentials',
        type=str,
        help='Ruta al archivo de credenciales de Google (default: token.pickle)',
        default='token.pickle'
    )
    
    parser.add_argument(
        '--parent-id',
        type=str,
        help='ID de la carpeta padre en Google Drive',
        default=None
    )
    
    parser.add_argument(
        '--dump-path',
        type=Path,
        help='Ruta donde guardar los dumps (default: ~/dump)',
        default=Path.home() / "dump"
    )
    
    parser.add_argument(
        '--project-root',
        type=Path,
        help='Ruta raíz del proyecto (default: directorio actual)',
        default=Path.cwd()
    )
    
    # Nuevos parámetros para usuarios personalizados
    parser.add_argument(
        '--cvlac-user',
        type=str,
        help='Usuario personalizado para CVLAC (ej: UDEA_CV). Si no se especifica, se detecta automáticamente.',
        default=None
    )
    
    parser.add_argument(
        '--gruplac-user',
        type=str,
        help='Usuario personalizado para GRUPLAC (ej: UDEA_GR). Si no se especifica, se detecta automáticamente.',
        default=None
    )
    
    parser.add_argument(
        '--institulac-user',
        type=str,
        help='Usuario personalizado para INSTITULAC (ej: UDEA_IN). Si no se especifica, se detecta automáticamente.',
        default=None
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.4'
    )
    
    return parser.parse_args()


def print_results(result: dict):
    """
    Imprime los resultados del procesamiento.
    
    Args:
        result: Diccionario con los resultados
    """
    print(f"\n{'='*60}")
    print("\n🎉 Proceso completado.")
    print(f"📊 Carpetas procesadas: {result['folders_processed']}")
    print(f"✅ Exitosas: {result['folders_successful']}")
    print(f"❌ Fallidas: {result['folders_failed']}")
    
    if result['errors']:
        print("\n📋 Detalle de errores:")
        for error in result['errors']:
            print(f"  • {error}")
    
    if result['env_files']:
        print(f"\n📝 Archivos .env generados: {len(result['env_files'])}")
        for env_file in result['env_files']:
            print(f"  • {env_file}")


def main():
    """Punto de entrada principal para la CLI."""
    args = parse_arguments()
    
    # Validar que tenemos las credenciales y parent_id
    credentials_path = args.credentials
    parent_id = args.parent_id
    
    # Intentar obtener de variables de entorno si no se proporcionaron
    if not Path(credentials_path).exists():
        print(f"❌ Error: No se encontraron credenciales en '{credentials_path}'")
        print("   Proporciona la ruta con --credentials o configura GOOGLE_CREDENTIALS")
        sys.exit(1)
    
    if not parent_id:
        # Intentar leer de archivo de configuración o variable de entorno
        try:
            from hanapacha.config.settings import settings
            parent_id = settings.GOOGLE_PARENT_ID
        except (ImportError, AttributeError):
            print("❌ Error: Debes proporcionar --parent-id o configurar GOOGLE_PARENT_ID")
            sys.exit(1)
    
    # Mostrar información de usuarios personalizados si se especificaron
    if any([args.cvlac_user, args.gruplac_user, args.institulac_user]):
        print("\n🔧 Usuarios personalizados:")
        if args.cvlac_user:
            print(f"   CVLAC_USER: {args.cvlac_user}")
        if args.gruplac_user:
            print(f"   GRUPLAC_USER: {args.gruplac_user}")
        if args.institulac_user:
            print(f"   INSTITULAC_USER: {args.institulac_user}")
    
    try:
        if args.ror:
            # Procesar carpeta específica por ROR ID
            print(f"\n🔍 Procesando carpetas con ROR ID: {args.ror}")
            result = process_scienti_dump_by_ror(
                credentials_path=credentials_path,
                parent_folder_id=parent_id,
                ror_id=args.ror,
                base_dump_path=args.dump_path,
                project_root=args.project_root,
                cvlac_user=args.cvlac_user,
                gruplac_user=args.gruplac_user,
                institulac_user=args.institulac_user,
            )
        else:
            # Procesar todas las carpetas
            print("\n📁 Procesando todas las carpetas...")
            result = process_all_scienti_dumps(
                credentials_path=credentials_path,
                parent_folder_id=parent_id,
                base_dump_path=args.dump_path,
                project_root=args.project_root,
                cvlac_user=args.cvlac_user,
                gruplac_user=args.gruplac_user,
                institulac_user=args.institulac_user,
            )
        
        # Mostrar resultados
        print_results(result)
        
        # Exit code basado en el resultado
        sys.exit(0 if result['success'] else 1)
        
    except ValueError as e:
        print(f"\n❌ Error de validación: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n❌ Archivo no encontrado: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()