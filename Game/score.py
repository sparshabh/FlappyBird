"""Score display using the supplied pixel-art number sprites."""

import pygame

from settings import HIGH_SCORE_Y, HIGHSCORE_PATH, SCORE_Y, SPRITES_DIR


class Score:
    def __init__(self) -> None:
        self.digits = [
            pygame.image.load(SPRITES_DIR / f"{n}.png").convert_alpha() for n in range(10)
        ]
        self.value = 0
        self.high_score = self._load_high_score()

    def _load_high_score(self) -> int:
        try:
            if HIGHSCORE_PATH.exists():
                return max(0, int(HIGHSCORE_PATH.read_text().strip()))
        except (ValueError, OSError):
            pass
        return 0

    def _save_high_score(self) -> None:
        try:
            HIGHSCORE_PATH.write_text(str(self.high_score))
        except OSError:
            pass

    def reset(self) -> None:
        self.value = 0

    def add(self, points: int = 1) -> None:
        self.value += points
        if self.value > self.high_score:
            self.high_score = self.value
            self._save_high_score()

    def draw(self, screen: pygame.Surface, show_high: bool = False) -> None:
        self._draw_number(screen, self.value, y=SCORE_Y)
        if show_high and self.high_score > 0:
            self._draw_number(screen, self.high_score, y=HIGH_SCORE_Y, scale=0.7)

    def _draw_number(
        self, screen: pygame.Surface, number: int, y: int, scale: float = 1.0
    ) -> None:
        text = str(number)
        images = [self.digits[int(char)] for char in text]
        if scale != 1.0:
            images = [
                pygame.transform.smoothscale(
                    img,
                    (
                        max(1, int(img.get_width() * scale)),
                        max(1, int(img.get_height() * scale)),
                    ),
                )
                for img in images
            ]
        gap = max(1, int(2 * scale))
        total_width = sum(img.get_width() for img in images) + gap * (len(images) - 1)
        x = (screen.get_width() - total_width) // 2
        for image in images:
            screen.blit(image, (x, y))
            x += image.get_width() + gap
