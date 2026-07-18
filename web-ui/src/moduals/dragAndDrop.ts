export type FileNode = { type: 'file'; file: File; path: string };
export type DirectoryNode = { type: 'directory'; name: string; path: string; children: (FileNode | DirectoryNode)[] };
export type DropSystemNode = FileNode | DirectoryNode;

export async function dropZone(): Promise<void> {
    const dropArea = document.getElementById("inventory-grid");

    // 1. THE FIREFOX FIX: Prevent the browser from opening dropped files anywhere
    window.addEventListener('dragover', (event) => {
        event.preventDefault();
    });
    window.addEventListener('drop', (event) => {
        event.preventDefault();
    });

    // 2. Your specific drop area logic
    dropArea?.addEventListener('dragenter', (event) => {
        event.preventDefault();
        dropArea.classList.add('highlight');
    });

    dropArea?.addEventListener('dragleave', (event) => {
        event.preventDefault();
        dropArea.classList.remove('highlight');
    });

    dropArea?.addEventListener('dragover', (event) => {
        event.preventDefault();
    });

    dropArea?.addEventListener('drop', async (event) => {
        event.preventDefault();
        // Stop the event from bubbling up just to be safe
        event.stopPropagation();
        dropArea.classList.remove('highlight');

        const items = event.dataTransfer?.items;
        if (!items) return;

        for (let i = 0; i < items.length; i++) {
            const item = items[i];

            if (item.kind === 'file') {
                const entry = item.webkitGetAsEntry();

                if (entry) {
                    if (entry.isDirectory) {
                        addDirectory(entry as FileSystemDirectoryEntry)
                    } else if (entry.isFile) {
                        addFile();
                    }
                }
            }
        }
    });
}


async function addFile():Promise<boolean>{
    console.log('File: make a api call to just add a specific file')
    return true;
}


async function addDirectory(entry:FileSystemDirectoryEntry):Promise<boolean>{
    const dirReader = (entry as FileSystemDirectoryEntry).createReader();

                // 1. Wrap the callback in a Promise to extract the list
    const nameList = await new Promise<string[]>((resolve, reject) => {
        dirReader.readEntries(
            (entries) => {
                // Map the entries to an array of strings
                resolve(entries.map(child => child.name));
                },
            (error) => reject(error)
        );
    });
    await fetch('http://127.0.0.1:5000/locate_directory', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ folder_name: entry?.name, fingerprint:nameList})
                });
    
    return true
}