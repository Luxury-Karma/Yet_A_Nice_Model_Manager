"""
@Project: modual/file_finder.py
@Author: Alexandre Gauvin (Optimized Setup)
This module handles dynamic 3D asset format validation via signature parsing.
"""
import os
from os import walk
from tqdm import tqdm
from os.path import splitext, join, getsize, isfile, isdir
from struct import unpack
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import platform
import re
from subprocess import check_output

SUPPORTED_3D_FORMATS: set[str] = {
    "stl", "obj", "3mf", "ply", "step", "stp", "iges", "igs", "dxf", "dwg",
    "fbx", "gltf", "glb", "dae", "usd", "usda", "usdc", "usdz", "xyz", "las",
    "laz", "e57", "pcd", "3ds", "off", "wrl", "wrz", "amf"
}


def __is_obj(path: str) -> bool:
    """Verify if a file is an ASCII Wavefront OBJ by looking for structural markers."""
    try:
        with open(path, "r", errors="ignore") as f:
            for _ in range(30):  # Scan up to 30 lines in case comments are at the top
                line = f.readline().strip()
                if not line or line.startswith("#"):
                    continue
                # Real OBJ files declare vertices (v) or faces (f) immediately
                if line.startswith(("v ", "f ", "vt ", "vn ")):
                    return True
    except Exception:
        return False
    return False


def __is_gltf(path: str) -> bool:
    """Verify if a file is a valid JSON-based glTF archive."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
        return "asset" in data and ("meshes" in data or "nodes" in data)
    except Exception:
        return False


def __detect_by_magic_bytes(path: str) -> str | None:
    """
    Detect file types by reading exact byte arrays (Signatures).
    Highly resilient against altered or missing file extensions.
    """
    try:
        with open(path, "rb") as f:
            header = f.read(128)  # Grab a structured byte block
    except IOError:
        return None

    if len(header) < 4:
        return None

    # 1. Zip Container Formats (3MF, USDZ)
    if header.startswith(b"PK\x03\x04"):
        # Instead of guessing bytes, let Python natively read the lightweight archive table
        try:
            if zipfile.is_zipfile(path):
                with zipfile.ZipFile(path, 'r') as z:
                    namelist = z.namelist()
                    # 3MF Specification standard requires [Content_Types].xml and a .model file
                    if any("[Content_Types].xml" in name for name in namelist):
                        return "3mf"
                    if any(name.endswith((".usd", ".usda", ".usdc")) for name in namelist):
                        return "usdz"
        except Exception:
            pass
        return None  # It's a regular zip file, not a 3D model

    # 2. STL Verification (ASCII vs Binary)
    # Check for ASCII STL text marker first
    if header.startswith(b"solid"):
        return "stl"

    # Check for Binary STL: A true binary STL is exactly: 80 bytes (header) + 4 bytes (uint32 count) + (triangles * 50 bytes)
    try:
        file_size = getsize(path)
        if file_size >= 84:
            with open(path, "rb") as f:
                f.seek(80)
                tri_count = unpack("<I", f.read(4))[0]
            # Calculate expected file size math to verify it's a real STL
            expected_size = 80 + 4 + (tri_count * 50)
            if tri_count > 0 and file_size == expected_size:
                return "stl"
    except Exception:
        pass

    # 3. Standard 3D File Magic Byte Signatures
    if header.startswith(b"ply"):
        return "ply"
    if header.startswith(b"Kaydara FBX Binary"):
        return "fbx"
    if header.startswith(b"glTF"):
        return "glb"
    if header.startswith(b"LASF"):
        return "las"

    return None


def __detect_by_extension(path: str) -> str | None:
    """Fallback extension check if magic bytes are inconclusive."""
    ext = splitext(path)[1].lower().strip(".")
    if ext in SUPPORTED_3D_FORMATS:
        return ext
    return None


def __detect_3d_file_type(path: str) -> str | None:
    """
    Public API engine to detect 3D file formats safely.
    Uses layered verification to filter out masquerading files.
    """
    if not isfile(path):
        return None

    # Layer 1: Check signature bytes
    magic = __detect_by_magic_bytes(path)
    if magic:
        return magic

    # Layer 2: Fall back to extension evaluation
    ext = __detect_by_extension(path)
    if not ext:
        return None

    # Layer 3: Validation layer for abstract text formats
    if ext == "obj":
        return "obj" if __is_obj(path) else None

    if ext in {"gltf"}:
        return "gltf" if __is_gltf(path) else None

    return ext


def find_all_stl_file_from_directory(directory: str) -> dict[str, str]:
    """
    Recursively search this directory for 3D models using a high-performance
    concurrent ThreadPool to validate magic bytes at maximum disk I/O speeds.
    """
    discovered_assets: dict[str, str] = {}

    if not isdir(directory):
        return discovered_assets

    # STEP 1: Rapid Path Gathering
    # Collect all potential candidate paths first without opening them
    candidates = []
    for root, dirs, filenames in walk(directory):
        for filename in filenames:
            ext = splitext(filename)[1].lower().strip(".")
            if ext in SUPPORTED_3D_FORMATS:
                candidates.append(join(root, filename))

    if not candidates:
        return discovered_assets

    # STEP 2: Concurrent Header Verification
    # File I/O operations benefit from a high worker count (e.g., 32 concurrent reads)
    max_threads = min(32, (os.cpu_count() or 1) * 4)

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        # Submit all candidates to the validation engine
        future_to_path = {
            executor.submit(__detect_3d_file_type, path): path
            for path in candidates
        }

        # As files finish being read, collect valid ones immediately
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                file_type = future.result()
                if isinstance(file_type, str):
                    discovered_assets[path] = file_type
            except Exception:
                pass  # Silently ignore unreadable/locked files

    return discovered_assets



def find_all_stl_files_tqdm(directory: str) -> dict[str, str]:
    discovered_assets: dict[str, str] = {}
    # We initialize an un-bounded manual progress bar context manager
    with tqdm(unit=" files", desc="🕵️ Crawling Storage Drive", colour="cyan") as pbar:
        for root, dirs, filenames in walk(directory):
            for filename in filenames:

                # Update the progress bar counter by 1 for every file observed
                pbar.update(1)

                ext = splitext(filename)[1].lower().strip(".")
                if ext not in SUPPORTED_3D_FORMATS:
                    continue

                full_path = join(root, filename)
                try:
                    file_type = __detect_3d_file_type(full_path)
                    if isinstance(file_type, str):
                        discovered_assets[full_path] = file_type

                        # Set custom dynamic text status tags on the far right of the loading bar!
                        pbar.set_postfix({"Found Models": len(discovered_assets)})
                except (PermissionError, FileNotFoundError):
                    continue

    return discovered_assets


def get_file_model(path:str) -> tuple[str, str] | tuple[None, None]:
    """
    Verify if single file is a 3D model file.
    :param path: path to file
    :return: path and type if valid file else None, None
    """
    file_type = __detect_3d_file_type(path)

    if not isinstance(file_type, str):
        return None, None

    return path, file_type

def __get_system_drive() -> list[str]:
    """
    Retrieve all root folders in both windows and linux environment.
    :return: the list of root folder strings ('C:\\', '/media', etc.)
    """
    current_os = platform.system()
    if current_os == 'Windows':
        try:
            reg = r"([a-zA-Z]:\\)"  # Match the full root string (letter + : + \)
            drive_list = re.findall(reg, check_output('fsutil fsinfo drives', shell=True).decode())
            return [d.strip() for d in drive_list if os.path.exists(d.strip())]
        except Exception as e:
            # Fallback if execution environment lacks administrative permissions
            import string
            return [f"{letter}:\\" for letter in string.ascii_uppercase if os.path.exists(f"{letter}:\\")]

    # Linux environment fallback
    home_path = os.path.expanduser('~')
    mount_points = ["/media", "/mnt", home_path]
    return [pt for pt in mount_points if os.path.exists(pt)]


def __scan_drive_for_folder(drive: str, directory_name: str, directory_content: set[str]) -> str | None:
    """
    Scan a single drive to find a specific folder using its subfolders information.
    :param drive: What Drive to scan ( C:\\, /mnt ... )
    :param directory_name: what is the folder name
    :param directory_content: what is the folder content blueprint
    :return: path to the folder if present
    """
    for root, dirs, files in os.walk(drive):
        if os.path.basename(root) == directory_name:
            try:
                set_of_files = set(os.listdir(root))

                # FIX: Verify the frontend fingerprint is a subset of the actual drive directory
                if directory_content.issubset(set_of_files):
                    return root  # FIX: root IS the path to the folder, don't double join it!
            except Exception:
                pass
    return None


def find_specific_directory(directory_name: str, directory_content: list[str]) -> str | None:
    """
    Launch asynchronous search through every drive to locate a specific folder.
    :param directory_name: name of the folder searched
    :param directory_content: content of the folder searched
    :return: path to the folder if present
    """
    drive_list = __get_system_drive()
    directory_content_set = set(directory_content)

    with ThreadPoolExecutor(max_workers=len(drive_list)) as executor:
        future_drive = {
            executor.submit(__scan_drive_for_folder, drive, directory_name, directory_content_set)
            for drive in drive_list
        }
        for future in as_completed(future_drive):
            result = future.result()
            if result:
                return result

    return None


if __name__ == "__main__":
    print('testing the file detector...')
    all_files = find_all_stl_files_tqdm(r'D:\wh40k\Shoulder_Pads')
    for e in all_files:
        print(e)