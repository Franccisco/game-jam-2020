import arcade
import math

from .pauseview import PauseView

PLAYER_MOVEMENT_SPEED = 5
GRAVITY = 1
PLAYER_JUMP_SPEED = 20

LEFT_VIEWPORT_MARGIN = 250
RIGHT_VIEWPORT_MARGIN = 250
BOTTOM_VIEWPORT_MARGIN = 50
TOP_VIEWPORT_MARGIN = 100

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

BULLET_SPEED = 35
SPRITE_SCALING_LASER = 0.3


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = None

        self.wall_list = None
        self.player_list = None
        self.player_sprite = None
        self.physics_engine = None

        self.view_bottom = 0
        self.view_left = 0

        self.gunshot_sound = arcade.load_sound("data/gunshot.mp3")
        self.footstep = arcade.load_sound("data/footsteps.ogg")

        self.life = 0
        self.bullet_list = None

    def on_show(self) -> None:
        pass

    def on_draw(self) -> None:
        arcade.start_render()

        arcade.draw_lrwh_rectangle_textured(0, 0, 1000, 900, self.background)

        self.wall_list.draw()
        self.player_list.draw()
        self.bullet_list.draw()

        # Draw our score on the screen, scrolling it with the viewport
        score_text = f"Life left: {self.life}%"
        arcade.draw_text(
            score_text,
            10 + self.view_left,
            570 + self.view_bottom,
            arcade.csscolor.BLUE,
            11,
        )

    def setup(self) -> None:
        self.background = arcade.load_texture("data/background1.png")

        self.wall_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()

        image_source = ":resources:images/animated_characters\
/female_adventurer/femaleAdventurer_idle.png"
        self.player_sprite = arcade.Sprite(image_source, 0.5)
        self.player_sprite.center_x = 50
        self.player_sprite.center_y = 300
        self.player_list.append(self.player_sprite)

        # layout build
        build = Build(image_x="data/steel.png", scale=0.1, image_y="data/steelV.png")
        build.lay((0, 720, 15), "y", 0, scale=0.1)
        build.lay((0, 50, 15), "x", 200, scale=0.1)
        build.lay((202, 260, 15), "y", 56, scale=0.1)
        build.lay((0, 1000, 15), "x", 10)

        self.wall_list = build.submit()

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, self.wall_list, GRAVITY
        )

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key == arcade.key.UP or key == arcade.key.W:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        if key == arcade.key.ESCAPE:
            self.pause_game()

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = 0

    def pause_game(self) -> None:
        """Switch to a Pause view."""
        pause = PauseView(self)
        self.window.show_view(pause)

    def on_mouse_press(self, x, y, button, modifiers):
        """
        Called whenever the mouse moves.
        """
        # Create a bullet
        bullet = arcade.Sprite(
            ":resources:images/space_shooter/laserBlue01.png", SPRITE_SCALING_LASER
        )

        # Position the bullet at the player's current location
        start_x = self.player_sprite.center_x
        start_y = self.player_sprite.center_y
        bullet.center_x = start_x
        bullet.center_y = start_y

        # Get from the mouse the destination location for the bullet
        # IMPORTANT! If you have a scrolling screen, you will also need
        # to add in self.view_bottom and self.view_left.
        dest_x = x
        dest_y = y

        # Do math to calculate how to get the bullet to the destination.
        # Calculation the angle in radians between the start points
        # and end points. This is the angle the bullet will travel.
        x_diff = dest_x - start_x
        y_diff = dest_y - start_y
        angle = math.atan2(y_diff, x_diff)

        # Angle the bullet sprite so it doesn't look like it is flying
        # sideways.
        bullet.angle = math.degrees(angle)

        # Taking into account the angle, calculate our change_x
        # and change_y. Velocity is how fast the bullet travels.
        bullet.change_x = math.cos(angle) * BULLET_SPEED
        bullet.change_y = math.sin(angle) * BULLET_SPEED

        # Add the bullet to the appropriate lists
        self.bullet_list.append(bullet)

    def on_update(self, delta_time):
        """ Movement and game logic """

        # Move the player with the physics engine
        self.physics_engine.update()
        self.bullet_list.update()

        # --- Manage Scrolling ---

        # Track if we need to change the viewport

        changed = False
        if self.player_sprite.change_x and not self.player_sprite.change_y:
            arcade.play_sound(self.footstep)

        # Scroll left
        left_boundary = self.view_left + LEFT_VIEWPORT_MARGIN
        if self.player_sprite.left < left_boundary:
            self.view_left -= left_boundary - self.player_sprite.left
            changed = True

        # Scroll right
        right_boundary = self.view_left + SCREEN_WIDTH - RIGHT_VIEWPORT_MARGIN
        if self.player_sprite.right > right_boundary:
            self.view_left += self.player_sprite.right - right_boundary
            changed = True

        # Scroll up
        top_boundary = self.view_bottom + SCREEN_HEIGHT - TOP_VIEWPORT_MARGIN
        if self.player_sprite.top > top_boundary:
            self.view_bottom += self.player_sprite.top - top_boundary
            changed = True

        # Scroll down
        bottom_boundary = self.view_bottom + BOTTOM_VIEWPORT_MARGIN
        if self.player_sprite.bottom < bottom_boundary:
            self.view_bottom -= bottom_boundary - self.player_sprite.bottom
            changed = True

        if changed:
            # Only scroll to integers. Otherwise we end up with pixels that
            # don't line up on the screen
            self.view_bottom = int(self.view_bottom)
            self.view_left = int(self.view_left)

            # Do the scrolling
            arcade.set_viewport(
                self.view_left,
                SCREEN_WIDTH + self.view_left,
                self.view_bottom,
                SCREEN_HEIGHT + self.view_bottom,
            )

        for bullet in self.bullet_list:
            """
            # Check this bullet to see if it hit a coin
            hit_list = arcade.check_for_collision_with_list(bullet, self.wall_list)

            # If it did, get rid of the bullet
            if len(hit_list) > 0:
                bullet.remove_from_sprite_lists()

            # For every coin we hit, add to the score and remove the coin
            for coin in hit_list:
                coin.remove_from_sprite_lists()
                self.life += 1
            """

            # If the bullet flies off-screen, remove it.
            if (
                bullet.bottom > SCREEN_WIDTH
                or bullet.top < 0
                or bullet.right < 0
                or bullet.left > SCREEN_WIDTH
            ):
                bullet.remove_from_sprite_lists()


# a building class that makes layout build easy
class Build:
    def __init__(
        self,
        image: str = None,
        scale: float = None,
        image_y: str = None,
        image_x: str = None,
    ) -> None:
        self.blocks = arcade.SpriteList()
        self.image = image
        self.scale = scale
        if image_y:
            self.image_y = image_y
        else:
            self.image_y = image
        if image_x:
            self.image_x = image_x
        else:
            self.image_x = image

    def lay(
        self,
        iteration: tuple,
        entry: str,
        default: int,
        image: str = None,
        scale: float = None,
    ):
        if image:
            self.image = image
            self.image_y = image
            self.image_x = image

        if scale:
            self.scale = scale

        for counter in range(iteration[0], iteration[1], iteration[2]):
            if entry == "x":
                block = arcade.Sprite(self.image_x, self.scale)
                block.center_x = counter
                block.center_y = default
            else:
                block = arcade.Sprite(self.image_y, self.scale)
                block.center_x = default
                block.center_y = counter
            self.blocks.append(block)

    def submit(self):
        return self.blocks
