import time

try:
    import pygame

    # We'll disable pygame GUI even if pygame is present — browser will be the primary UI.
    PYGAME_AVAILABLE = False
except Exception:
    pygame = None
    PYGAME_AVAILABLE = False

import asyncio
import json
import threading

import cv2
import mediapipe as mp

from hand_tacking.gesture_stabilizer import GestureStabilizer
from hand_tacking.hand_tracking import (
    classify_gesture,
    create_hand_landmarker,
    draw_hand,
    draw_label,
    get_finger_state,
    open_camera,
)
from particles.engine import (
    MorphCloud3D,
)
from recognition.asl_translator import translate_gesture

# WebSocket broadcaster state (optional): main.py will try to broadcast normalized
# hand landmarks to ws://localhost:8765 so the browser client can consume them.
latest_landmarks = []
_landmarks_lock = threading.Lock()
latest_detected = False
latest_gesture = ""
latest_letter = ""


def start_ws_broadcaster():
    try:
        import websockets
    except Exception:
        print("websockets package not available; skipping WS broadcaster")
        return

    CLIENTS = set()

    async def _handler(ws, path=None):
        CLIENTS.add(ws)
        try:
            await ws.wait_closed()
        finally:
            CLIENTS.discard(ws)

    async def _server():
        # start server and run broadcaster loop
        async with websockets.serve(_handler, "0.0.0.0", 8765):
            print("WS broadcaster listening on ws://0.0.0.0:8765")
            while True:
                if CLIENTS:
                    with _landmarks_lock:
                        data = list(latest_landmarks)
                        detected = bool(latest_detected)
                        gesture = str(latest_gesture)
                        letter = str(latest_letter)
                    # always send the current hands list and whether anything is detected
                    await asyncio.gather(
                        *(
                            c.send(
                                json.dumps(
                                    {
                                        "hands": data,
                                        "detected": detected,
                                        "gesture": gesture,
                                        "letter": letter,
                                    }
                                )
                            )
                            for c in list(CLIENTS)
                        ),
                        return_exceptions=True,
                    )
                await asyncio.sleep(0.05)

    def _thread_target():
        try:
            asyncio.run(_server())
        except Exception:
            pass

    t = threading.Thread(target=_thread_target, daemon=True)
    t.start()


# Particle window mode: 'same' = same size as camera frame, 'small' = small floating window, 'fullscreen'
PARTICLE_WINDOW_MODE = "same"

# Map letters to RGB colors
LETTER_COLOR_MAP = {
    "A": (220, 40, 40),
    "B": (40, 80, 220),
    "L": (60, 235, 255),
    "Y": (200, 40, 200),
    "I": (40, 200, 80),
    "V": (40, 220, 200),
}

DEFAULT_PARTICLE_COLOR = (70, 235, 255)


def main() -> None:
    global latest_detected, latest_gesture, latest_letter
    landmarker = create_hand_landmarker()
    # start optional WS broadcaster so browser can receive landmarks
    start_ws_broadcaster()
    stabilizers = [GestureStabilizer() for _ in range(2)]

    # ASL cooldown state to avoid repeated letters per frame
    last_letter = ""
    last_time = 0.0
    cooldown = 1.0  # seconds
    # Particles
    particles: list = []
    max_particles = 2000
    # Pygame renderer state (separate GUI)
    pygame_inited = False
    pygame_screen = None
    pygame_clock = None
    # scaling for pygame window (camera->pygame)
    scale_x = 1.0
    scale_y = 1.0
    # persistent pseudo-3D cloud that is always visible
    morph_cloud = MorphCloud3D(count=5000, base_color=(110, 235, 255))
    # pseudo-3D camera motion
    scene_angle = 0.0

    cap = open_camera()

    if cap is None:
        print("Tidak ada kamera yang bisa dibuka")
        landmarker.close()
        return

    try:
        while True:
            success, frame = cap.read()

            if not success:
                print("Gagal membaca kamera")
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Slowly rotate the 3D scene so depth becomes visible
            scene_angle += 0.012

            # Initialize pygame window after we know frame size
            if PYGAME_AVAILABLE and not pygame_inited:
                try:
                    height, width, _ = frame.shape
                    pygame.init()

                    if PARTICLE_WINDOW_MODE == "same":
                        pw, ph = width, height
                        flags = pygame.RESIZABLE
                    elif PARTICLE_WINDOW_MODE == "small":
                        pw = min(480, width)
                        ph = int(pw * (height / max(1, width)))
                        flags = pygame.RESIZABLE
                    else:  # fullscreen
                        pw, ph = width, height
                        flags = pygame.FULLSCREEN

                    pygame_screen = pygame.display.set_mode((pw, ph), flags)
                    pygame.display.set_caption("Particles")
                    pygame_clock = pygame.time.Clock()
                    # scale factors from camera frame -> pygame window
                    scale_x = pw / width
                    scale_y = ph / height
                    pygame_inited = True
                except Exception:
                    pygame_inited = False

            results = landmarker.detect(mp_image)

            # If no hands detected, clear latest landmarks so broadcaster sends detected=False
            if not results.hand_landmarks:
                try:
                    with _landmarks_lock:
                        latest_landmarks.clear()
                        latest_detected = False
                        latest_gesture = ""
                        latest_letter = ""
                except Exception:
                    pass

            if results.hand_landmarks:
                # collect all detected hands this frame
                hands_for_broadcast = []
                frame_gestures = []
                frame_letters = []
                for hand_index, hand_landmarks in enumerate(results.hand_landmarks):
                    draw_hand(frame, hand_landmarks, show_coordinates=False)
                    try:
                        lm_list = [
                            {
                                "x": float(lm.x),
                                "y": float(lm.y),
                                "z": float(getattr(lm, "z", 0.0)),
                            }
                            for lm in hand_landmarks
                        ]
                        # determine handedness if available
                        h_label = None
                        if results.handedness and hand_index < len(results.handedness):
                            try:
                                h_label = results.handedness[hand_index][
                                    0
                                ].category_name
                            except Exception:
                                h_label = None
                        hands_for_broadcast.append(
                            {"landmarks": lm_list, "handedness": h_label}
                        )
                    except Exception:
                        pass
                # publish the per-frame hands list
                try:
                    with _landmarks_lock:
                        latest_landmarks.clear()
                        latest_landmarks.extend(hands_for_broadcast)
                        latest_detected = True
                except Exception:
                    pass

                hand_label = "Unknown"
                # Process each detected hand for labels/gestures
                for hand_index, hand_landmarks in enumerate(results.hand_landmarks):
                    if results.handedness and hand_index < len(results.handedness):
                        hand_label = results.handedness[hand_index][0].category_name

                    # The frame was flipped for a selfie view; set mirrored=False
                    # so handedness-based thumb logic matches the visible palm direction.
                    finger_states = get_finger_state(
                        hand_landmarks,
                        hand_label=hand_label,
                        mirrored=False,
                    )
                    gesture = classify_gesture(finger_states)

                    if hand_index < len(stabilizers):
                        stable_gesture = stabilizers[hand_index].update(gesture)
                    else:
                        stable_gesture = gesture

                    # Translate stable gesture to ASL letter
                    letter = translate_gesture(stable_gesture)
                    if stable_gesture:
                        frame_gestures.append(stable_gesture)
                    if letter:
                        frame_letters.append(letter)

                    # Cooldown handling
                    current_time = time.time()
                    if (
                        letter != ""
                        and letter != last_letter
                        and current_time - last_time > cooldown
                    ):
                        print(f"Huruf: {letter}")
                        last_letter = letter
                        last_time = current_time

                    # Morph the persistent 3D cloud into an L whenever L is recognized.
                    desired_cloud_mode = (
                        "L" if (stable_gesture == "L" or letter == "L") else "abstract"
                    )
                    if desired_cloud_mode != morph_cloud.mode:
                        if desired_cloud_mode == "L":
                            morph_cloud.set_letter_targets("L")
                        else:
                            morph_cloud.set_abstract_targets()

                    print(
                        f"Hand {hand_index + 1} ({hand_label}): Status jari: {finger_states}, "
                        f"Gesture: {gesture}, Stabil: {stable_gesture}"
                    )

                    draw_label(
                        frame,
                        f"{hand_label}: {stable_gesture}",
                        (20, 40 + (hand_index * 35)),
                    )

                    # Draw translated letter on screen (global, top-left)
                    cv2.putText(
                        frame,
                        f"Letter: {letter}",
                        (20, 100),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (255, 0, 0),
                        2,
                    )

                try:
                    with _landmarks_lock:
                        latest_gesture = (
                            "Y"
                            if "Y" in frame_gestures or "Y" in frame_letters
                            else (frame_gestures[0] if frame_gestures else "")
                        )
                        latest_letter = (
                            "Y"
                            if "Y" in frame_letters
                            else (frame_letters[0] if frame_letters else "")
                        )
                except Exception:
                    pass

            # If no hands detected this frame, clear latest_landmarks so browser hides skeleton quickly
            if not results.hand_landmarks:
                try:
                    with _landmarks_lock:
                        latest_landmarks.clear()
                        latest_detected = False
                        latest_gesture = ""
                        latest_letter = ""
                except Exception:
                    pass

            # Update particles (we no longer draw them onto the OpenCV frame; rendering happens in pygame)
            if particles:
                for p in particles:
                    p.update()

                # prune dead and limit total
                particles = [p for p in particles if not p.is_dead()]
                if len(particles) > max_particles:
                    particles = particles[-max_particles:]

            # update the always-on pseudo-3D morph cloud
            morph_cloud.update()

            # Also render particles into separate pygame window
            if pygame_inited and pygame_screen is not None:
                # clear overlay with transparent background
                overlay = pygame.Surface(pygame_screen.get_size(), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 0))

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        # user closed pygame window; exit app
                        raise KeyboardInterrupt()
                    if event.type == pygame.VIDEORESIZE:
                        # allow user to enlarge/shrink the particle GUI
                        pygame_screen = pygame.display.set_mode(
                            event.size,
                            pygame.RESIZABLE,
                        )
                        scale_x = event.w / width
                        scale_y = event.h / height
                        overlay = pygame.Surface(
                            pygame_screen.get_size(), pygame.SRCALPHA
                        )

                # draw particles onto overlay with alpha blending and scaling
                morph_cloud.draw(overlay)
                for p in particles:
                    try:
                        # call particle's own draw routine (supports 2D and pseudo-3D)
                        try:
                            p.draw_pygame(
                                overlay,
                                screen_w=pygame_screen.get_width(),
                                screen_h=pygame_screen.get_height(),
                                scale=900.0,
                                depth=350.0,
                                rot_x=scene_angle * 0.25,
                                rot_y=scene_angle * 0.7,
                                rot_z=scene_angle * 0.08,
                            )
                        except TypeError:
                            p.draw_pygame(overlay, scale_x=scale_x, scale_y=scale_y)
                    except Exception:
                        # fallback: draw simple circle if the particle is legacy
                        try:
                            px = int(p.x * scale_x)
                            py = int(p.y * scale_y)
                            alpha = max(0.0, 1.0 - (p.age / max(1, p.life)))
                            a = int(255 * alpha)
                            r, g, b = p.color
                            color = (int(r), int(g), int(b), a)
                            radius = max(1, int(p.size * max(scale_x, scale_y)))
                            pygame.draw.circle(overlay, color, (px, py), radius)
                        except Exception:
                            pass

                # blit overlay onto the window and present
                pygame_screen.fill((0, 0, 0))
                pygame_screen.blit(overlay, (0, 0))
                pygame.display.flip()
                if pygame_clock:
                    pygame_clock.tick(60)

            cv2.imshow("Hand Tracking", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        landmarker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
