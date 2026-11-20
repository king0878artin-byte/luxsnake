
from random import choice, choices
import os

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.storage.jsonstore import JsonStore
from kivy.core.window import Window

Window.clearcolor = (.008, .018, .012, 1)


class Board(Widget):

    def __init__(self, store, **kw):
        super().__init__(**kw)

        self.store = store
        self.n = 18

        self.snake = []
        self.food = None
        self.food_type = "normal"

        self.direction = (1, 0)
        self.next_dir = (1, 0)

        self.running = False
        self.score = 0
        self.start_touch = None

        self.mode = "Medium"

        self.bind(pos=self.draw, size=self.draw)

        self.reset()
        Clock.schedule_interval(self.step, .15)

    def set_mode(self, mode):
        self.mode = mode
        self.reset()

    def reset(self):
        self.snake = [
            (5, 9), (4, 9), (3, 9), (2, 9), (1, 9)
        ]

        self.direction = (1, 0)
        self.next_dir = (1, 0)

        self.score = 0
        self.running = False
        self.start_touch = None

        self.spawn()
        self.draw()

        if hasattr(self, "score_cb"):
            self.score_cb(0)

    def begin(self):
        self.reset()
        self.running = True

    def spawn(self):
        free = [
            (x, y)
            for x in range(self.n)
            for y in range(self.n)
            if (x, y) not in self.snake
        ]

        if not free:
            self.food = None
            self.running = False
            return

        self.food = choice(free)

        if self.mode == "Easy":
            types = [
                "normal", "normal", "normal",
                "normal", "normal", "green",
                "green", "gold", "red"
            ]

            weights = [20, 20, 20, 20, 20, 7, 7, 3, 1]

        else:
            types = ["normal", "green", "gold"]
            weights = [80, 15, 5]

        self.food_type = choices(
            types,
            weights=weights,
            k=1
        )[0]

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.start_touch = (
                touch.uid,
                touch.x,
                touch.y
            )
            return True

        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.start_touch:
            uid, start_x, start_y = self.start_touch

            if uid != touch.uid:
                return super().on_touch_up(touch)

            dx = touch.x - start_x
            dy = touch.y - start_y

            self.start_touch = None

            if max(abs(dx), abs(dy)) > dp(12):

                if abs(dx) > abs(dy):
                    direction = (1, 0) if dx > 0 else (-1, 0)
                else:
                    direction = (0, 1) if dy > 0 else (0, -1)

                opposite = (
                    -self.next_dir[0],
                    -self.next_dir[1]
                )

                if direction != opposite:
                    self.next_dir = direction

            return True

        return super().on_touch_up(touch)

    def step(self, dt):
        if not self.running:
            return

        self.direction = self.next_dir

        x, y = self.snake[0]
        dx, dy = self.direction

        head = (x + dx, y + dy)

        # Easy and Medium: Wrap around the walls
        if self.mode in ("Easy", "Medium"):
            head = (
                head[0] % self.n,
                head[1] % self.n
            )

        # Hard: Hitting a wall ends the game
        else:
            if (
                head[0] < 0
                or head[0] >= self.n
                or head[1] < 0
                or head[1] >= self.n
            ):
                self.end_game()
                return

        if head in self.snake[:-1]:
            self.end_game()
            return

        self.snake.insert(0, head)

        if head == self.food:

            points = {
                "normal": 2,
                "green": 5,
                "gold": 10,
                "red": 30
            }

            self.score += points.get(self.food_type, 2)

            self.spawn()

            if hasattr(self, "score_cb"):
                self.score_cb(self.score)

        else:
            self.snake.pop()

        self.draw()

    def end_game(self):
        self.running = False

        if hasattr(self, "over_cb"):
            self.over_cb()

        self.draw()

    def draw(self, *args):
        self.canvas.clear()

        if self.width <= 0 or self.height <= 0:
            return

        side = min(self.width * .94, self.height * .94)

        x0 = self.center_x - side / 2
        y0 = self.center_y - side / 2

        cell = side / self.n

        with self.canvas:

            Color(.02, .12, .045, .5)

            RoundedRectangle(
                pos=(x0-dp(3), y0-dp(3)),
                size=(side+dp(6), side+dp(6)),
                radius=[dp(28)]
            )

            Color(.006, .018, .011, 1)

            RoundedRectangle(
                pos=(x0, y0),
                size=(side, side),
                radius=[dp(26)]
            )

            Color(.13, .23, .16, .38)

            for i in range(self.n + 1):
                Line(
                    points=[
                        x0+i*cell, y0,
                        x0+i*cell, y0+side
                    ],
                    width=.55
                )

                Line(
                    points=[
                        x0, y0+i*cell,
                        x0+side, y0+i*cell
                    ],
                    width=.55
                )

            if self.food:
                fx, fy = self.food

                px = x0 + fx*cell
                py = y0 + fy*cell

                colors = {
                    "normal": (.75, .025, .035, 1),
                    "green": (.12, .95, .12, 1),
                    "gold": (1, .72, .02, 1),
                    "red": (.05, .35, 1, 1)
                }

                Color(*colors.get(
                    self.food_type,
                    (.75, .025, .035, 1)
                ))

                Ellipse(
                    pos=(px+cell*.12, py+cell*.12),
                    size=(cell*.76, cell*.76)
                )

                Color(1, 1, 1, .65)

                Ellipse(
                    pos=(px+cell*.25, py+cell*.62),
                    size=(cell*.16, cell*.10)
                )

                Color(.4, .95, .16, 1)

                Line(
                    points=[
                        px+cell*.5, py+cell*.8,
                        px+cell*.56, py+cell*.98
                    ],
                    width=1.4
                )

                Ellipse(
                    pos=(px+cell*.52, py+cell*.82),
                    size=(cell*.3, cell*.14)
                )

            for i, (sx, sy) in enumerate(reversed(self.snake)):

                px = x0 + sx*cell
                py = y0 + sy*cell

                p = dp(1.2)

                if i == len(self.snake)-1:
                    Color(.1, 1, .1, .2)

                    RoundedRectangle(
                        pos=(px, py),
                        size=(cell, cell),
                        radius=[cell*.25]
                    )

                Color(.12, .95, .08, 1)

                RoundedRectangle(
                    pos=(px+p, py+p),
                    size=(cell-2*p, cell-2*p),
                    radius=[cell*.23]
                )

                Color(.65, 1, .48, .8)

                Line(
                    rounded_rectangle=(
                        px+p, py+p,
                        cell-2*p, cell-2*p,
                        cell*.23
                    ),
                    width=.7
                )

            hx, hy = self.snake[0]

            cx = x0 + (hx+.5)*cell
            cy = y0 + (hy+.5)*cell

            dx, dy = self.direction

            ex = cx + (dx*.18-dy*.16)*cell
            ey = cy + (dy*.18+dx*.16)*cell

            Color(.005, .008, .003, 1)

            Ellipse(
                pos=(ex-cell*.085, ey-cell*.085),
                size=(cell*.17, cell*.17)
            )


class LuxSnake(App):

    def build(self):
        score_path = os.path.join(
            self.user_data_dir,
            "luxsnake_scores.json"
        )

        self.store = JsonStore(score_path)

        self.best_score = 0
        self.best_mode = "Medium"

        if self.store.exists("best"):
            data = self.store.get("best")
            self.best_score = data["score"]
            self.best_mode = data["mode"]

        root = FloatLayout()

        self.score = Label(
            text="Score: 0",
            font_size="21sp",
            bold=True,
            color=(.55, 1, .4, 1),
            size_hint=(.48, None),
            height=dp(42),
            pos_hint={"x": .01, "top": .99}
        )

        root.add_widget(self.score)

        self.best = Label(
            text=self.best_text(),
            font_size="15sp",
            bold=True,
            color=(1, .82, .25, 1),
            size_hint=(.50, None),
            height=dp(42),
            pos_hint={"right": .99, "top": .99}
        )

        root.add_widget(self.best)

        self.board = Board(
            self.store,
            size_hint=(.96, .65),
            pos_hint={
                "center_x": .5,
                "center_y": .56
            }
        )

        self.board.score_cb = self.update_score
        self.board.over_cb = self.game_over

        root.add_widget(self.board)

        self.info = Label(
            text="Swipe to change direction",
            font_size="13sp",
            color=(.72, .88, .72, 1),
            size_hint=(1, None),
            height=dp(32),
            pos_hint={
                "center_x": .5,
                "y": .205
            }
        )

        root.add_widget(self.info)

        self.easy_btn = self.make_mode_button(
            "Easy",
            .04,
            (.12, .65, .18, 1)
        )

        self.medium_btn = self.make_mode_button(
            "Medium",
            .36,
            (.12, .45, .75, 1)
        )

        self.hard_btn = self.make_mode_button(
            "Hard",
            .68,
            (.75, .12, .12, 1)
        )

        root.add_widget(self.easy_btn)
        root.add_widget(self.medium_btn)
        root.add_widget(self.hard_btn)

        self.button = Button(
            text="Start Game",
            font_size="18sp",
            bold=True,
            size_hint=(.55, None),
            height=dp(48),
            pos_hint={
                "center_x": .5,
                "y": .015
            },
            background_normal="",
            background_color=(.16, .75, .12, 1),
            color=(.02, .06, .02, 1)
        )

        self.button.bind(on_release=self.start)
        root.add_widget(self.button)

        self.refresh_mode_buttons()

        return root

    def make_mode_button(self, text, x, color):
        btn = Button(
            text=text,
            font_size="15sp",
            bold=True,
            size_hint=(.27, None),
            height=dp(40),
            pos_hint={"x": x, "y": .145},
            background_normal="",
            background_color=color
        )

        btn.bind(
            on_release=lambda instance, mode=text:
            self.select_mode(mode)
        )

        return btn

    def refresh_mode_buttons(self):
        selected = self.board.mode

        self.easy_btn.opacity = 1 if selected == "Easy" else .55
        self.medium_btn.opacity = 1 if selected == "Medium" else .55
        self.hard_btn.opacity = 1 if selected == "Hard" else .55

    def select_mode(self, mode):
        self.board.set_mode(mode)

        self.info.text = {
            "Easy": "Easy: Wall wrapping enabled",
            "Medium": "Medium: Wall wrapping enabled",
            "Hard": "Hard: Wall collision = Game Over"
        }[mode]

        self.button.text = "Start Game"
        self.refresh_mode_buttons()
        self.update_score(0)

    def best_text(self):
        return (
            f"Best: {self.best_score} "
            f"({self.best_mode})"
        )

    def update_score(self, score):
        self.score.text = f"Score: {score}"

        if score > self.best_score:
            self.best_score = score
            self.best_mode = self.board.mode

            self.store.put(
                "best",
                score=self.best_score,
                mode=self.best_mode
            )

            self.best.text = self.best_text()

    def game_over(self):
        self.info.text = "Game Over! Try Again"

    def start(self, *args):
        self.board.begin()

        self.info.text = "Swipe to control the snake"
        self.button.text = "Restart"
        self.update_score(0)


if __name__ == "__main__":
    LuxSnake().run()
