import { useEffect, useRef, useState } from 'react'

type Landmark = { x: number; y: number; z?: number }

// Improved hook: connects to Python WS and performs matching + temporal smoothing
// of incoming hands to avoid flicker when hands appear/disappear or swap indices.
export default function useHandTracking() {
    const [hands, setHands] = useState<Array<{ landmarks: Array<Landmark>; handedness?: string }>>([])
    const [connected, setConnected] = useState(false)
    const [gesture, setGesture] = useState<string>('')
    const [letter, setLetter] = useState<string>('')

    // persistent refs to store smoothed hands (with stable ids) and life counters
    type SmoothedHand = { id: number; landmarks: Array<Landmark>; handedness?: string }
    const smoothedRef = useRef<Array<SmoothedHand>>([])
    const lifeRef = useRef<Array<number>>([])
    const idCounter = useRef(1)

    // helper: resample landmarks array to length L using linear interpolation
    function resampleLandmarks(src: Array<Landmark>, L: number) {
        if (!src || src.length === 0) {
            const out: Array<Landmark> = []
            for (let i = 0; i < L; i++) out.push({ x: 0.5, y: 0.5, z: 0 })
            return out
        }
        if (src.length === L) return src.slice(0, L)
        const out: Array<Landmark> = []
        const n = src.length
        for (let i = 0; i < L; i++) {
            const t = (n - 1) * (i / Math.max(1, L - 1))
            const lo = Math.floor(t)
            const hi = Math.min(n - 1, Math.ceil(t))
            const f = t - lo
            const a = src[lo]
            const b = src[hi]
            const x = a.x * (1 - f) + b.x * f
            const y = a.y * (1 - f) + b.y * f
            const z = ((a.z || 0) * (1 - f) + (b.z || 0) * f) as number
            out.push({ x, y, z })
        }
        return out
    }

    // smoothing parameters
    const landmarkAlpha = 0.22 // per-landmark EMA
    const disappearGrace = 8 // frames to keep a disappeared hand
    const matchThreshold = 0.15 // tightened: centroid distance threshold for matching
    const predictFactor = 0.45 // predictive extrapolation factor (0..1)

    useEffect(() => {
        let ws: WebSocket | null = null
        try {
            ws = new WebSocket('ws://localhost:8765')
            ws.onopen = () => {
                setConnected(true)
                console.log('HandTracking WS connected')
            }

            ws.onmessage = (ev) => {
                try {
                    const data = JSON.parse(ev.data)
                    // If server explicitly signals no detection, clear immediately
                    if (data && data.detected === false) {
                        smoothedRef.current = []
                        lifeRef.current = []
                        setHands([])
                        setGesture('')
                        setLetter('')
                        return
                    }
                    if (!data || !Array.isArray(data.hands)) return
                    if (data.hands.length === 0) {
                        smoothedRef.current = []
                        lifeRef.current = []
                        setHands([])
                        setGesture('')
                        setLetter('')
                        return
                    }

                    setGesture(typeof data.gesture === 'string' ? data.gesture : '')
                    setLetter(typeof data.letter === 'string' ? data.letter : '')

                    // debug log
                    // console.log('WS frame', data.detected, Array.isArray(data.hands) ? data.hands.length : 0)
                    // Normalize incoming hands to objects: {landmarks, handedness?}
                    const incomingRaw = data.hands as any[]
                    const incoming = incomingRaw.map((h) => {
                        if (Array.isArray(h)) return { landmarks: h as Array<Landmark>, handedness: undefined }
                        return { landmarks: h.landmarks || [], handedness: h.handedness }
                    })

                    // compute centroids for incoming hands (normalized coords)
                    const incomingCentroids = incoming.map((h) => {
                        let sx = 0,
                            sy = 0
                        for (const lm of h.landmarks) {
                            sx += lm.x
                            sy += lm.y
                        }
                        const n = Math.max(1, h.landmarks.length)
                        return { x: sx / n, y: sy / n }
                    })

                    // compute centroids for existing smoothed hands
                    const existing = smoothedRef.current
                    const existingCentroids = existing.map((h) => {
                        let sx = 0,
                            sy = 0
                        for (const lm of h.landmarks) {
                            sx += lm.x
                            sy += lm.y
                        }
                        const n = Math.max(1, h.landmarks.length)
                        return { x: sx / n, y: sy / n }
                    })

                    // matching: build stable ID mapping
                    const usedExisting = new Set<number>()
                    const newSmoothed: Array<SmoothedHand> = []

                    // 1) Try to match incoming hands by handedness -> most stable
                    for (let i = 0; i < incoming.length; i++) {
                        const inc = incoming[i]
                        if (!inc.handedness) continue
                        // find existing with same handedness
                        let found = -1
                        for (let j = 0; j < existing.length; j++) {
                            if (usedExisting.has(j)) continue
                            if (existing[j].handedness && existing[j].handedness === inc.handedness) {
                                found = j
                                break
                            }
                        }
                        if (found !== -1) {
                            usedExisting.add(found)
                            const existingHand = existing[found]
                            const L = Math.max(existingHand.landmarks.length, inc.landmarks.length)
                            const prevResampled = resampleLandmarks(existingHand.landmarks, L)
                            const curResampled = resampleLandmarks(inc.landmarks, L)
                            const smoothedHand: Array<Landmark> = []
                            for (let k = 0; k < L; k++) {
                                const prev = prevResampled[k]
                                const cur = curResampled[k]
                                const vx = cur.x - prev.x
                                const vy = cur.y - prev.y
                                const vz = (cur.z || 0) - (prev.z || 0)
                                const px = cur.x + vx * predictFactor
                                const py = cur.y + vy * predictFactor
                                const pz = (cur.z || 0) + vz * predictFactor
                                const sx = prev.x * (1 - landmarkAlpha) + px * landmarkAlpha
                                const sy = prev.y * (1 - landmarkAlpha) + py * landmarkAlpha
                                const sz = (prev.z || 0) * (1 - landmarkAlpha) + pz * landmarkAlpha
                                smoothedHand.push({ x: sx, y: sy, z: sz })
                            }
                            newSmoothed.push({ id: existingHand.id, landmarks: smoothedHand, handedness: inc.handedness })
                        }
                    }

                    // 2) For remaining incoming, match by centroid distance
                    for (let i = 0; i < incoming.length; i++) {
                        const inc = incoming[i]
                        // skip those already matched by handedness
                        const alreadyMatched = newSmoothed.some((s) => s.handedness && inc.handedness && s.handedness === inc.handedness)
                        if (alreadyMatched) continue
                        const incC = incomingCentroids[i]
                        let bestIdx = -1
                        let bestDist = Infinity
                        for (let j = 0; j < existingCentroids.length; j++) {
                            if (usedExisting.has(j)) continue
                            const exC = existingCentroids[j]
                            const dx = exC.x - incC.x
                            const dy = exC.y - incC.y
                            const d = Math.hypot(dx, dy)
                            if (d < bestDist) {
                                bestDist = d
                                bestIdx = j
                            }
                        }
                        if (bestIdx !== -1 && bestDist < matchThreshold) {
                            usedExisting.add(bestIdx)
                            const existingHand = existing[bestIdx]
                            const L = Math.max(existingHand.landmarks.length, inc.landmarks.length)
                            const prevResampled = resampleLandmarks(existingHand.landmarks, L)
                            const curResampled = resampleLandmarks(inc.landmarks, L)
                            const smoothedHand: Array<Landmark> = []
                            for (let k = 0; k < L; k++) {
                                const prev = prevResampled[k]
                                const cur = curResampled[k]
                                const vx = cur.x - prev.x
                                const vy = cur.y - prev.y
                                const vz = (cur.z || 0) - (prev.z || 0)
                                const px = cur.x + vx * predictFactor
                                const py = cur.y + vy * predictFactor
                                const pz = (cur.z || 0) + vz * predictFactor
                                const sx = prev.x * (1 - landmarkAlpha) + px * landmarkAlpha
                                const sy = prev.y * (1 - landmarkAlpha) + py * landmarkAlpha
                                const sz = (prev.z || 0) * (1 - landmarkAlpha) + pz * landmarkAlpha
                                smoothedHand.push({ x: sx, y: sy, z: sz })
                            }
                            newSmoothed.push({ id: existingHand.id, landmarks: smoothedHand, handedness: inc.handedness })
                        } else {
                            // new hand — assign new id
                            const sm = inc.landmarks.map((lm: Landmark) => ({ x: lm.x, y: lm.y, z: lm.z || 0 }))
                            const newId = idCounter.current++
                            newSmoothed.push({ id: newId, landmarks: sm, handedness: inc.handedness })
                        }
                    }

                    // handle existing hands that were not matched (fade/keep)
                    for (let j = 0; j < existing.length; j++) {
                        if (usedExisting.has(j)) continue
                        // keep the old hand for a few frames (decay life)
                        const life = (lifeRef.current[j] || disappearGrace) - 1
                        lifeRef.current[j] = life
                        if (life > 0) {
                            newSmoothed.push(existing[j])
                        }
                    }

                    // update refs: set life counters for newSmoothed hands
                    lifeRef.current = newSmoothed.map(() => disappearGrace)
                    smoothedRef.current = newSmoothed
                    setHands(newSmoothed)
                } catch (e) {
                    // ignore
                }
            }

            ws.onclose = () => {
                setConnected(false)
                console.log('HandTracking WS closed')
            }
            ws.onerror = () => {
                setConnected(false)
            }
        } catch (e) {
            console.warn('Could not connect to HandTracking WS', e)
        }

        return () => {
            if (ws && ws.readyState === WebSocket.OPEN) ws.close()
        }
    }, [])

    return { hands, connected, gesture, letter }
}
