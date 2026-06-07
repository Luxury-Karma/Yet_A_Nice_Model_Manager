from os import walk
from os.path import splitext
from struct import unpack
from json import load
SUPPORTED_3D_FORMATS: set[str] = {
    # Mesh / printing
    "stl", "obj", "3mf", "ply",

    # CAD
    "step", "stp", "iges", "igs", "dxf", "dwg",

    # Real-time / scene
    "fbx", "gltf", "glb", "dae", "usd", "usda", "usdc", "usdz",

    # Point clouds / scan
    "xyz", "las", "laz", "e57", "pcd",

    # Legacy
    "3ds", "off", "wrl", "wrz", "amf"
}


def __is_obj(path: str) -> bool:
    """
    This is a special case, verify if it is actually a obj file
    :param path: str : file path to inspect
    :return:
    """
    with open(path, "r", errors="ignore") as f:
        for _ in range(10):
            line = f.readline()
            if line.startswith("v ") or line.startswith("f "):
                return True
    return False


def __is_gltf(path: str):
    """
     special case, this file is more like a group of files. This verify if if it a gltf
    :param path: str : file path to inspect
    :return:
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = load(f)
        return "asset" in data and "meshes" in data
    except:
        return False


def __detect_by_magic_bytes(path: str) -> str | None:
    """
    detect file type by bytes. More reliable then the file extension
    :param path: str : file path to inspect
    :return: extension if there is or None if not valid file
    """
    with open(path, "rb") as f:
        header = f.read(256)

    # STL (binary STL starts with 80-byte header then uint32)
    if len(header) > 84:
        tri_count = unpack("<I", header[80:84])[0]
        if tri_count > 0:
            return "stl"

    # 3MF (ZIP container with special structure)
    if header.startswith(b"PK"):
        if b"[Content_Types].xml" in header:
            return "3mf"
        # could also be gltf/zip-based formats

    # PLY
    if header.startswith(b"ply"):
        return "ply"

    # FBX (binary)
    if header.startswith(b"Kaydara FBX Binary"):
        return "fbx"

    # GLB (binary glTF)
    if header[:4] == b"glTF":
        return "glb"

    # USDZ (ZIP container)
    if header.startswith(b"PK") and b"USD" in header:
        return "usdz"

    # LAS point cloud
    if header[:4] == b"LASF":
        return "las"

    return None


def __detect_by_extension(path:str) -> str | None:
    """
    Basic detection base on the type format. Could be trick but is a fall back
    :param path: str : file path to inspect
    :return: extension if there is or None if not valid file
    """
    ext = splitext(path)[1].lower().strip(".")
    ext = str(ext)
    KNOWN_3D = SUPPORTED_3D_FORMATS
    if ext in KNOWN_3D:
        return ext
    return None


def __detect_3d_file_type(path: str) -> str | None:
    """
    attempt to detect 3d file type
    :param path: str : file path to inspect
    :return: extension if there is or None if not valid file
    """
    # 1. magic bytes first (most reliable)
    magic = __detect_by_magic_bytes(path)
    if magic:
        return magic

    # 2. extension guess
    ext = __detect_by_extension(path)
    if not ext:
        return None

    # 3. validation layer (IMPORTANT FIX)
    # ensures OBJ / GLTF are real, not just renamed files
    if ext == "obj":
        return "obj" if __is_obj(path) else None

    if ext in {"gltf"}:
        return "gltf" if __is_gltf(path) else None

    # everything else accepted by extension
    return ext


# TODO: next step is how we search. So are we searching the full device ( long ) a specific directory, file, or mount
# We will need to add UI for this but this should be easy and update automatically once in a while