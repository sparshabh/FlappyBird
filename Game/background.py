"""Background drawing and ground scrolling."""

import random

import pygame

from settings import BASE_SPEED, SPRITES_DIR


class Background:
    """Draw day or night scenery and the scrolling ground strip."""

    def __init__(self) -> None:
        self.sky_day = pygame.image.load(SPRITES_DIR / "background-day.png").convert_alpha()
        self.sky_night = pygame.image.load(SPRITES_DIR / "background-night.png").convert_alpha()
        self.sky = self.sky_day
        self.base = pygame.image.load(SPRITES_DIR / "base.png").convert_alpha()
        self.base_x = 0.0
        self.moving = True
        self.pick_random_sky()

    def pick_random_sky(self) -> None:
        """Randomly choose day or night for this round."""
        self.sky = self.sky_day if random.random() < 0.6 else self.sky_night

    def update(self) -> None:
        """Scroll the ground from right to left, wrapping its repeated artwork."""
        if not self.moving:
            return
        self.base_x -= BASE_SPEED
        if self.base_x <= -self.base.get_width():
            self.base_x += self.base.get_width()

    def stop(self) -> None:
        self.moving = False

    def start(self) -> None:
        self.moving = True
        self.base_x = 0.0
        self.pick_random_sky()

    def draw_sky(self, screen: pygame.Surface) -> None:
        screen.blit(self.sky, (0, 0))

    def draw_base(self, screen: pygame.Surface) -> None:
        """Draw ground on top so pipes never visually overlap the base."""
        base_y = screen.get_height() - self.base.get_height()
        screen.blit(self.base, (round(self.base_x), base_y))
        screen.blit(self.base, (round(self.base_x) + self.base.get_width(), base_y))

    def draw(self, screen: pygame.Surface) -> None:
        self.draw_sky(screen)
        self.draw_base(screen)
