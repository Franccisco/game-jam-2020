import arcade

from .pauseview import PauseView
from ..gameconstants import (
    GAME_PATH,
    CHARACTER_SCALING,
    SCREEN_WIDTH,
    OVER_FLOOR_POSITION,
)


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        # Lists that will keep track of the sprites
        self.player_list = None

        # Character sprites
        self.robot_sprite = None
        self.female_sprite = None
        self.male_sprite = None

    def on_show(self) -> None:
        arcade.set_background_color(arcade.color.WHITE)

    def on_draw(self) -> None:
        arcade.start_render()

        self.player_list.draw()

    def setup(self) -> None:
        self.player_list = arcade.SpriteList()

        characters_source = f"{GAME_PATH}/assets/characters"

        self.robot_sprite = arcade.Sprite(
            f"{characters_source}/robot/robot_idle.png", CHARACTER_SCALING
        )
        self.robot_sprite.center_x = 0.1 * SCREEN_WIDTH
        self.robot_sprite.center_y = OVER_FLOOR_POSITION
        self.player_list.append(self.robot_sprite)

        self.female_sprite = arcade.Sprite(
            f"{characters_source}/female/female_idle.png", CHARACTER_SCALING
        )
        self.female_sprite.center_x = 0.2 * SCREEN_WIDTH
        self.female_sprite.center_y = OVER_FLOOR_POSITION
        self.player_list.append(self.female_sprite)

        self.male_sprite = arcade.Sprite(
            f"{characters_source}/male/male_idle.png", CHARACTER_SCALING
        )
        self.male_sprite.center_x = 0.3 * SCREEN_WIDTH
        self.male_sprite.center_y = OVER_FLOOR_POSITION
        self.player_list.append(self.male_sprite)

    def pause_game(self) -> None:
        """Switch to a Pause view."""
        pause = PauseView(self)
        self.window.show_view(pause)

    def on_key_press(self, key: int, modifiers: int) -> None:
        """Catch key events."""
        if key == arcade.key.ESCAPE:
            self.pause_game()
