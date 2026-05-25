import React, { useEffect, useMemo, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import * as THREE from 'three'

type Landmark = { x: number; y: number; z?: number }
type Hand = { id?: number; landmarks: Array<Landmark>; handedness?: string }

type ParticleSystemProps = { count?: number; hands: Array<Hand>; gesture?: string; letter?: string }
type Point3 = { x: number; y: number; z: number }

function hash2D(x: number, y: number) {
    const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453123
    return s - Math.floor(s)
}

function fillRectPoints(out: Point3[], cx: number, cy: number, w: number, h: number, spacing = 6, z = 0, jitter = 0.8) {
    const x1 = cx - w / 2
    const y1 = cy - h / 2
    const cols = Math.max(2, Math.ceil(w / spacing))
    const rows = Math.max(2, Math.ceil(h / spacing))

    for (let iy = 0; iy <= rows; iy++) {
        for (let ix = 0; ix <= cols; ix++) {
            const u = ix / cols
            const v = iy / rows
            const px = x1 + u * w
            const py = y1 + v * h
            const jx = (hash2D(px, py) - 0.5) * jitter
            const jy = (hash2D(py, px) - 0.5) * jitter
            out.push({ x: px + jx, y: py + jy, z })
        }
    }
}

function glyphToPoints(glyph: string, fontSize: number, sampleStep = 3): Point3[] {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')!
    const font = `900 ${fontSize}px "Arial Black", Impact, sans-serif`
    ctx.font = font
    const m = ctx.measureText(glyph)
    const w = Math.ceil(m.width) + 30
    const h = Math.ceil(fontSize * 1.3)
    canvas.width = w
    canvas.height = h
    ctx.fillStyle = '#000'
    ctx.fillRect(0, 0, w, h)
    ctx.strokeStyle = '#fff'
    ctx.font = font
    ctx.textBaseline = 'middle'
    ctx.lineWidth = Math.max(2, Math.floor(fontSize * 0.045))
    ctx.lineJoin = 'round'
    ctx.lineCap = 'round'
    ctx.strokeText(glyph, 15, h * 0.54)
    const img = ctx.getImageData(0, 0, w, h).data
    const out: Point3[] = []
    for (let y = 0; y < h; y += sampleStep) {
        for (let x = 0; x < w; x += sampleStep) {
            const idx = (y * w + x) * 4
            const r = img[idx]
            const g = img[idx + 1]
            const b = img[idx + 2]
            const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
            if (lum < 150) continue
            out.push({ x: x - w / 2, y: (h - y) - h / 2, z: 0 })
        }
    }
    return out
}

function buildPhrasePoints(): Point3[] {
    const out: Point3[] = []
    const iPts = glyphToPoints('I', 230, 3).map((p) => ({ x: p.x - 320, y: p.y, z: p.z }))
    const heartPts = glyphToPoints('❤', 220, 3).map((p) => ({ x: p.x, y: p.y + 4, z: p.z }))
    const uPts = glyphToPoints('U', 230, 3).map((p) => ({ x: p.x + 320, y: p.y, z: p.z }))
    out.push(...iPts, ...heartPts, ...uPts)
    return out
}

export default function ParticleSystem({ count = 20000, hands, gesture = '', letter = '' }: ParticleSystemProps) {
    const { size } = useThree()
    const pointsRef = useRef<THREE.Points | null>(null)
    const geomRef = useRef<THREE.BufferGeometry | null>(null)
    const blackholeModeRef = useRef(false)
    const textModeRef = useRef(false)
    const saturnModeRef = useRef(false)
    const cosmicModeRef = useRef(false)
    const explodeModeRef = useRef(false)
    const lSpiralModeRef = useRef(false)

    const positions = useMemo(() => new Float32Array(count * 3), [count])
    const targets = useMemo(() => new Float32Array(count * 3), [count])
    const speeds = useMemo(() => new Float32Array(count), [count])
    const orbitRadius = useMemo(() => new Float32Array(count), [count])
    const orbitSpeed = useMemo(() => new Float32Array(count), [count])
    const orbitPhase = useMemo(() => new Float32Array(count), [count])
    const centerDirX = useMemo(() => new Float32Array(count), [count])
    const centerDirY = useMemo(() => new Float32Array(count), [count])
    const centerDirZ = useMemo(() => new Float32Array(count), [count])
    const textDepth = useMemo(() => new Float32Array(count), [count])
    const textWave = useMemo(() => new Float32Array(count), [count])
    const textNoise = useMemo(() => new Float32Array(count), [count])
    const colors = useMemo(() => new Float32Array(count * 3), [count])

    const phrasePoints = useMemo(() => buildPhrasePoints(), [])
    const spriteTexture = useMemo(() => {
        const c = document.createElement('canvas')
        c.width = 64
        c.height = 64
        const ctx = c.getContext('2d')!
        const g = ctx.createRadialGradient(32, 32, 2, 32, 32, 30)
        g.addColorStop(0, 'rgba(255,255,255,1)')
        g.addColorStop(0.35, 'rgba(255,255,255,0.95)')
        g.addColorStop(0.7, 'rgba(255,255,255,0.28)')
        g.addColorStop(1, 'rgba(255,255,255,0)')
        ctx.fillStyle = g
        ctx.fillRect(0, 0, 64, 64)
        const tex = new THREE.CanvasTexture(c)
        tex.needsUpdate = true
        return tex
    }, [])

    useEffect(() => {
        for (let i = 0; i < count; i++) {
            positions[i * 3 + 0] = (Math.random() - 0.5) * 500
            positions[i * 3 + 1] = (Math.random() - 0.5) * 500
            positions[i * 3 + 2] = (Math.random() - 0.5) * 300

            targets[i * 3 + 0] = positions[i * 3 + 0]
            targets[i * 3 + 1] = positions[i * 3 + 1]
            targets[i * 3 + 2] = positions[i * 3 + 2]

            speeds[i] = Math.random() * 0.08 + 0.02
            orbitRadius[i] = 80 + Math.random() * 280
            orbitSpeed[i] = 0.6 + Math.random() * 1.8
            orbitPhase[i] = Math.random() * Math.PI * 2
            textDepth[i] = (Math.random() - 0.5) * 42
            textWave[i] = Math.random() * Math.PI * 2
            textNoise[i] = Math.random()

            const u = Math.random() * 2 - 1
            const a = Math.random() * Math.PI * 2
            const s = Math.sqrt(1 - u * u)
            centerDirX[i] = s * Math.cos(a)
            centerDirY[i] = s * Math.sin(a)
            centerDirZ[i] = u
            colors[i * 3 + 0] = 0.27
            colors[i * 3 + 1] = 0.92
            colors[i * 3 + 2] = 1.0
        }

        const geometry = new THREE.BufferGeometry()
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
        geomRef.current = geometry

        return () => {
            geometry.dispose()
        }
    }, [colors, count, centerDirX, centerDirY, centerDirZ, orbitPhase, orbitSpeed, orbitRadius, positions, speeds, targets, textDepth, textNoise, textWave])

    useEffect(() => {
        textModeRef.current = gesture === 'Y' || letter === 'Y'
        saturnModeRef.current = gesture === 'B' || letter === 'B'
        cosmicModeRef.current = gesture === 'I' || letter === 'I'
        explodeModeRef.current = gesture === 'A' || letter === 'A'
        lSpiralModeRef.current = gesture === 'L' || letter === 'L'

        if (!hands || hands.length === 0) {
            blackholeModeRef.current = true
            return
        }

        blackholeModeRef.current = false
        const orderedHands =
            hands.length && typeof hands[0] === 'object' && 'id' in hands[0]
                ? [...hands].sort((a: any, b: any) => (a.id || 0) - (b.id || 0))
                : hands

        const handCount = orderedHands.length
        const groupSize = Math.max(1, Math.floor(count / handCount))
        const beta = 0.18

        for (let i = 0; i < count; i++) {
            const ix = i * 3
            const groupIdx = Math.min(Math.floor(i / groupSize), handCount - 1)
            const hand = orderedHands[groupIdx]
            const lmArray = Array.isArray(hand) ? hand : hand.landmarks
            if (!lmArray || lmArray.length === 0) continue

            const lm = lmArray[i % lmArray.length]
            const wx = (lm.x - 0.5) * 500
            const wy = ((1 - lm.y) - 0.5) * 500
            const wz = 'z' in lm ? lm.z * 300 - 150 : (Math.random() - 0.5) * 200

            targets[ix] = targets[ix] * (1 - beta) + (wx + (Math.random() - 0.5) * 8) * beta
            targets[ix + 1] = targets[ix + 1] * (1 - beta) + (wy + (Math.random() - 0.5) * 8) * beta
            targets[ix + 2] = targets[ix + 2] * (1 - beta) + (wz + (Math.random() - 0.5) * 30) * beta
        }
    }, [hands, count, gesture, letter, targets])

    useFrame((state, dt) => {
        const geometry = geomRef.current
        if (!geometry) return
        const posAttr = geometry.getAttribute('position') as THREE.BufferAttribute

        const isTextMode = textModeRef.current
        const isSaturnMode = saturnModeRef.current
        const isCosmicMode = cosmicModeRef.current
        const isExplodeMode = explodeModeRef.current
        const isLSpiralMode = lSpiralModeRef.current
        const isBlackhole = !isTextMode && !isSaturnMode && !isCosmicMode && !isExplodeMode && !isLSpiralMode && blackholeModeRef.current
        const centerCount = Math.max(1, Math.floor(count * 0.18))
        const ringCount = Math.max(1, Math.floor(count * 0.24))
        const diskCount = Math.max(1, count - centerCount - ringCount)

        const phraseCount = phrasePoints.length
        const viewportScale = THREE.MathUtils.clamp(Math.min(size.width / 1920, size.height / 1080), 0.62, 1.15)
        const phraseScale = 1 + Math.sin(state.clock.elapsedTime * 0.9) * 0.006
        const phraseSpin = Math.sin(state.clock.elapsedTime * 0.1) * 0.004
        const cs = Math.cos(phraseSpin)
        const ss = Math.sin(phraseSpin)
        const colorAttr = geometry.getAttribute('color') as THREE.BufferAttribute

        for (let i = 0; i < count; i++) {
            const ix = i * 3
            let tx = targets[ix]
            let ty = targets[ix + 1]
            let tz = targets[ix + 2]

            if (isTextMode && phraseCount > 0) {
                const p = phrasePoints[i % phraseCount]
                const px = p.x * phraseScale
                const py = p.y * phraseScale
                const x = px * cs - py * ss
                const y = px * ss + py * cs
                const depthWave = Math.sin(state.clock.elapsedTime * 1.1 + textWave[i]) * 2.8
                tx = x
                ty = y * 0.84
                tz = p.z + textDepth[i] * 0.35 + depthWave + Math.sin(state.clock.elapsedTime * 0.8 + i * 0.018) * 0.7
                tx *= viewportScale
                ty *= viewportScale
            }

            if (isSaturnMode) {
                const t = state.clock.elapsedTime
                const coreCount = Math.floor(count * 0.26)
                const ringAEnd = coreCount + Math.floor(count * 0.34)
                const ringBEnd = ringAEnd + Math.floor(count * 0.24)
                const tilt = 0.52
                const ct = Math.cos(tilt)
                const st = Math.sin(tilt)

                if (i < coreCount) {
                    const u = centerDirZ[i]
                    const r = 88 * Math.cbrt(Math.max(0.0001, textNoise[i]))
                    const sw = Math.sin(t * 0.75 + orbitPhase[i]) * 1.8
                    tx = centerDirX[i] * (r + sw)
                    ty = centerDirY[i] * (r + sw)
                    tz = u * (r + sw)
                } else {
                    const ringIdx = i < ringAEnd ? i - coreCount : i - ringAEnd
                    const ringDen = i < ringAEnd ? Math.max(1, ringAEnd - coreCount) : Math.max(1, ringBEnd - ringAEnd)
                    const rrBase = i < ringAEnd ? 125 : 178
                    const rrSpan = i < ringAEnd ? 65 : 92
                    const rn = ringIdx / ringDen
                    const rr = rrBase + rn * rrSpan + Math.sin(orbitPhase[i] * 3.2 + t * 0.7) * 1.4
                    const spin = orbitPhase[i] + t * (i < ringAEnd ? 0.62 : 0.38)
                    const localX = Math.cos(spin) * rr
                    const localY = (textNoise[i] - 0.5) * (i < ringAEnd ? 5 : 7)
                    const localZ = Math.sin(spin) * rr
                    tx = localX
                    ty = localY * ct - localZ * st * 0.12
                    tz = localY * st + localZ * ct * 0.12
                }
            }

            if (isCosmicMode) {
                const t = state.clock.elapsedTime
                const swirl = i / Math.max(1, count - 1)
                const armCount = 5
                const arm = i % armCount
                const armOffset = (Math.PI * 2 * arm) / armCount
                const radius = 18 + Math.pow(swirl, 0.85) * 360
                const spin = orbitPhase[i] + t * (1.25 - swirl * 0.7)
                const spiral = spin + armOffset + swirl * 8.6
                tx = Math.cos(spiral) * radius
                ty = Math.sin(spiral) * radius * 0.58
                tz = Math.sin(spiral * 0.65 + t * 0.8) * (24 + swirl * 46)
                tx *= viewportScale
                ty *= viewportScale
                tz *= viewportScale
            }

            if (isExplodeMode) {
                const t = state.clock.elapsedTime
                const blast = 90 + (0.2 + textNoise[i] * 0.8) * 520
                const pulse = 1 + Math.sin(t * 2.6 + orbitPhase[i] * 2.2) * 0.12
                tx = centerDirX[i] * blast * pulse
                ty = centerDirY[i] * blast * pulse
                tz = centerDirZ[i] * blast * pulse + Math.sin(t * 1.7 + i * 0.02) * 16
                tx *= viewportScale
                ty *= viewportScale
                tz *= viewportScale
            }

            if (isLSpiralMode) {
                const t = state.clock.elapsedTime
                const n = i / Math.max(1, count - 1)
                const coils = 8.5
                const radius = 22 + Math.pow(n, 0.86) * 360
                const theta = n * Math.PI * coils + t * 1.3 + orbitPhase[i] * 0.45
                const ripple = Math.sin(theta * 1.55 - t * 1.4 + orbitPhase[i]) * (8 + n * 18)
                tx = Math.cos(theta) * (radius + ripple * 0.28)
                ty = Math.sin(theta) * (radius * 0.34) + Math.sin(theta * 0.8 + t) * (5 + n * 8)
                tz = Math.sin(theta * 0.72 + t * 0.9) * (18 + n * 42)
                tx *= viewportScale
                ty *= viewportScale
                tz *= viewportScale
            }

            if (isBlackhole) {
                if (i < centerCount) {
                    const pulse = 22 + Math.sin(state.clock.elapsedTime * 2.2 + orbitPhase[i]) * 4
                    const wobble = Math.sin(state.clock.elapsedTime * 3.1 + i * 0.13) * 2.5
                    const radius = pulse + wobble
                    const sphereX = centerDirX[i] * radius * 0.72
                    const sphereY = centerDirY[i] * radius * 0.78
                    const sphereZ = centerDirZ[i] * radius * 0.78
                    tx = sphereX
                    ty = sphereY * 0.72 - Math.abs(sphereX) * 0.06
                    tz = sphereZ
                } else if (i < centerCount + ringCount) {
                    const ringIndex = i - centerCount
                    const ringT = ringIndex / ringCount
                    const spin = orbitPhase[i] + state.clock.elapsedTime * (orbitSpeed[i] * 1.15)
                    const radius = 118 + Math.sin(ringT * Math.PI * 6 + state.clock.elapsedTime * 1.3) * 12
                    tx = Math.cos(spin) * radius
                    ty = Math.sin(spin) * radius * 0.42
                    tz = Math.sin(spin * 2 + ringT * Math.PI * 8) * 16 + Math.cos(ringT * Math.PI * 2) * 10
                } else {
                    const diskIndex = i - centerCount - ringCount
                    const swirl = diskIndex / diskCount
                    const armCount = 6
                    const arm = diskIndex % armCount
                    const armPhase = (Math.PI * 2 * arm) / armCount
                    const spinRate = 0.9 + (1 - swirl) * 4.8
                    const spin = orbitPhase[i] + state.clock.elapsedTime * spinRate
                    const radius = 140 + swirl * 340
                    const spiral = spin + armPhase + swirl * 8.2
                    const bulge = Math.sin((swirl * 1.8 + 0.2) * Math.PI) * 42
                    tx = Math.cos(spiral) * radius
                    ty = Math.sin(spiral) * radius * 0.33
                    tz = bulge + Math.sin(spiral * 0.8 + state.clock.elapsedTime * 1.25) * 18 - swirl * 24
                }
            }

            let x = positions[ix]
            let y = positions[ix + 1]
            let z = positions[ix + 2]
            const dx = tx - x
            const dy = ty - y
            const dz = tz - z

            const smooth = isTextMode ? 12.0 : isSaturnMode ? 10.5 : isCosmicMode ? 9.6 : isExplodeMode ? 13.0 : isLSpiralMode ? 10.8 : 8.0
            x += dx * speeds[i] * smooth * dt
            y += dy * speeds[i] * smooth * dt
            z += dz * speeds[i] * smooth * dt

            if (isTextMode) {
                x += Math.sin(state.clock.elapsedTime * 1.1 + textWave[i] * 1.7) * 0.11
                y += Math.cos(state.clock.elapsedTime * 0.95 + textWave[i] * 1.3) * 0.09
                z += Math.sin(state.clock.elapsedTime * 1.35 + textWave[i]) * 0.14

                const depthNorm = THREE.MathUtils.clamp((z + 90) / 180, 0, 1)
                const shimmer = 0.86 + Math.sin(state.clock.elapsedTime * 2.0 + textWave[i] * 0.7) * 0.14
                const noise = textNoise[i] * 0.14
                const r = (0.95 - depthNorm * 0.32 + noise) * shimmer
                const g = (0.28 + depthNorm * 0.46 + noise * 0.4) * shimmer
                const b = (0.72 + depthNorm * 0.5 + noise * 0.25) * shimmer
                colorAttr.setXYZ(i, r, g, b)

                positions[ix] = x
                positions[ix + 1] = y
                positions[ix + 2] = z
                posAttr.setXYZ(i, x, y, z)
                continue
            }

            if (isSaturnMode) {
                const radius = Math.hypot(x, y, z)
                const gold = THREE.MathUtils.clamp(1 - radius / 300, 0, 1)
                const ringGlow = 0.82 + Math.sin(state.clock.elapsedTime * 1.2 + orbitPhase[i] * 2) * 0.18
                const r = 0.95 * ringGlow
                const g = (0.5 + gold * 0.35) * ringGlow
                const b = (0.14 + gold * 0.18) * ringGlow
                colorAttr.setXYZ(i, r, g, b)
                positions[ix] = x
                positions[ix + 1] = y
                positions[ix + 2] = z
                posAttr.setXYZ(i, x, y, z)
                continue
            }

            if (isCosmicMode) {
                const t = state.clock.elapsedTime
                const rn = i / Math.max(1, count - 1)
                const hue = (0.58 + rn * 0.5 + Math.sin(t * 0.08 + orbitPhase[i]) * 0.08) % 1
                const sat = 0.78 + textNoise[i] * 0.2
                const light = 0.5 + (1 - rn) * 0.35
                const col = new THREE.Color().setHSL(hue, sat, light)
                const sparkle = 0.82 + Math.sin(t * 2.1 + orbitPhase[i] * 3.0) * 0.18
                colorAttr.setXYZ(i, col.r * sparkle, col.g * sparkle, col.b * sparkle)

                x += Math.sin(t * 0.9 + orbitPhase[i] * 2.5) * 0.1
                y += Math.cos(t * 1.05 + orbitPhase[i] * 2.2) * 0.1
                z += Math.sin(t * 1.15 + orbitPhase[i] * 1.8) * 0.12

                positions[ix] = x
                positions[ix + 1] = y
                positions[ix + 2] = z
                posAttr.setXYZ(i, x, y, z)
                continue
            }

            if (isExplodeMode) {
                const t = state.clock.elapsedTime
                const hue = (0.02 + textNoise[i] * 0.92 + Math.sin(t * 0.35 + orbitPhase[i]) * 0.06) % 1
                const sat = 0.72 + textNoise[i] * 0.22
                const light = 0.52 + Math.sin(t * 1.8 + orbitPhase[i] * 2.5) * 0.16
                const col = new THREE.Color().setHSL(hue, sat, THREE.MathUtils.clamp(light, 0.35, 0.78))
                const sparkle = 0.82 + Math.sin(t * 3.2 + orbitPhase[i] * 5.4) * 0.22
                colorAttr.setXYZ(i, col.r * sparkle, col.g * sparkle, col.b * sparkle)

                x += Math.sin(t * 1.9 + orbitPhase[i] * 2.1) * 0.34
                y += Math.cos(t * 2.1 + orbitPhase[i] * 1.8) * 0.34
                z += Math.sin(t * 1.6 + orbitPhase[i] * 2.4) * 0.4

                positions[ix] = x
                positions[ix + 1] = y
                positions[ix + 2] = z
                posAttr.setXYZ(i, x, y, z)
                continue
            }

            if (isLSpiralMode) {
                const t = state.clock.elapsedTime
                const n = i / Math.max(1, count - 1)
                const hue = (0.74 + Math.sin(t * 0.24 + n * 4.1 + orbitPhase[i] * 0.6) * 0.08 + n * 0.05) % 1
                const sat = 0.78 + textNoise[i] * 0.2
                const light = 0.36 + (1 - n) * 0.42 + Math.sin(t * 2.2 + orbitPhase[i] * 2.8) * 0.08
                const col = new THREE.Color().setHSL(hue, sat, THREE.MathUtils.clamp(light, 0.24, 0.86))
                const glow = 0.88 + Math.sin(t * 2.7 + orbitPhase[i] * 3.3) * 0.16
                colorAttr.setXYZ(i, col.r * glow, col.g * glow, col.b * glow)

                x += Math.sin(t * 1.2 + orbitPhase[i] * 1.8) * 0.08
                y += Math.cos(t * 1.0 + orbitPhase[i] * 1.5) * 0.08
                z += Math.sin(t * 1.35 + orbitPhase[i] * 2.0) * 0.11

                positions[ix] = x
                positions[ix + 1] = y
                positions[ix + 2] = z
                posAttr.setXYZ(i, x, y, z)
                continue
            }

            colorAttr.setXYZ(i, 0.27, 0.92, 1.0)

            x += Math.sin(i + state.clock.elapsedTime * 0.5) * 0.06
            y += Math.cos(i * 1.1 + state.clock.elapsedTime * 0.4) * 0.06

            positions[ix] = x
            positions[ix + 1] = y
            positions[ix + 2] = z
            posAttr.setXYZ(i, x, y, z)
        }

        posAttr.needsUpdate = true
        colorAttr.needsUpdate = true
        if (pointsRef.current && pointsRef.current.geometry !== geometry) {
            pointsRef.current.geometry = geometry
        }
    })

    return (
        <points ref={pointsRef} frustumCulled={false}>
            <pointsMaterial
                map={spriteTexture}
                vertexColors
                size={2.7}
                sizeAttenuation
                transparent
                alphaTest={0.02}
                opacity={0.96}
                depthWrite={false}
                blending={THREE.AdditiveBlending}
            />
        </points>
    )
}
