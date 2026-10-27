"""The Pygame application window and game loop."""

from pathlib import Path

import pygame

from background import Background
from bird import Bird
from colors import WINDOW_BACKGROUND
from input import Input
from message import Message
from pipe import PipePair
from score import Score
from settings import (
    ASSETS_DIR,
    AUDIO_DIR,
    DEATH_FREEZE_DELAY_MS,
    FPS,
    GAME_HEIGHT,
    GAME_WIDTH,
    PIPE_SPAWN_OFFSET,
    PIPE_SPAWN_X,
    SOUND_VOLUME,
    SPRITES_DIR,
    TITLE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class Window:
    def __init__(self) -> None:
        pygame.init()
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self._audio_ok = True
        except pygame.error:
            self._audio_ok = False
        pygame.display.set_caption(TITLE)
        self._set_favicon()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.game_screen = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 18)

        self.background = Background()
        self.message = Message((GAME_WIDTH // 2, 156))
        self.score = Score()
        self.input = Input()
        self.ground_y = GAME_HEIGHT - self.background.base.get_height()

        # Game-over sprite
        self.gameover_img = pygame.image.load(
            SPRITES_DIR / "gameover.png"
        ).convert_alpha()

        self._load_sounds()
        self._reset()

    def _set_favicon(self) -> None:
        icon_path = ASSETS_DIR / "favicon.ico"
        try:
            pygame.display.set_icon(pygame.image.load(icon_path))
        except pygame.error:
            pass

    def _load_sounds(self) -> None:
        self.snd_wing = None
        self.snd_point = None
        self.snd_hit = None
        self.snd_die = None
        self.snd_swoosh = None
        if not getattr(self, "_audio_ok", False):
            return

        def load(name: str):
            for ext in (".ogg", ".wav"):
                path = AUDIO_DIR / f"{name}{ext}"
                if path.exists():
                    try:
                        snd = pygame.mixer.Sound(str(path))
                        snd.set_volume(SOUND_VOLUME)
                        return snd
                    except pygame.error:
                        continue
            return None

        self.snd_wing = load("wing")
        self.snd_point = load("point")
        self.snd_hit = load("hit")
        self.snd_die = load("die")
        self.snd_swoosh = load("swoosh")

    def _play(self, sound) -> None:
        if sound is not None and getattr(self, "_audio_ok", False):
            try:
                sound.play()
            except pygame.error:
                pass

    def _reset(self) -> None:
        self.bird = Bird((GAME_WIDTH // 2, 220))
        self.pipes: list[PipePair] = []
        self.score.reset()
        self.game_started = False
        self.game_over = False
        self.death_at: int | None = None  # timestamp when hit happened
        self.world_frozen = False
        self.background.start()
        self.next_pipe_at = PIPE_SPAWN_OFFSET

    def _start_or_restart(self) -> None:
        if self.game_over:
            self._reset()
            self.game_started = True
            self.bird.jump()
            self._play(self.snd_wing)
            self._play(self.snd_swoosh)
        elif not self.game_started:
            self.game_started = True
            self.bird.jump()
            self._play(self.snd_wing)
        else:
            self.bird.jump()
            self._play(self.snd_wing)

    def _end_game(self) -> None:
        if not self.game_over:
            self.game_over = True
            self.death_at = pygame.time.get_ticks()
            self.bird.kill()
            self._play(self.snd_hit)
            self._play(self.snd_die)

    def _update(self) -> None:
        now = pygame.time.get_ticks()

        # After death: bird keeps falling for a short time, then freeze world
        if self.game_over:
            if (
                self.death_at is not None
                and not self.world_frozen
                and now - self.death_at >= DEATH_FREEZE_DELAY_MS
            ):
                self.world_frozen = True
                self.background.stop()

            if not self.world_frozen:
                self.background.update()
            self.bird.update(now, True, self.ground_y)
            return

        # Always animate bird + ground on title / in play
        self.background.update()
        self.bird.update(now, self.game_started, self.ground_y)

        if not self.game_started:
            return

        # Spawn pipes
        if not self.pipes or self.pipes[-1].x < GAME_WIDTH - self.next_pipe_at:
            self.pipes.append(PipePair(PIPE_SPAWN_X, self.ground_y))

        bird_rect = self.bird.rect

        if not self.bird.alive:
            self._end_game()
            return

        for pipe in self.pipes:
            pipe.update()
            if pipe.collides(bird_rect):
                self._end_game()
                return
            if not pipe.scored and pipe.x + pipe.image.get_width() < self.bird.x:
                pipe.scored = True
                self.score.add(1)
                self._play(self.snd_point)

        self.pipes = [p for p in self.pipes if not p.is_offscreen()]

    def _draw_game_over(self) -> None:
        overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))
        self.game_screen.blit(overlay, (0, 0))

        # Real game-over sprite
        go_rect = self.gameover_img.get_rect(center=(GAME_WIDTH // 2, 160))
        self.game_screen.blit(self.gameover_img, go_rect)

        # Score + best
        self.score.draw(self.game_screen, show_high=True)

        hint = self.small_font.render(
            "Press any key or click to restart", True, (255, 255, 255)
        )
        self.game_screen.blit(
            hint, hint.get_rect(center=(GAME_WIDTH // 2, 280))
        )

    def run(self) -> None:
        running = True
        while running:
            events = pygame.event.get()
            actions = self.input.process(events, self.game_over)

            for action in actions:
                if action == Input.QUIT:
                    running = False
                elif action in (Input.JUMP, Input.RESTART):
                    self._start_or_restart()

            self._update()

            # Draw — sky, pipes, base on top, then bird/UI
            self.game_screen.fill(WINDOW_BACKGROUND)
            self.background.draw_sky(self.game_screen)
            for pipe in self.pipes:
                pipe.draw(self.game_screen)
            self.background.draw_base(self.game_screen)
            if not self.game_started:
                self.message.draw(self.game_screen)
            self.bird.draw(self.game_screen)
            if self.game_started and not self.game_over:
                self.score.draw(self.game_screen, show_high=True)
            if self.game_over:
                self._draw_game_over()

            pygame.transform.scale(
                self.game_screen, self.screen.get_size(), self.screen
            )
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
