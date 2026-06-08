/**
 * @File: src/main.ts
 * @Author: Alexandre Gauvin
 * Core frontend asset interaction loop for managing and dropping 3D assets.
 */

interface ModelRecord {
    id: number;
    file_name: string;
    mock_image_url: string;
    tags: string[];
}

const labelColorPalette: Record<string, string> = {
    // Technical Format Extensions
    "STL": "#3182ce",          // Blue
    "3MF": "#dd6b20",          // Orange
    "OBJ": "#38a169",          // Green
    "FBX": "#805ad5",          // Purple
    "GLTF": "#e53e3e",         // Red

    // Core Category Fallbacks
    "MINIATURE": "#718096",
    "FUNCTIONAL": "#4a5568"
};

const inventoryGrid = document.getElementById("inventory-grid");

// Track our polling interval globally at the top level so it doesn't lose state
let scanPollingInterval: number | null = null;

// --- 1. LIVE DATA BACKEND FETCH ENGINE ---
async function fetchInventoryFromDatabase(): Promise<void> {
    if (!inventoryGrid) return;
    try {
        // Points to Flask via your Vite proxy setup
        const response = await fetch('/api/get_stl');
        if (!response.ok) throw new Error("Database fetch failed");

        const liveRows: ModelRecord[] = await response.json();
        buildInventoryUI(liveRows);
    } catch (err) {
        console.error("Error updating UI grid layout:", err);
        inventoryGrid.innerHTML = `<div style="color: #e53e3e; padding: 2rem;">❌ Server offline. Run STL_API.py first.</div>`;
    }
}

// --- 2. DRAG AND DROP DIRECTORY INGESTION LAYERS ---
function initializeDragAndDropZone(): void {
    const dropZone = document.body; // Allows dropping folders anywhere across the main window layout
    if (!dropZone) return;

    // Prevent default browser behavior (opening/downloading files when dropped)
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => e.preventDefault(), false);
    });

    // Provide visual style shifts when dragging files over the window context
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            if (inventoryGrid) inventoryGrid.style.borderColor = "#805ad5"; // Highlight borders purple
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            if (inventoryGrid) inventoryGrid.style.borderColor = "transparent"; // Reset borders
        }, false);
    });

    dropZone.addEventListener('drop', async (e: DragEvent) => {
        const dt = e.dataTransfer;
        if (!dt) return;

        const items = dt.items;
        if (!items || items.length === 0) return;

        // Extract filesystem interface item entry
        const entry = items[0].webkitGetAsEntry();

        if (entry && entry.isDirectory) {
            const dirEntry = entry as FileSystemDirectoryEntry;
            const dirReader = dirEntry.createReader();

            showScanStatusBanner(`🔍 Analyzing folder structure for "${dirEntry.name}"...`);

            // Read the contents of the dropped directory to gather the signature
            dirReader.readEntries(async (entries) => {
                // Collect up to 5 filenames from the root of the dropped folder as a fingerprint
                const fileFingerprint = entries
                    .filter(item => item.isFile)
                    .slice(0, 5)
                    .map(item => item.name);

                try {
                    // Send the folder name and its blueprint to your backend picker engine
                    const response = await fetch('/api/locate_directory', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            folder_name: dirEntry.name,
                            fingerprint: fileFingerprint
                        })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        showScanStatusBanner(`🚀 Match found! Scanning background path: ${data.resolved_path}`);

                        // Start auto-polling the database every 3 seconds to pull in new models live
                        if (!scanPollingInterval) {
                            let checks = 0;
                            scanPollingInterval = window.setInterval(async () => {
                                await fetchInventoryFromDatabase();
                                checks++;

                                // Automatically turn off polling after 2 minutes (40 checks) to save resources
                                if (checks > 40 && scanPollingInterval) {
                                    clearInterval(scanPollingInterval);
                                    scanPollingInterval = null;
                                    hideScanStatusBanner();
                                }
                            }, 3000);
                        }
                    } else {
                        showScanStatusBanner(`❌ Matching failed: ${data.error}`, true);
                    }
                } catch (err) {
                    showScanStatusBanner(`❌ Connection error: ${err}`, true);
                }
            });
        }
    });
}

// --- 3. DOM ASSEMBLY ENGINE ---
function buildInventoryUI(records: ModelRecord[]): void {
    if (!inventoryGrid) return;
    inventoryGrid.innerHTML = "";

    if (records.length === 0) {
        inventoryGrid.innerHTML = `<div style="color: #a0aec0; padding: 2rem; width: 100%; text-align: center;">📭 Database is empty. Drag and drop a folder to seed models.</div>`;
        return;
    }

    records.forEach((record) => {
        const cardElement = document.createElement("div");
        cardElement.className = "model-card";

        // Dynamically process extension format array groupings
        const computedTagsHTML = record.tags.map((tag) => {
            const upperTag = tag.toUpperCase();
            const backgroundColor = labelColorPalette[upperTag] || "#4a5568"; // Fallback grey if color unspecified
            return `<span class="label-tag" style="background-color: ${backgroundColor};">${tag}</span>`;
        }).join("");

        cardElement.innerHTML = `
            <div class="image-container">
                <img src="${record.mock_image_url}" alt="Preview of ${record.file_name}" />
            </div>
            <div class="model-title" title="${record.file_name}">${record.file_name}</div>
            <div class="tag-container">
                ${computedTagsHTML}
            </div>
        `;

        inventoryGrid.appendChild(cardElement);
    });
}

// --- 4. STATUS BANNER RENDERING SYSTEM ---
function showScanStatusBanner(message: string, isError: boolean = false): void {
    let banner = document.getElementById("scan-status-banner");

    // If the banner doesn't exist yet, create it dynamically on the fly
    if (!banner) {
        banner = document.createElement("div");
        banner.id = "scan-status-banner";
        Object.assign(banner.style, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            backgroundColor: isError ? '#e53e3e' : '#2d3748',
            color: '#fff',
            padding: '12px 24px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            fontFamily: 'sans-serif',
            fontSize: '14px',
            zIndex: '9999',
            transition: 'all 0.3s ease',
            opacity: '0'
        });
        document.body.appendChild(banner);
    }

    // Update contents and fade into view
    banner.textContent = message;
    banner.style.backgroundColor = isError ? '#e53e3e' : '#1a202c';
    banner.style.borderLeft = isError ? '4px solid #fff' : '4px solid #3182ce';
    banner.style.opacity = '1';

    // Auto-fade status update messages after 7 seconds if it's not an error
    if (!isError) {
        setTimeout(() => {
            if (banner) banner.style.opacity = '0';
        }, 7000);
    }
}

function hideScanStatusBanner(): void {
    const banner = document.getElementById("scan-status-banner");
    if (banner) banner.style.opacity = '0';
}

// --- 5. SYSTEM BOOTSTRAP CONTROL INITIALIZATION ---
initializeDragAndDropZone();
fetchInventoryFromDatabase();