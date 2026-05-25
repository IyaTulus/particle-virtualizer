import React, { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Stars } from '@react-three/drei'
import ParticleSystem from './ParticleSystem'
import HandSkeleton from './HandSkeleton'
import useHandTracking from '../hooks/useHandTracking'

export default function Scene() {
    const { hands, gesture, letter } = useHandTracking()
    const isTextMode = gesture === 'Y' || letter === 'Y'
    const isSaturnMode = gesture === 'B' || letter === 'B'
    const isCosmicMode = gesture === 'I' || letter === 'I'
    const isExplodeMode = gesture === 'A' || letter === 'A'
    const isLSpiralMode = gesture === 'L' || letter === 'L'

    return (
        <Canvas camera={{ position: [0, 0, 450], fov: 55 }} dpr={[1, 2]}>
            <color attach="background" args={[0, 0, 0]} />
            <ambientLight intensity={0.28} />
            <pointLight
                position={[-120, 90, 180]}
                intensity={isTextMode ? 1.15 : isSaturnMode ? 1.35 : isCosmicMode ? 1.25 : isLSpiralMode ? 1.22 : 0.65}
                color={isSaturnMode ? '#ffb347' : isCosmicMode ? '#ff5ecf' : isExplodeMode ? '#ff6a6a' : isLSpiralMode ? '#d56bff' : '#ff5ea8'}
            />
            <pointLight
                position={[130, -40, 210]}
                intensity={isTextMode ? 1.2 : isSaturnMode ? 1.1 : isCosmicMode ? 1.2 : isExplodeMode ? 1.28 : isLSpiralMode ? 1.18 : 0.7}
                color={isSaturnMode ? '#ffd86a' : isCosmicMode ? '#5eb9ff' : isExplodeMode ? '#6ae7ff' : isLSpiralMode ? '#ff79d6' : '#5ee8ff'}
            />
            <pointLight position={[0, 0, -220]} intensity={0.45} color="#a9a1ff" />
            <Suspense fallback={null}>
                <ParticleSystem count={40000} hands={hands} gesture={gesture} letter={letter} />
                {!isTextMode && !isSaturnMode && !isCosmicMode && !isExplodeMode && !isLSpiralMode && <HandSkeleton hands={hands} />}
            </Suspense>
            <Stars radius={900} depth={80} count={isTextMode ? 2000 : 1300} factor={isTextMode ? 2.1 : 1.35} saturation={0} fade speed={isTextMode ? 0.7 : 0.25} />
            <OrbitControls enablePan={false} enableZoom={false} autoRotate={false} />
        </Canvas>
    )
}
