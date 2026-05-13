import subprocess
import re
import sys
import os

# Configuramos el archivo de destino
README_FILE = "README.md"

def run_command(command):
    """Ejecuta un comando en la terminal y devuelve el resultado."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_current_version():
    """Busca el número de versión dentro del README.md usando Regex."""
    if not os.path.exists(README_FILE):
        print(f"Error: No se encontró el archivo {README_FILE}.")
        sys.exit(1)
    
    with open(README_FILE, "r", encoding="utf-8") as file:
        content = file.read()
        # Busca un patrón tipo 1.2.3 o v1.2.3
        match = re.search(r'(\d+\.\d+\.\d+)', content)
        if match:
            return match.group(1)
        else:
            print("Error: No se encontró un número de versión (x.x.x) en el README.md")
            sys.exit(1)

def get_commits_since_last_tag():
    """Obtiene los mensajes de los commits desde el último tag."""
    latest_tag = run_command("git describe --tags --abbrev=0")
    
    if latest_tag:
        commits = run_command(f"git log {latest_tag}..HEAD --format=%s")
    else:
        commits = run_command("git log --format=%s")
        
    return commits.split('\n') if commits else []

def calculate_next_version(current_version, commits):
    """Calcula la nueva versión. Si no hay prefijos, sube 'Minor' (feat) por defecto."""
    if not commits:
        return current_version

    major, minor, patch = map(int, current_version.split('.'))
    
    bump_major = False
    bump_minor = False
    bump_patch = False

    for commit in commits:
        if "BREAKING CHANGE" in commit or re.match(r'^.*!:', commit):
            bump_major = True
        elif commit.startswith("feat:"):
            bump_minor = True
        elif commit.startswith("fix:"):
            bump_patch = True

    # Lógica de incremento
    if bump_major:
        major += 1
        minor = 0
        patch = 0
    elif bump_patch and not bump_minor:
        # Sube parche solo si hubo fix y NADA de feat
        patch += 1
    else:
        # COMPORTAMIENTO POR DEFECTO: 
        # Si hubo 'feat' o si no se detectó ningún prefijo, se asume Minor.
        minor += 1
        patch = 0

    return f"{major}.{minor}.{patch}"

def update_readme_and_git(old_version, new_version):
    """Reemplaza la versión en el README y realiza las acciones de Git."""
    with open(README_FILE, "r", encoding="utf-8") as file:
        content = file.read()

    # Reemplazamos la versión vieja por la nueva en el texto
    new_content = content.replace(old_version, new_version)

    with open(README_FILE, "w", encoding="utf-8") as file:
        file.write(new_content)
    
    # Comandos de Git
    run_command(f"git add {README_FILE}")
    run_command(f'git commit -m "chore: actualiza versión a {new_version} en README"')
    run_command(f"git tag v{new_version}")
    run_command(f"git push origin v{new_version}")

def main():
    print(f"--- Actualizando Versión en {README_FILE} ---")
    
    current_version = get_current_version()
    print(f"Versión detectada en README: {current_version}")

    commits = get_commits_since_last_tag()
    
    if not commits:
        print("No hay commits nuevos desde el último tag.")
        return

    new_version = calculate_next_version(current_version, commits)

    print(f"Nueva versión propuesta: {new_version}")
    
    confirm = input(f"¿Actualizar {README_FILE} y crear tag v{new_version}? (s/n): ")
    if confirm.lower() == 's':
        update_readme_and_git(current_version, new_version)
        print(f"¡Listo! README actualizado y Tag v{new_version} creado.")
    else:
        print("Operación cancelada.")

if __name__ == "__main__":
    main()