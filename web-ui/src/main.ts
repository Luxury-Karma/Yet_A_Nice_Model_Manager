/**
 * @File: src/main.ts
 * @Author: Alexandre Gauvin
 * Scalable Object-Oriented 3D Model Component for high-density inventory views.
 */
import * as Three from 'three';
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

// Define the exact structural typing coming from Flask's /get_stl payload
interface DBModelItem {
    id: number;
    file_name: string;
    file_path: string;
    file_size: number;
    tags: string[];
}

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

// --- DYNAMIC INVENTORY CONSTRUCTOR ---
async function buildInventoryGrid(): Promise<void> {
    const gridContainer = document.querySelector('#inventory-grid');
    if (!gridContainer) return;

    try {
        // Step 1: Grab the untampered database layout definition list
        const response = await fetch('http://127.0.0.1:5000/get_stl');
        if (!response.ok) throw new Error("Could not reach DB endpoint.");

        const stlItems: DBModelItem[] = await response.json();

        // Step 2: Draw the layout elements instantly using style.css rules
        stlItems.forEach((item) => {
            const cardNode = document.createElement('div');
            cardNode.className = 'model-card';

            cardNode.innerHTML = `
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

            gridContainer.appendChild(cardNode);

            // Step 3: Trigger the independent 3D renderer per card to fetch its verified binary
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
// Attach listener lifecycle initializers
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildInventoryGrid);
} else {
    buildInventoryGrid();
}