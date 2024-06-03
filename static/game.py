from browser import document, html, window
import random

# 常量
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SPEED = 5
BULLET_SPEED = 7
ALIEN_SPEED_START = 1
ALIEN_SPEED_INCREMENT = 0.1
SPAWN_INTERVAL = 50  # 外星人生成间隔

# 获取Canvas上下文
canvas = document["gameCanvas"]
context = canvas.getContext("2d")

# 检测深色模式
def is_dark_mode():
    return window.matchMedia('(prefers-color-scheme: dark)').matches

# 设置字体和子弹颜色
FONT_COLOR = "black" if not is_dark_mode() else "white"
BULLET_COLOR = "black" if not is_dark_mode() else "white"

# 玩家类
class Player:
    def __init__(self):
        self.width = 50
        self.height = 50
        self.color = "green"
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT - self.height - 10
        self.speed = PLAYER_SPEED
        self.bullets = []

    def update(self, keys):
        if keys.get("ArrowLeft"):
            self.x -= self.speed
        if keys.get("ArrowRight"):
            self.x += self.speed
        if keys.get("ArrowUp"):
            self.y -= self.speed
        if keys.get("ArrowDown"):
            self.y += self.speed

        # 保持玩家在屏幕内
        self.x = max(self.x, 0)
        self.x = min(self.x, SCREEN_WIDTH - self.width)
        self.y = max(self.y, 0)
        self.y = min(self.y, SCREEN_HEIGHT - self.height)

    def draw(self):
        context.fillStyle = self.color
        context.fillRect(self.x, self.y, self.width, self.height)

    def shoot(self):
        bullet = Bullet(self.x + self.width // 2, self.y)
        self.bullets.append(bullet)

# 子弹类
class Bullet:
    def __init__(self, x, y):
        self.width = 5
        self.height = 10
        self.color = BULLET_COLOR
        self.x = x - self.width // 2
        self.y = y
        self.speed = BULLET_SPEED

    def update(self):
        self.y -= self.speed

    def draw(self):
        context.fillStyle = self.color
        context.fillRect(self.x, self.y, self.width, self.height)

# 外星人类
class Alien:
    def __init__(self, speed):
        self.width = 50
        self.height = 50
        self.color = "red"
        self.x = random.randint(0, SCREEN_WIDTH - self.width)
        self.y = random.randint(-100, -40)
        self.speed = speed

    def update(self):
        self.y += self.speed

    def draw(self):
        context.fillStyle = self.color
        context.fillRect(self.x, self.y, self.width, self.height)

# 游戏类
class Game:
    def __init__(self):
        self.player = Player()
        self.aliens = []
        self.score = 0
        self.alien_speed = ALIEN_SPEED_START
        self.spawn_timer = 0
        self.paused = False
        self.game_over_flag = False
        self.keys = {}

        document.bind("keydown", self.key_down_handler)
        document.bind("keyup", self.key_up_handler)
        self.create_touch_controls()
        self.restart_button = None

    def key_down_handler(self, event):
        self.keys[event.key] = True
        if event.key == " ":
            self.player.shoot()

    def key_up_handler(self, event):
        self.keys[event.key] = False

    def create_touch_controls(self):
        button_style = {
            "position": "absolute",
            "bottom": "10px",
            "fontSize": "20px",
            "padding": "10px",
            "backgroundColor": "black",
            "color": "white",
            "border": "1px solid white",  # 添加白色描边
            "cursor": "pointer",
            "transition": "transform 0.2s"
        }

        left_button = html.BUTTON("Left", style=button_style)
        left_button.style.left = "10px"
        right_button = html.BUTTON("Right", style=button_style)
        right_button.style.left = "90px"
        shoot_button = html.BUTTON("Shoot", style=button_style)
        shoot_button.style.left = "700px"

        def enlarge(event):
            event.target.style.transform = "scale(1.2)"

        def shrink(event):
            event.target.style.transform = "scale(1.0)"

        for button in [left_button, right_button, shoot_button]:
            button.bind("mousedown", self.start_moving_button_handler(button))
            button.bind("mouseup", self.stop_moving_button_handler(button))
            button.bind("mouseover", enlarge)
            button.bind("mouseout", shrink)

        document["gameCanvasContainer"] <= left_button
        document["gameCanvasContainer"] <= right_button
        document["gameCanvasContainer"] <= shoot_button

    def start_moving_button_handler(self, button):
        if button.textContent == "Left":
            return lambda event: self.start_moving("ArrowLeft")
        elif button.textContent == "Right":
            return lambda event: self.start_moving("ArrowRight")
        elif button.textContent == "Shoot":
            return lambda event: self.player.shoot()

    def stop_moving_button_handler(self, button):
        if button.textContent == "Left":
            return lambda event: self.stop_moving("ArrowLeft")
        elif button.textContent == "Right":
            return lambda event: self.stop_moving("ArrowRight")

    def start_moving(self, direction):
        self.keys[direction] = True

    def stop_moving(self, direction):
        self.keys[direction] = False

    def spawn_alien(self):
        alien = Alien(self.alien_speed)
        self.aliens.append(alien)

    def update(self):
        if not self.paused and not self.game_over_flag:
            self.player.update(self.keys)

            # 更新子弹
            for bullet in self.player.bullets:
                bullet.update()

            # 更新外星人
            for alien in self.aliens:
                alien.update()

            # 检查碰撞
            self.check_collisions()

            # 移除屏幕外的子弹和外星人
            self.player.bullets = [bullet for bullet in self.player.bullets if bullet.y > 0]
            self.aliens = [alien for alien in self.aliens if alien.y < SCREEN_HEIGHT]

            # 生成外星人
            self.spawn_timer += 1
            if self.spawn_timer >= SPAWN_INTERVAL:
                self.spawn_alien()
                self.spawn_timer = 0

            # 增加外星人速度
            self.alien_speed += ALIEN_SPEED_INCREMENT / 1000

    def check_collisions(self):
        for bullet in self.player.bullets:
            for alien in self.aliens:
                if (bullet.x < alien.x + alien.width and
                        bullet.x + bullet.width > alien.x and
                        bullet.y < alien.y + alien.height and
                        bullet.y + bullet.height > alien.y):
                    self.player.bullets.remove(bullet)
                    self.aliens.remove(alien)
                    self.score += 10
                    break

        for alien in self.aliens:
            if (self.player.x < alien.x + alien.width and
                    self.player.x + self.player.width > alien.x and
                    self.player.y < alien.y + alien.height and
                    self.player.y + self.player.height > alien.y):
                self.game_over()

    def draw(self):
        context.clearRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.player.draw()
        for bullet in self.player.bullets:
            bullet.draw()
        for alien in self.aliens:
            alien.draw()
        self.draw_text(f'Score: {self.score}', 25, SCREEN_WIDTH // 2, 20)

        if self.game_over_flag:
            self.draw_text('Game Over', 50, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)
            self.draw_text(f'Your Score: {self.score}', 36, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10)
            self.show_restart_button()

    def draw_text(self, text, size, x, y):
        context.font = f"{size}px Arial"
        context.fillStyle = FONT_COLOR
        context.textAlign = "center"
        context.fillText(text, x, y)

    def show_restart_button(self):
        if not self.restart_button:
            button_style = {
                "position": "absolute",
                "left": f"{SCREEN_WIDTH // 2 - 50}px",
                "top": f"{SCREEN_HEIGHT // 2 + 50}px",
                "fontSize": "30px",
                "padding": "15px",
                "backgroundColor": "black",
                "color": "white",
                "border": "1px solid white",  # 添加白色描边
                "cursor": "pointer",
                "transition": "transform 0.2s"
            }

            self.restart_button = html.BUTTON("Restart", id="restartButton", style=button_style)

            def enlarge(event):
                event.target.style.transform = "scale(1.2)"

            def shrink(event):
                event.target.style.transform = "scale(1.0)"

            self.restart_button.bind("mouseover", enlarge)
            self.restart_button.bind("mouseout", shrink)
            self.restart_button.bind("click", self.restart_game)
            document["gameCanvasContainer"] <= self.restart_button

    def restart_game(self, event):
        self.player = Player()
        self.aliens = []
        self.score = 0
        self.alien_speed = ALIEN_SPEED_START
        self.spawn_timer = 0
        self.paused = False
        self.game_over_flag = False
        if self.restart_button:
            self.restart_button.remove()
            self.restart_button = None

    def game_over(self):
        self.game_over_flag = True

# 主游戏循环
game = Game()

def main(*args):
    game.update()
    game.draw()
    window.requestAnimationFrame(main)

main()
