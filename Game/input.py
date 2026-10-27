"""Keyboard and mouse input handling."""

import pygame


class Input:
    """Translate pygame events into simple game actions."""

    QUIT = "quit"
    JUMP = "jump"
    RESTART = "restart"

    def __init__(self) -> None:
        self.actions: list[str] = []

    def process(self, events: list[pygame.event.Event], game_over: bool) -> list[str]:
        """Return a list of actions for this frame."""
        self.actions = []
        for event in events:
            if event.type == pygame.QUIT:
                self.actions.append(self.QUIT)
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    self.actions.append(self.QUIT)
                elif game_over:
                    self.actions.append(self.RESTART)
                else:
                    self.actions.append(self.JUMP)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_over:
                    self.actions.append(self.RESTART)
                else:
                    self.actions.append(self.JUMP)
        return self.actions
