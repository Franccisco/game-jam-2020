import random
import arcade
import os
from multiprocessing import Process, Queue
from .networking import net_interface
import socket
import multiprocessing

SPRITE_SCALING_PLAYER = 0.2

enemy_pre_scale = 0.05
enemy_pre_pos = 500

SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Trio Survivals"
BOTTOM_VIEWPORT_MARGIN = 50
TOP_VIEWPORT_MARGIN = 100

PLAYER_MOVEMENT_SPEED = 5
GRAVITY = 1
PLAYER_JUMP_SPEED = 20

BULLET_SPEED = 30


def networking(forward, feedback, udp):
    while True:
        items_no = forward.qsize()

        for _ in range(items_no - 2):
            forward.get()
        data = list(forward.get())
        feedback.put(udp.transport(data))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    pl = net_interface.Pipe(server=socket.gethostname(), port=9000)
    print(pl.login(entry="create", room_name="game3", username="David"))
    for _ in range(3):
        print(pl.await_response())

    class Game(arcade.View):
        """ Main application class. """

        def __init__(self):
            """ Initializer """
            # Call the parent class initializer
            super().__init__()

            # Set the working directory (where we expect to find files) to the same
            # directory this .py file is in. You can leave this out of your own
            # code, but it is needed to easily run the examples using "python -m"
            # as mentioned at the top of this program.
            file_path = os.path.dirname(os.path.abspath(__file__))
            os.chdir(file_path)

            # Variables that will hold sprite lists
            self.player1 = None
            self.player2 = None
            self.player3 = None

            self.player_list = None
            self.wall_list = None

            self.jet_sound = arcade.sound.load_sound(":resources:sounds/laser2.wav")
            self.jet_gun = arcade.sound.load_sound(":resources:sounds/explosion2.wav")

            arcade.set_background_color(arcade.color.BLACK)
            self.background = None
            self.physics_engine = None
            self.view_bottom = 0

            self.forward = Queue()
            self.feedback = Queue()

        def setup(self):

            """ Set up the game and initialize the variables. """
            import os

            print(os.getcwd())

            self.background = arcade.load_texture("data/14.png")

            # Sprite lists
            self.player_list = arcade.SpriteList()

            # jet sprites
            self.player1 = arcade.Sprite("data/player1.png", SPRITE_SCALING_PLAYER)
            self.player2 = arcade.Sprite("data/player2.png", SPRITE_SCALING_PLAYER)
            self.player3 = arcade.Sprite("data/player3.png", SPRITE_SCALING_PLAYER)
            self.player1.center_x = 100
            self.player1.center_y = 100

            self.player2.center_x = 500
            self.player2.center_y = 100

            self.player3.center_x = 1000
            self.player3.center_y = 100

            self.player_list.append(self.player1)
            self.player_list.append(self.player2)
            self.player_list.append(self.player3)

            build = Build(scale=0.1, image="data/11.png")
            build.lay((0, 1000, 15), "x", 10)
            self.wall_list = build.submit()

            self.physics_engine = arcade.PhysicsEnginePlatformer(
                self.player1, self.wall_list, GRAVITY
            )

            sync = Process(target=networking, args=(self.forward, self.feedback, pl,))
            sync.start()

        def on_draw(self):
            """
            Render the screen.
            """

            # This command has to happen before we start drawing
            arcade.start_render()

            arcade.draw_lrwh_rectangle_textured(
                0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background
            )
            self.player_list.draw()
            self.wall_list.draw()

        def add_wall(self, pos=None):
            if pos:
                pos = random.randint(10, 650)

            wall = arcade.Sprite("data/11.png", 0.15)
            wall.position = (SCREEN_WIDTH, pos)
            wall.change_x = -5
            self.wall_list.append(wall)

        def on_key_press(self, key, modifiers):
            """Called whenever a key is pressed. """

            if key == arcade.key.SPACE or key == arcade.key.W:
                if self.physics_engine.can_jump():
                    self.player1.change_y = PLAYER_JUMP_SPEED
                    # arcade.play_sound(self.jump_sound)
            elif key == arcade.key.LEFT or key == arcade.key.A:
                self.player1.change_x = -PLAYER_MOVEMENT_SPEED
            elif key == arcade.key.RIGHT or key == arcade.key.D:
                self.player1.change_x = PLAYER_MOVEMENT_SPEED

        def on_key_release(self, key, modifiers):
            """Called when the user releases a key. """

            if key == arcade.key.LEFT or key == arcade.key.A:
                self.player1.change_x = 0
            elif key == arcade.key.RIGHT or key == arcade.key.D:
                self.player1.change_x = 0

        def on_mouse_press(self, x, y, button, modifiers):
            """
            Called whenever the mouse button is clicked.
            """
            self.add_wall()

        def on_update(self, delta_time):
            """ Movement and game logic """

            self.physics_engine.update()

            for i, wall in enumerate(self.wall_list):
                if wall.bottom > SCREEN_HEIGHT:
                    wall.remove_from_sprite_lists()

            changed = False
            # Scroll up
            top_boundary = self.view_bottom + SCREEN_HEIGHT - TOP_VIEWPORT_MARGIN
            if self.player1.top > top_boundary:
                self.view_bottom += self.player1.top - top_boundary
                changed = True

            # Scroll down
            bottom_boundary = self.view_bottom + BOTTOM_VIEWPORT_MARGIN
            if self.player1.bottom < bottom_boundary:
                self.view_bottom -= bottom_boundary - self.player1.bottom
                changed = True

            if changed:
                # Only scroll to integers. Otherwise we end up with pixels that
                # don't line up on the screen
                self.view_bottom = int(self.view_bottom)

                arcade.set_viewport(
                    0,
                    SCREEN_WIDTH + 0,
                    self.view_bottom,
                    SCREEN_HEIGHT + self.view_bottom,
                )

            self.stream()

        def stream(self):
            self.forward.put(())
            if not self.feedback.empty():
                data = self.feedback.get()
                if data[0]:
                    for seg in data[1]:
                        print(f"wall position ...{seg[1]}")
                        self.add_wall(pos=seg[1])

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

    class Menu(arcade.View):
        def __init__(self):
            super().__init__()

            self.background = None
            self.username = "Game"

        def on_draw(self) -> None:
            """Show the widgets."""
            arcade.start_render()

            # Draw the background
            arcade.draw_lrwh_rectangle_textured(
                0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background
            )

            arcade.draw_text(
                self.username,
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                arcade.csscolor.WHITE,
                130,
            )

        def setup(self):
            """Setup the view and initialize the variables."""
            self.background = arcade.load_texture(
                ":resources:images/backgrounds/abstract_1.jpg"
            )

        def start_game(self) -> None:
            """Switch to the Main Menu View."""
            main_menu_view = Game()
            self.window.show_view(main_menu_view)
            main_menu_view.setup()

        def on_key_press(self, key: int, modifiers: int) -> None:
            """Move to the next view when any key is pressed."""
            self.start_game()

        def on_update(self, delta_time: float):
            pass

    def main():
        window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        main_view = Menu()
        main_view.setup()
        window.show_view(main_view)
        arcade.run()

    main()
