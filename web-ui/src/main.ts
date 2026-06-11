/**
 * @File: src/main.ts
 * @Author: Alexandre Gauvin
 * Scalable Object-Oriented 3D Model Component for high-density inventory views.
 */
import * as Three from 'three';
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export class ModelViewer {
    private scene!: Three.Scene;
    private camera!: Three.PerspectiveCamera;
    private renderer!: Three.WebGLRenderer;
    private controls!: OrbitControls;
    private meshesToAnimate: Three.Mesh[] = [];
    private canvasElement: HTMLCanvasElement;

    // Flag to track if the user has touched/moved the model with their mouse
    private isMoved: boolean = false;

    constructor(canvas: HTMLCanvasElement) {
        this.canvasElement = canvas;
        this.initThree();
        this.animate();
    }

    private initThree(): void {
        this.scene = new Three.Scene();
        this.scene.background = new Three.Color(0x1a1a1a);

        const width = this.canvasElement.clientWidth || 400;
        const height = this.canvasElement.clientHeight || 400;

        this.camera = new Three.PerspectiveCamera(75, width / height, 0.1, 1000);
        this.camera.position.set(0, 0, 5);

        this.renderer = new Three.WebGLRenderer({ canvas: this.canvasElement, antialias: true });
        this.renderer.setSize(width, height);

        // Initialize Controls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;

        // --- INTERACTION EVENT LISTENERS ---
        // 'start' fires the exact millisecond the user clicks/drags on the canvas
        this.controls.addEventListener('start', () => {
            this.isMoved = true;
        });

        const ambientLight = new Three.AmbientLight(0x404040, 2);
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
                    loadedModel.scale.set(0.1, 0.1, 0.1);

                    this.scene.add(loadedModel);
                    this.meshesToAnimate.push(loadedModel);
                    console.log(`Model ID ${modelId} successfully received from API and rendered!`);

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

        // ONLY auto-rotate if the user hasn't interacted with it yet
        if (!this.isMoved) {
            this.meshesToAnimate.forEach((mesh) => {
                mesh.rotation.y += 0.01;
            });
        }

        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
}

// --- SINGLE MODEL TESTING BLOCK ---
const canvasElement = document.querySelector('#webgl-canvas') as HTMLCanvasElement;

if (canvasElement) {
    const singleTestViewer = new ModelViewer(canvasElement);
    singleTestViewer.loadSTL(1);
}