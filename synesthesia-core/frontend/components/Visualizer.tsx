"use client";

import React, { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import * as THREE from 'three';

interface VisualizerProps {
    targetVector?: number[];
}

interface ScatterPlotProps {
    targetVector?: number[];
}

const ScatterPlot = ({ targetVector }: ScatterPlotProps) => {
    const count = 1000; // Mock 1000 points
    const mesh = useRef<THREE.InstancedMesh>(null);
    const dummy = useMemo(() => new THREE.Object3D(), []);

    const particles = useMemo(() => {
        const temp = [];
        for (let i = 0; i < count; i++) {
            const t = Math.random() * 100;
            const factor = 20 + Math.random() * 100;
            const speed = 0.01 + Math.random() / 200;
            const x = Math.random() * 100 - 50;
            const y = Math.random() * 100 - 50;
            const z = Math.random() * 100 - 50;
            temp.push({ t, factor, speed, x, y, z, mx: 0, my: 0 });
        }
        return temp;
    }, [count]);

    useFrame((state) => {
        if (!mesh.current) return;

        particles.forEach((particle, i) => {
            // Simple static position for now, but could animate
            dummy.position.set(particle.x, particle.y, particle.z);
            dummy.scale.setScalar(0.5);
            dummy.updateMatrix();
            mesh.current!.setMatrixAt(i, dummy.matrix);
        });
        mesh.current.instanceMatrix.needsUpdate = true;

        if (targetVector) {
            // Simple camera animation to target vector (mock logic for now)
            // In a real app, we'd interpolate state.camera.position to targetVector
            // For now, just log it to show we received it
            // console.log("Target Vector:", targetVector);
        }
    });

    return (
        <instancedMesh ref={mesh} args={[undefined, undefined, count]}>
            <sphereGeometry args={[0.2, 32, 32]} />
            <meshStandardMaterial color="#00ff88" emissive="#00ff88" emissiveIntensity={0.5} />
        </instancedMesh>
    );
};

export default function Visualizer({ targetVector }: VisualizerProps) {
    return (
        <div className="w-full h-[600px] bg-black rounded-lg overflow-hidden">
            <Canvas camera={{ position: [0, 0, 50], fov: 75 }}>
                <ambientLight intensity={0.5} />
                <pointLight position={[10, 10, 10]} />
                <Stars />
                <ScatterPlot targetVector={targetVector} />
                <OrbitControls />
            </Canvas>
        </div>
    );
}
