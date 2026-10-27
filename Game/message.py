"""Welcome artwork shown in the game window."""

import pygame

from settings import SPRITES_DIR


class Message:
    def __init__(self, center: tuple[int, int]) -> None:
        self.image = pygame.image.load(SPRITES_DIR / "message.png").convert_alpha()
        self.rect = self.image.get_rect(center=center)

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.image, self.rect)
