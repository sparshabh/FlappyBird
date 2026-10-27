"""Bird physics, flap animation, rotation and idle bob."""

import math

import pygame

from settings import (
    BIRD_COLOR,
    BIRD_FLAP_MS,
    BIRD_IDLE_BOB_AMPLITUDE,
    BIRD_IDLE_BOB_SPEED,
    BIRD_MAX_DOWN_ANGLE,
    BIRD_MAX_UP_ANGLE,
    BIRD_ROTATION_SMOOTH,
    GRAVITY,
    JUMP_VELOCITY,
    MAX_FALL_SPEED,
    SPRITES_DIR,
)


class Bird:
    def __init__(self, center: tuple[int, int]) -> None:
        prefix = f"{BIRD_COLOR}bird"
        self.frames = [
            pygame.image.load(SPRITES_DIR / name).convert_alpha()
            for name in (
                f"{prefix}-upflap.png",
                f"{prefix}-midflap.png",
                f"{prefix}-downflap.png",
            )
        ]
        self.base_x, self.base_y = float(center[0]), float(center[1])
        self.x, self.y = self.base_x, self.base_y
        self.velocity = 0.0
        self.frame = 0
        self.next_frame_at = 0
        self.angle = 0.0
        self.alive = True
        self._image = self.frames[0]
        self._bob_phase = 0.0

    def jump(self) -> None:
        """Give the bird an upward flap impulse."""
        if self.alive:
            self.velocity = JUMP_VELOCITY

    def update(self, now: int, game_started: bool, floor_y: int) -> None:
        """Animate wings, idle bob, gravity, rotate, and handle floor."""
        # Always animate flaps
        if now >= self.next_frame_at:
            self.frame = (self.frame + 1) % len(self.frames)
            self.next_frame_at = now + BIRD_FLAP_MS

        if not game_started:
            # Gentle up/down bob on title screen
            self._bob_phase = now * BIRD_IDLE_BOB_SPEED
            self.y = self.base_y + math.sin(self._bob_phase) * BIRD_IDLE_BOB_AMPLITUDE
            self.x = self.base_x
            self._image = self.frames[self.frame]
            return

        # Physics
        if self.alive:
            self.velocity = min(self.velocity + GRAVITY, MAX_FALL_SPEED)
        else:
            self.velocity = min(self.velocity + GRAVITY * 1.15, MAX_FALL_SPEED + 2)

        self.y += self.velocity

        half_height = self.frames[self.frame].get_height() // 2
        if self.y < half_height:
            self.y = half_height
            self.velocity = 0.0

        floor_limit = floor_y - half_height
        if self.y >= floor_limit:
            self.y = floor_limit
            self.velocity = 0.0
            self.alive = False

        # Smooth rotation from velocity
        target_angle = max(
            BIRD_MAX_DOWN_ANGLE,
            min(BIRD_MAX_UP_ANGLE, -self.velocity * 3.8),
        )
        self.angle += (target_angle - self.angle) * BIRD_ROTATION_SMOOTH
        self._image = pygame.transform.rotozoom(self.frames[self.frame], self.angle, 1.0)

    def kill(self) -> None:
        self.alive = False

    @property
    def rect(self) -> pygame.Rect:
        """Slightly tighter hitbox than the full sprite."""
        img = self.frames[self.frame]
        r = img.get_rect(center=(round(self.x), round(self.y)))
        return r.inflate(-6, -4)

    def draw(self, screen: pygame.Surface) -> None:
        rect = self._image.get_rect(center=(round(self.x), round(self.y)))
        screen.blit(self._image, rect)
