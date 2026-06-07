// 1. Blueprint: Define what a row of data looks like. 
// This mimics exactly what your SQL schema will eventually return to Flask.
interface ModelRecord {
    id: number;
    file_name: string;
    mock_image_url: string;
    tags: string[];
}

// 2. Dictionary: Define unique colors for our category labels.
// We keep this decoupled from CSS so you can easily assign colors based on strings.
const labelColorPalette: Record<string, string> = {
    "WARHAMMER": "#e53e3e",   // Red
    "MINIATURE": "#805ad5",   // Purple
    "TERRAIN": "#dd6b20",      // Orange
    "FUNCTIONAL": "#38a169",   // Green
    "BITZ": "#3182ce",         // Blue
    "PROTOTYPE": "#718096"     // Gray fallback
};

// 3. Mock Database Content: Hardcoded rows to test our layout configuration.
const mockDatabaseRows: ModelRecord[] = [
    {
        id: 1,
        file_name: "Ultramarines_Pauldron_MkX.stl",
        mock_image_url: "https://picsum.photos/seed/marine/300/200", // Generates a random stable image
        tags: ["Warhammer", "Bitz"]
    },
    {
        id: 2,
        file_name: "Modular_Hydroponic_Tower_v4.3mf",
        mock_image_url: "https://picsum.photos/seed/tower/300/200",
        tags: ["Functional"]
    },
    {
        id: 3,
        file_name: "Gothic_Ruined_Wall_Corner.stl",
        mock_image_url: "https://picsum.photos/seed/wall/300/200",
        tags: ["Warhammer", "Terrain"]
    },
    {
        id: 4,
        file_name: "Sariel_Archangel_Sculpt_75mm.obj",
        mock_image_url: "https://picsum.photos/seed/angel/300/200",
        tags: ["Miniature"]
    }
];

// 4. Dom Link: Locate our root inventory container grid on the HTML document tree
const inventoryGrid = document.getElementById("inventory-grid");

// 5. Execution Function: Loop and assemble the elements safely
function buildInventoryUI(records: ModelRecord[]): void {
    // Edge Guard: If the HTML element isn't found, terminate execution safely
    if (!inventoryGrid) return;

    // Clear any existing boilerplate text out of the container
    inventoryGrid.innerHTML = "";

    // Iterate over every record object inside our mock dataset array
    records.forEach((record) => {
        // Create an empty, unattached <div> node in the browser's memory
        const cardElement = document.createElement("div");
        cardElement.className = "model-card";

        // Convert the record tags array into HTML string components
        // We use `.toUpperCase()` to ensure key matches our palette dictionary flawlessly
        const computedTagsHTML = record.tags.map((tag) => {
            const upperTag = tag.toUpperCase();
            const backgroundColor = labelColorPalette[upperTag] || "#4a5568"; // default gray
            
            return `<span class="label-tag" style="background-color: ${backgroundColor};">${tag}</span>`;
        }).join(""); // Glue the array of strings together into a single block of HTML text

        // Inject the structured layout layout blocks inside our temporary card node
        cardElement.innerHTML = `
            <div class="image-container">
                <img src="${record.mock_image_url}" alt="Preview of ${record.file_name}" />
            </div>
            <div class="model-title" title="${record.file_name}">${record.file_name}</div>
            <div class="tag-container">
                ${computedTagsHTML}
            </div>
        `;

        // Append the fully assembled card node directly into the live HTML document DOM grid
        inventoryGrid.appendChild(cardElement);
    });
}

// 6. Trigger: Run the assembly algorithm when the script initializes
buildInventoryUI(mockDatabaseRows);