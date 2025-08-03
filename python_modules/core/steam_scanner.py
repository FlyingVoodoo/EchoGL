# python_modules/core/steam_scanner.py
import os
import re
from pathlib import Path

try:
    import winreg
except ImportError:
    winreg = None

def parse_libraryfolders_vdf(vdf_file_path):
    library_paths = []
    try:
        with open(vdf_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            matches = re.findall(r'"\d+"\s+"([^"]+)"', content)
            for path_str in matches:
                corrected_path = path_str.replace('\\\\', os.sep)
                library_paths.append(Path(corrected_path) / "steamapps")
    except Exception as e:
        print(f"Error reading file {vdf_file_path}: {e}")
    return library_paths

def find_all_potential_steamapps_folders():
    potential_steamapps_paths = set()

    main_steam_folder = None

    if os.name == 'nt':
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam") as key:
                main_steam_folder = Path(winreg.QueryValueEx(key, "InstallPath")[0])
        except (ImportError, FileNotFoundError):
            pass

        if not main_steam_folder or not main_steam_folder.is_dir():
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                    main_steam_folder = Path(winreg.QueryValueEx(key, "SteamPath")[0])
            except (ImportError, FileNotFoundError):
                pass

        if main_steam_folder and main_steam_folder.is_dir():
            steamapps_subfolder = main_steam_folder / "steamapps"
            if steamapps_subfolder.is_dir():
                print(f"Found primary Steam folder from registry: {main_steam_folder}")
                potential_steamapps_paths.add(steamapps_subfolder)

    elif os.name == 'posix':
        home = Path.home()
        linux_steam_paths = [
            home / ".steam" / "steam",
            home / ".local" / "share" / "Steam",
        ]
        for p in linux_steam_paths:
            if p.is_dir():
                steamapps_subfolder = p / "steamapps"
                if steamapps_subfolder.is_dir():
                    main_steam_folder = p
                    print(f"Found primary Steam folder (Linux): {main_steam_folder}")
                    potential_steamapps_paths.add(steamapps_subfolder)
                    break 

    all_known_main_steam_folders = set()
    for s_app_path in potential_steamapps_paths.copy():
        if s_app_path.name.lower() == "steamapps" and s_app_path.parent != s_app_path:
            all_known_main_steam_folders.add(s_app_path.parent)

    for current_main_folder in all_known_main_steam_folders:
        library_vdf_path = current_main_folder / "steamapps" / "libraryfolders.vdf"
        if library_vdf_path.is_file():
            print(f"Attempting to parse libraryfolders.vdf from: {library_vdf_path}")
            additional_library_paths = parse_libraryfolders_vdf(library_vdf_path)
            for lib_path in additional_library_paths:
                if lib_path.is_dir():
                    potential_steamapps_paths.add(lib_path)

    common_scan_paths = []
    if os.name == 'nt':
        common_scan_paths.append(Path("C:/Program Files (x86)/Steam"))
        common_scan_paths.append(Path("C:/Program Files/Steam"))
        for drive in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
            common_scan_paths.append(Path(f"{drive}:/Steam"))
            common_scan_paths.append(Path(f"{drive}:/SteamLibrary"))
            common_scan_paths.append(Path(f"{drive}:/Games/Steam"))
            common_scan_paths.append(Path(f"{drive}:/Games"))

    elif os.name == 'posix':
        common_scan_paths.append(Path("/opt/steam"))
        common_scan_paths.append(Path("/usr/share/steam"))
        common_scan_paths.append(Path("/mnt"))
        common_scan_paths.append(Path("/media"))
    elif os.name == 'darwin':
        common_scan_paths.append(Path("/Applications/Steam.app/Contents/SteamOS"))
        common_scan_paths.append(Path(Path.home() / "Library" / "Application Support" / "Steam"))

    for scan_base_path in common_scan_paths:
        if scan_base_path.is_dir():
            if scan_base_path.name.lower() == "steamapps":
                potential_steamapps_paths.add(scan_base_path)
            elif (scan_base_path / "steamapps").is_dir():
                potential_steamapps_paths.add(scan_base_path / "steamapps")
            elif scan_base_path.name.lower() == "steamlibrary" and (scan_base_path / "steamapps").is_dir():
                potential_steamapps_paths.add(scan_base_path / "steamapps")

    return list(potential_steamapps_paths)

def parse_acf_file(file_path):
    game_info = {}
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

            appid_match = re.search(r'"appid"\s+"(\d+)"', content)
            name_match = re.search(r'"name"\s+"([^"]+)"', content)
            installdir_match = re.search(r'"installdir"\s+"([^"]+)"', content)

            if appid_match:
                game_info['appid'] = appid_match.group(1)
            if name_match:
                game_info['name'] = name_match.group(1)
            if installdir_match:
                game_info['installdir'] = installdir_match.group(1)

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return game_info