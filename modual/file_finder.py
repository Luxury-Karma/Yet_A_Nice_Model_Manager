"""
@Project: modual/file_finder.py
@Author: Alexandre Gauvin (Optimized Setup)
This module handles dynamic 3D asset format validation via signature parsing.
"""
import os
from os.path import splitext
from struct import unpack
import json
import zipfile

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
        file_size = os.path.getsize(path)
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


def detect_3d_file_type(path: str) -> str | None:
    """
    Public API engine to detect 3D file formats safely.
    Uses layered verification to filter out masquerading files.
    """
    if not os.path.isfile(path):
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

# TODO: next step is how we search. So are we searching the full device ( long ) a specific directory, file, or mount
# We will need to add UI for this but this should be easy and update automatically once in a while