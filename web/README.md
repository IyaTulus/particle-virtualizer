# Particle Visualizer (Web)

This is a starter scaffold for migrating the Python/Pygame particle visualizer to a Web-based React + Three.js project.

Quick start:

1. cd web
2. npm install
3. npm run dev

Notes:
- This scaffold contains a simple CPU-updated particle system using R3F Points and BufferGeometry.
- For production-scale particle counts (100k+), migrate steering logic to the GPU (GPUComputationRenderer / ping-pong textures).
- Hook `useHandTracking` is a stub. Integrate MediaPipe Tasks Vision (HandLandmarker) or TensorFlow.js handpose and call a gesture classifier to drive particle morph targets.

Next steps I can implement for you:
- Full MediaPipe Tasks integration in the browser
- text->point cloud conversion integrated into the particle targets
- GPU-based particle update shader pipeline
- More advanced GLSL shaders for holographic glow

Tell me which next step to generate and I'll implement it.
