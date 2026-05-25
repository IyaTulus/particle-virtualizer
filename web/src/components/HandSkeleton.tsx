import React, { useMemo, useRef, useEffect } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'

// MediaPipe Hands connectivity (pairs of indices)
const HAND_CONNECTIONS: Array<[number, number]> = [
    [0, 1],
    [1, 2],
    [2, 3],
    [3, 4],
    [0, 5],
    [5, 6],
    [6, 7],
    [7, 8],
    [5, 9],
    [9, 10],
    [10, 11],
    [11, 12],
    [9, 13],
    [13, 14],
    [14, 15],
    [15, 16],
    [13, 17],
    [17, 18],
    [18, 19],
    [19, 20],
]

type Landmark = { x: number; y: number; z?: number }
type Hand = { id?: number; landmarks: Array<Landmark>; handedness?: string }

type Props = {
    hands: Array<Hand>
}

export default function HandSkeleton({ hands }: Props) {
    const maxHands = 2
    const smoothed = useRef<Array<Array<{ x: number; y: number; z: number }>>>([])

    const lineGeometries = useMemo(() => new Array(maxHands).fill(0).map(() => new THREE.BufferGeometry()), [])
    const pointsGeometries = useMemo(() => new Array(maxHands).fill(0).map(() => new THREE.BufferGeometry()), [])

    useEffect(() => {
        for (let h = 0; h < maxHands; h++) {
            const pos = new Float32Array(21 * 3)
            pointsGeometries[h].setAttribute('position', new THREE.BufferAttribute(pos, 3))

            const connCount = HAND_CONNECTIONS.length
            const connPos = new Float32Array(connCount * 2 * 3)
            lineGeometries[h].setAttribute('position', new THREE.BufferAttribute(connPos, 3))
        }
    }, [lineGeometries, pointsGeometries])

    useEffect(() => {
        if (hands && hands.length > 0) return
        for (let h = 0; h < maxHands; h++) {
            const posAttr = pointsGeometries[h].getAttribute('position') as THREE.BufferAttribute | undefined
            const lineAttr = lineGeometries[h].getAttribute('position') as THREE.BufferAttribute | undefined
            if (posAttr) {
                posAttr.array.fill(0)
                posAttr.needsUpdate = true
            }
            if (lineAttr) {
                lineAttr.array.fill(0)
                lineAttr.needsUpdate = true
            }
        }
        smoothed.current = []
    }, [hands, lineGeometries, pointsGeometries])

    useFrame(() => {
        if (!hands || hands.length === 0) return
        // ensure deterministic ordering like ParticleSystem: sort by id when available
        const orderedHands = (hands && hands.length && typeof hands[0] === 'object' && 'id' in hands[0]) ? [...hands].sort((a: any, b: any) => (a.id || 0) - (b.id || 0)) : hands
        const alpha = 0.22
        if (smoothed.current.length !== maxHands) {
            smoothed.current = new Array(maxHands).fill(0).map(() => new Array(21).fill(0).map(() => ({ x: 0, y: 0, z: 0 })))
        }

        for (let h = 0; h < Math.min(orderedHands.length, maxHands); h++) {
            const handRaw = orderedHands[h]
            const hand = Array.isArray(handRaw) ? handRaw : handRaw.landmarks
            const handedness = !Array.isArray(handRaw) ? handRaw.handedness : undefined
            const posAttr = pointsGeometries[h].getAttribute('position') as THREE.BufferAttribute
            for (let i = 0; i < 21; i++) {
                const lm = hand[i] || hand[i % hand.length]
                const tx = (lm.x - 0.5) * 500
                const ty = ((1 - lm.y) - 0.5) * 500
                const tz = ('z' in lm) ? (lm.z * 300 - 150) : 0
                const s = smoothed.current[h][i]
                s.x = s.x * (1 - alpha) + tx * alpha
                s.y = s.y * (1 - alpha) + ty * alpha
                s.z = s.z * (1 - alpha) + tz * alpha
                posAttr.setXYZ(i, s.x, s.y, s.z)
            }
            posAttr.needsUpdate = true

            const linePos = lineGeometries[h].getAttribute('position') as THREE.BufferAttribute
            let idx = 0
            for (let i = 0; i < HAND_CONNECTIONS.length; i++) {
                const [a, b] = HAND_CONNECTIONS[i]
                const sa = smoothed.current[h][a]
                const sb = smoothed.current[h][b]
                linePos.setXYZ(idx++, sa.x, sa.y, sa.z)
                linePos.setXYZ(idx++, sb.x, sb.y, sb.z)
            }
            linePos.needsUpdate = true
        }
    })

    return (
        <group>
            {Array.from({ length: maxHands }).map((_, h) => {
                const orderedHands = (hands && hands.length && typeof hands[0] === 'object' && 'id' in hands[0]) ? [...hands].sort((a: any, b: any) => (a.id || 0) - (b.id || 0)) : hands
                const handRaw = orderedHands && orderedHands[h]
                // choose stable color by id when available, fallback to handedness
                const palette = [0x46ebff, 0xff6b6b, 0xffd166, 0x8affc1]
                let color = 0xffd166
                if (handRaw && typeof handRaw === 'object' && 'id' in handRaw) {
                    color = palette[(handRaw.id || 0) % palette.length]
                } else {
                    const handedness = handRaw && !Array.isArray(handRaw) ? handRaw.handedness : undefined
                    color = handedness === 'Left' ? 0x46ebff : handedness === 'Right' ? 0xff6b6b : 0xffd166
                }
                return (
                    <group key={h} visible={!!handRaw}>
                        <points geometry={pointsGeometries[h]}>
                            <pointsMaterial color={color} size={6} sizeAttenuation={true} depthWrite={false} />
                        </points>
                        <lineSegments geometry={lineGeometries[h]}>
                            <lineBasicMaterial color={color} linewidth={2} transparent={true} opacity={0.9} depthWrite={false} />
                        </lineSegments>
                    </group>
                )
            })}
        </group>
    )
}
