"""Scrolling pipe obstacles for Flappy Bird."""

import random

import pygame

from settings import (
    PIPE_COLOR,
    PIPE_GAP,
    PIPE_MAX_GAP_BOTTOM,
    PIPE_MIN_GAP_Y,
    PIPE_SPEED,
    SPRITES_DIR,
)


class PipePair:
    def __init__(self, x: float, ground_y: int) -> None:
        self.image = pygame.image.load(SPRITES_DIR / f"pipe-{PIPE_COLOR}.png").convert_alpha()
        self.top_image = pygame.transform.flip(self.image, False, True)
        self.x = float(x)
        self.ground_y = ground_y
        self.gap_y = random.randint(PIPE_MIN_GAP_Y, ground_y - PIPE_MAX_GAP_BOTTOM)
        self.scored = False
        self.top_rect = pygame.Rect(0, 0, 0, 0)
        self.bottom_rect = pygame.Rect(0, 0, 0, 0)
        self._position_rects()

    def _position_rects(self) -> None:
        mid_x = round(self.x) + self.image.get_width() // 2
        self.top_rect = self.top_image.get_rect(
            midbottom=(mid_x, self.gap_y - PIPE_GAP // 2)
        )
        self.bottom_rect = self.image.get_rect(
            midtop=(mid_x, self.gap_y + PIPE_GAP // 2)
        )

    def update(self) -> None:
        self.x -= PIPE_SPEED
        self._position_rects()

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.top_image, self.top_rect)
        screen.blit(self.image, self.bottom_rect)

    def collides(self, bird_rect: pygame.Rect) -> bool:
        return bird_rect.colliderect(self.top_rect) or bird_rect.colliderect(
            self.bottom_rect
        )

    def is_offscreen(self) -> bool:
        return self.x + self.image.get_width() < 0
