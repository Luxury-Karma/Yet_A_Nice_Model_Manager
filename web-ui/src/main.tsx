/**
 * @File: src/main.ts
 * @Author: Alexandre Gauvin
 * Scalable Object-Oriented 3D Model Component for high-density inventory views.
 */
import * as Three from 'three';
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import {dropZone} from './moduals/dragAndDrop.ts';


// Define the exact structural typing coming from Flask's /get_stl payload
interface DBModelItem {
    id: number;
    file_name: string;
    file_path: string;
    file_size: number;
    tags: string[];
}

let currentPage: number = 0;
let maxPage : number = 0;
let maxAmount:number = 20;
let pagesInformation: DBModelItem[][]
let isShowModels: boolean = false;

export class ModelViewer {
    private scene!: Three.Scene;
    private camera!: Three.PerspectiveCamera;
    private renderer!: Three.WebGLRenderer;
    private controls!: OrbitControls;
    private meshesToAnimate: Three.Mesh[] = [];
    private canvasElement: HTMLCanvasElement;

    private isMoved: boolean = false;

    constructor(canvas: HTMLCanvasElement) {
        this.canvasElement = canvas;
        this.initThree();
        this.animate();
    }

    private initThree(): void {
        this.scene = new Three.Scene();
        // Match background color subtly to card environments
        this.scene.background = new Three.Color(0x0f0f11);

        // Dynamically measure parent sizes mapped out by style.css bounding rules
        const width = this.canvasElement.clientWidth || 260;
        const height = this.canvasElement.clientHeight || 180;

        this.camera = new Three.PerspectiveCamera(60, width / height, 0.1, 1000);
        this.camera.position.set(0, 0, 5);

        this.renderer = new Three.WebGLRenderer({ canvas: this.canvasElement, antialias: true });
        this.renderer.setSize(width, height);

        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;

        this.controls.addEventListener('start', () => {
            this.isMoved = true;
        });

        const ambientLight = new Three.AmbientLight(0x404040, 2.5);
        this.scene.add(ambientLight);

        const dirLight1 = new Three.DirectionalLight(0xffffff, 3);
        dirLight1.position.set(1, 1, 1).normalize();
        this.scene.add(dirLight1);

        const dirLight2 = new Three.DirectionalLight(0x555555, 2);
        dirLight2.position.set(-1, -1, -1).normalize();
        this.scene.add(dirLight2);
    }

// Inside your ModelViewer class in main.ts
public updateSize() {
    // 1. Get the current size from the DOM element (the canvas)
    const width = this.canvasElement.clientWidth;
    const height = this.canvasElement.clientHeight;

    // 2. Update the Three.js renderer to match the new size
    this.renderer.setSize(width, height);

    // 3. Update the camera aspect ratio so it doesn't distort
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
}

    // Inside your ModelViewer class
public resize() {
    // 1. Get the actual size of the canvas element on screen
    const width = this.canvasElement.clientWidth;
    const height = this.canvasElement.clientHeight;

    // 2. `Update` the renderer resolution
    this.renderer.setSize(width, height);

    // 3. Update the camera aspect ratio so the object isn't squashed or offset
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();

    // 4. Force a re-render
    this.renderer.render(this.scene, this.camera);
}

    public async loadSTL(modelId: number): Promise<void> {
        try {
            const response = await fetch('http://127.0.0.1:5000/fetch-model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ model_id: modelId })
            });

            if (!response.ok) {
                throw new Error(`Flask API responded with status: ${response.status}`);
            }

            const fileBlob = await response.blob();
            const blobUrl = URL.createObjectURL(fileBlob);

            const loader = new STLLoader();
            loader.load(
                blobUrl,
                (geometry: Three.BufferGeometry) => {
                    const material = new Three.MeshStandardMaterial({
                        color: 0x90caf9,
                        roughness: 0.4,
                        metalness: 0.2
                    });
                    const loadedModel = new Three.Mesh(geometry, material);

                    geometry.center();

                    // Automatically compute sizing normalization matrices
                    // so gigantic and tiny STLs fit nicely in their cards
                    geometry.computeBoundingBox();
                    const boundingBox = geometry.boundingBox;
                    if (boundingBox) {
                        const size = new Three.Vector3();
                        boundingBox.getSize(size);
                        const maxDim = Math.max(size.x, size.y, size.z);
                        const scaleFactor = 3.2 / maxDim;
                        loadedModel.scale.set(scaleFactor, scaleFactor, scaleFactor);
                    }

                    this.scene.add(loadedModel);
                    this.meshesToAnimate.push(loadedModel);

                    URL.revokeObjectURL(blobUrl);
                },
                undefined,
                (error) => console.error("Error parsing downloaded STL:", error)
            );

        } catch (error) {
            console.error("Failed to fetch model from backend API:", error);
        }
    }

    private animate = (): void => {
        requestAnimationFrame(this.animate);

        if (!this.isMoved) {
            this.meshesToAnimate.forEach((mesh) => {
                mesh.rotation.y += 0.01;
            });
        }

        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
}
// -- Settings ---
function showModels() {
    const toggler: HTMLInputElement | null= document.getElementById('mySwitch') as HTMLInputElement;
    if (!toggler){ return; } // container not found
    toggler.innerHTML = '' // empty it for reload
    // create slider
    toggler.addEventListener('change', (event:Event) => {
       const target:HTMLInputElement = event.target as HTMLInputElement;
       if (target.checked){
            isShowModels = true;
            renderCurrentPage()
       }
       else {
           isShowModels = false;
           renderCurrentPage()
       }
    });



}

function howManyModelsShown(): void {
    const dropdownSection: HTMLElement | null = document.getElementById("settings");
    if (!dropdownSection) return;
    const dropDownItem:HTMLElement | null = document.getElementById("itemsPerPage");
    if (dropDownItem) return;  // Ensure no duplicate on reloads

    // 1. Dynamically set the 'selected' attribute so the UI matches your TypeScript state
    let dropFormat : string = `
        <label for="itemsPerPage">Items per page:</label>
        <select id="itemsPerPage">
            <option value="10" ${maxAmount === 10 ? 'selected' : ''}>10</option>
            <option value="20" ${maxAmount === 20 ? 'selected' : ''}>20</option>
            <option value="30" ${maxAmount === 30 ? 'selected' : ''}>30</option>
            <option value="40" ${maxAmount === 40 ? 'selected' : ''}>40</option>
            <option value="50" ${maxAmount === 50 ? 'selected' : ''}>50</option>
            <option value="60" ${maxAmount === 60 ? 'selected' : ''}>60</option>
        </select>
    `;

    let menu: HTMLDivElement = document.createElement('div');
    menu.innerHTML = dropFormat;
    dropdownSection.appendChild(menu);

    // 2. Handle the event
    dropdownSection.addEventListener('change', async (event: Event) => {
        const target = event.target as HTMLSelectElement;

        if (target.id === 'itemsPerPage') {
            // Update the logic state
            maxAmount = parseInt(target.value, 10);

            // Force the UI to visually hold the new value
            target.value = maxAmount.toString();

            // Reset pagination
            currentPage = 0;

            // Re-fetch and re-split based on the new maxAmount
            const rawDB = await getItemsInformation();
            pagesInformation = splitDB(rawDB);
            maxPage = pagesInformation.length;

            // Render the screen
            renderCurrentPage();
        }
    });
}


// --- DB ---

async function getAllTags():Promise<string[]>{
        // 1. Fetch available tags to populate autocomplete
        const response = await fetch('http://127.0.0.1:5000/get_tags');
        const allTags: string[] = await response.json();
        return await allTags
}

function splitDB(dbSplit:DBModelItem[]):DBModelItem[][]{
    // Split STL in groups for performance
        let grouping: DBModelItem[][] = [];

        for (let i = 0; i < Math.ceil(dbSplit.length / maxAmount); i++) {
            let temp_group: any[] = []
            for (let j = 0; j < maxAmount; j++) {
                let location: number = i * maxAmount + j
                if (location > dbSplit.length) {
                    break; // ensure we're done it may not be a multiple of the max amount
                }
                temp_group.push(dbSplit[location])
            }
            grouping.push(temp_group)
        }
        return grouping
}

async function getItemsInformation():Promise<DBModelItem[]>{
        // Get the model DB from the backend
        const response: Response = await fetch('http://127.0.0.1:5000/get_stl');
        if (!response.ok) throw new Error("Could not reach DB endpoint.");

        return  await response.json();
}

// --- add models  ---

function setupQuickAdd(): void {
    const addBtn = document.getElementById('quick-add-btn') as HTMLButtonElement | null;
    if (!addBtn) return;

    addBtn.addEventListener('click', async () => {
        // 1. Ask the user for the local absolute path
        const directoryPath = window.prompt("Enter the absolute path to your STL folder (e.g., D:\\wh40k\\Shoulder_Pads):");

        // 2. Cancel if the user hits escape or leaves it blank
        if (!directoryPath || directoryPath.trim() === '') {
            return;
        }

        try {
            // 3. Send the path to your existing local Flask backend
            const response = await fetch('http://127.0.0.1:5000/find_stl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ directory_path: directoryPath.trim() })
            });

            // 4. Handle the response
            if (response.status === 202) {
                alert(`Scan initiated!\n\nThe backend is currently crawling: ${directoryPath}\nRefresh the page in a few moments to see the new models.`);
            } else {
                const errorData = await response.json();
                alert(`Failed to start scan: ${errorData.error}`);
            }
        } catch (error) {
            console.error("Error communicating with backend:", error);
            alert("Failed to connect to the backend API. Is Flask running?");
        }
    });
}

// Don't forget to call it at the bottom of your file where you initialize everything else!
setupQuickAdd();


// --- Pages ---
function renderCurrentPage(){
    buildInventory(pagesInformation[currentPage]).then(_ => {return});
    buildPaginationControls()
}

// --- PAGES control ---
function buildPaginationControls(){
    const paginationContainer:HTMLElement | null = document.getElementById('pagination-controls');

    if (!paginationContainer) return; // container not found

    paginationContainer.innerHTML = ''; // cleaning

    // Previous page
    const prevBtn:HTMLButtonElement = document.createElement("button");
    prevBtn.textContent = '◀';
    prevBtn.disabled = currentPage === 0;
    prevBtn.onclick = () => {
        if(currentPage < 0){
            return;
        }
        currentPage--;
        renderCurrentPage();
    }
    paginationContainer.appendChild(prevBtn);

    // next page
    const nextBtn:HTMLButtonElement = document.createElement("button");
    nextBtn.textContent = "▶";
    nextBtn.disabled = currentPage === (maxPage-1);
    nextBtn.onclick = () => {
        if (currentPage >= maxPage-1){
            return
        }
        currentPage++;
        renderCurrentPage();
    }
    paginationContainer.appendChild(nextBtn)

}


// --- INVENTORY ---

async function buildInventory(grouping:DBModelItem[]): Promise<void> {
    const gridContainer = document.querySelector('#inventory-grid');
    if (!gridContainer) return;
    gridContainer.innerHTML = ''; // clean
    try {


        // build visual inventory
        grouping.forEach((item) => {
            const cardNode = document.createElement('div');
            cardNode.className = 'model-card';

            let format:string = `
                <div class="image-container">
                    <canvas id="canvas-viewer-${item.id}" style="width: 100%; height: 100%; display: block;"></canvas>
                </div>
                <div class="model-title" title="${item.file_name}">${item.file_name}</div>
                <div style="font-size: 0.85rem; color: #a0aec0; margin-bottom: 1rem;">
                    Size: ${(item.file_size / (1024 * 1024)).toFixed(2)} MB
                </div>
                <div class="tag-container">
                    ${item.tags.map(tag => `<span class="label-tag" style="background-color: #2b6cb0;">${tag}</span>`).join('')}
                </div>
            `;

            if (!isShowModels){
                format = `
                <div class="model-title" title="${item.file_name}">${item.file_name}</div>
                <div style="font-size: 0.85rem; color: #a0aec0; margin-bottom: 1rem;">
                    Size: ${(item.file_size / (1024 * 1024)).toFixed(2)} MB
                </div>
                <div class="tag-container">
                    ${item.tags.map(tag => `<span class="label-tag" style="background-color: #2b6cb0;">${tag}</span>`).join('')}
                </div>
                `
            }


            cardNode.innerHTML = format;
            cardNode.addEventListener( 'click', (e: MouseEvent) => {
                const target:HTMLElement|null = e.target as HTMLElement;
                if (target.tagName.toLowerCase() === "canvas"){
                    return // Let the user control the model. Do nothing
                }
                // Todo : Add the ignore for selections as well so we can grab multiple models at once
                getModelMoreInformation(item)
                console.log(`You clicked a card: ${item.file_name}. This is good.`);
            });

            gridContainer.appendChild(cardNode);
            // Block the 3D rendering if requested. This can be highly demanding for JS to show
            if (!isShowModels){
                return;
            }

            // start the 3D rendering
            const targetCanvas = document.getElementById(`canvas-viewer-${item.id}`) as HTMLCanvasElement;
            if (targetCanvas) {
                const viewer = new ModelViewer(targetCanvas);
                viewer.loadSTL(item.id); // This requests the secure stream by its verified database ID
            }
        });

    } catch (error) {
        console.error("Failed to construct catalog list layout view grids:", error);
    }
}

async function getModelMoreInformation(item: DBModelItem): Promise<void> {
    const informationSection: HTMLElement | null = document.getElementById("moreInformation");
    if (!informationSection) return;

    informationSection.innerHTML = '';

    const format: string = `
        <dialog id="modal-dialog" class="modal">
            <div class="modal-header" style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div class="header-info">
                    <h2 id="model-title" style="margin: 0 0 0.5rem 0;">${item.file_name}</h2>
                    <div id="modal-tags" class="tag-container" style="margin-bottom: 1rem;">
                        ${item.tags.map(tag => `<span class="label-tag" style="background-color: #2b6cb0;">${tag}</span>`).join('')}
                        <button id="add-tag-btn" class="add-btn">&plus;</button>
                    </div>
                </div>
                <button id="close-modal-btn" class="close-btn">&times;</button>    
            </div>
            
            <div class="modal-body">
                <div class="modal-viewer">
                    <canvas id="modal-canvas" style="width: 100%; height: 100%; display: block;"></canvas>
                </div>
                <div class="modal-details">
                    <p><strong>Size:</strong> ${(item.file_size / (1024 * 1024)).toFixed(2)} MB</p>
                    <p><strong>Path:</strong> ${item.file_path}</p>
                </div>
            </div>
        </dialog>
    `;

    informationSection.innerHTML = format;

    const dialog = document.getElementById("modal-dialog") as HTMLDialogElement;
    const canvas = document.getElementById("modal-canvas") as HTMLCanvasElement;
    const closeBtn = document.getElementById("close-modal-btn") as HTMLButtonElement;
    const addTagBtn = document.getElementById("add-tag-btn") as HTMLButtonElement;
    const tagContainer = document.getElementById("modal-tags") as HTMLElement;

    if (!dialog || !closeBtn || !addTagBtn || !canvas) return;

    // 1. Initialize the 3D Viewer


    dialog.showModal();

    const viewer = new ModelViewer(canvas);
    viewer.loadSTL(item.id);
    viewer.updateSize();
    (viewer as any).loadSTL(item.id);

    closeBtn.onclick = () => {
        dialog.close();
        informationSection.innerHTML = '';
    };

    // 2. Setup the Tagging Logic
    addTagBtn.onclick = async () => {
        addTagBtn.style.display = 'none';

        const inputWrapper = document.createElement('span');
        inputWrapper.innerHTML = `
            <input list="tag-suggestions" id="tag-input" placeholder="Type or search tags..." 
                   style="background: #1a1a1e; color: white; border: 1px solid #4299e1; padding: 4px; border-radius: 4px;">
            <datalist id="tag-suggestions"></datalist>
        `;
        tagContainer.appendChild(inputWrapper);

        const input = document.getElementById('tag-input') as HTMLInputElement;
        const datalist = document.getElementById('tag-suggestions') as HTMLDataListElement;

        const allTags: string[] = await getAllTags();
        allTags.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t;
            datalist.appendChild(opt);
        });

        input.focus();

        input.onkeydown = async (e) => {
            if (e.key === 'Enter') {
                const tagName = input.value;
                if (!tagName) return;

                await fetch('http://127.0.0.1:5000/add_tag_to_model', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ model_id: item.id, tag_name: tagName })
                });

                item.tags.push(tagName);

                tagContainer.innerHTML = item.tags.map(tag =>
                    `<span class="label-tag" style="background-color: #2b6cb0;">${tag}</span>`
                ).join('') + `<button id="add-tag-btn" class="add-btn">&plus;</button>`;

                // Re-bind the click event to the newly created button
                document.getElementById("add-tag-btn")!.onclick = addTagBtn.onclick;
            }
        };
    };
}

pagesInformation = splitDB(await getItemsInformation()); // Give us pages informations
maxPage = pagesInformation.length; // give us how many pages present
showModels();
howManyModelsShown();
renderCurrentPage(); // show the page we are active on based on the page location and split db
// TODO: add search bar which over write anything then once empty go back to last page
dropZone();
