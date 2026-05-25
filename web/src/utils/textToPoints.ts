export function textToPoints(text: string, sampleStep = 2, fontSize = 220) {
    // Render text to an offscreen canvas and sample bright pixels to return 2D points.
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')!
    ctx.font = `bold ${fontSize}px sans-serif`
    const metrics = ctx.measureText(text)
    const w = Math.ceil(metrics.width) + 20
    const h = fontSize + 40
    canvas.width = w
    canvas.height = h
    ctx.fillStyle = 'black'
    ctx.fillRect(0, 0, w, h)
    ctx.fillStyle = 'white'
    ctx.font = `bold ${fontSize}px sans-serif`
    ctx.fillText(text, 10, fontSize)

    const data = ctx.getImageData(0, 0, w, h).data
    const points: Array<[number, number]> = []
    for (let y = 0; y < h; y += sampleStep) {
        for (let x = 0; x < w; x += sampleStep) {
            const idx = (y * w + x) * 4
            const r = data[idx]
            const g = data[idx + 1]
            const b = data[idx + 2]
            const a = data[idx + 3]
            const intensity = Math.max(r, g, b, a)
            if (intensity > 20) {
                // center origin
                const nx = x - w / 2
                const ny = (h - y) - h / 2
                points.push([nx, ny])
            }
        }
    }
    return points
}
