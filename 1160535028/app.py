import pygame
import random
import sys

# 初始化 Pygame
pygame.init()

# 設定視窗與常數
WIDTH, HEIGHT = 600, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python 打地鼠遊戲")
FPS = 60

# 顏色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (85, 170, 85)       # 草地背景
DARK_BROWN = (60, 40, 20)   # 洞穴顏色
BROWN = (139, 69, 19)       # 地鼠顏色
RED = (200, 50, 50)         # 陷阱顏色
GRAY = (200, 200, 200)      # UI 面板背景

# 字體設定
try:
    FONT_LARGE = pygame.font.SysFont("microsoftjhenghei", 64)
    FONT_MEDIUM = pygame.font.SysFont("microsoftjhenghei", 36)
    FONT_SMALL = pygame.font.SysFont("microsoftjhenghei", 24)
    FONT_MEDIUM_BOLD = pygame.font.SysFont("microsoftjhenghei", 36, bold=True)
except:
    # 若系統無微軟正黑體，退回預設字體
    FONT_LARGE = pygame.font.Font(None, 64)
    FONT_MEDIUM = pygame.font.Font(None, 36)
    FONT_SMALL = pygame.font.Font(None, 24)
    FONT_MEDIUM_BOLD = pygame.font.Font(None, 36)
    try:
        FONT_MEDIUM_BOLD.set_bold(True)
    except:
        pass

# 定義 3x3 九個洞穴的位置 (x, y)
HOLES = [
    (150, 150), (300, 150), (450, 150),
    (150, 300), (300, 300), (450, 300),
    (150, 450), (300, 450), (450, 450)
]

class Game:
    def __init__(self):
        self.reset_game()
        self.state = "START"  # 狀態：START, COUNTDOWN, PLAYING, GAME_OVER
        self.clock = pygame.time.Clock()
        self.running = True

    def reset_game(self):
        self.score = 0
        self.level = 1
        self.game_time = 45  # 遊戲時間 45 秒
        self.start_ticks = 0
        self.countdown_ticks = 0
        
        # 實體狀態 (地鼠或陷阱)
        self.active_entities = [None] * 9  # None, 'mole', 'trap'
        self.entity_timers = [0] * 9       # 記錄實體還剩多久消失
        
        # 關卡難度參數
        self.spawn_rate = 1000  # 幾毫秒產生一次
        self.stay_time = 1500   # 停留多久(毫秒)
        self.last_spawn_time = 0
        # 給藍鑽地鼠用的計時器與間隔
        self.last_diamond_spawn_time = 0
        self.diamond_spawn_interval = 2000  # 每 2000 ms 嘗試出現一次
        # 擊中特效記錄: 每個洞穴可有一個短暫特效
        self.hit_effects = [None] * 9  # None or dict with keys: start, dur, points, type

    def draw_text(self, text, font, color, x, y, center=True):
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        SCREEN.blit(surface, rect)

    def draw_button(self, text, x, y, w, h, inactive_color, active_color, action=None):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        clicked = False

        if x < mouse[0] < x + w and y < mouse[1] < y + h:
            pygame.draw.rect(SCREEN, active_color, (x, y, w, h), border_radius=10)
            if click[0] == 1 and action != None:
                clicked = True
        else:
            pygame.draw.rect(SCREEN, inactive_color, (x, y, w, h), border_radius=10)

        self.draw_text(text, FONT_MEDIUM, BLACK, x + w/2, y + h/2)
        return clicked

    def spawn_entity(self, current_time):
        empty_holes = [i for i, entity in enumerate(self.active_entities) if entity is None]
        if empty_holes and current_time - self.last_spawn_time > self.spawn_rate:
            idx = random.choice(empty_holes)
            # 70% 機率是地鼠，30% 是陷阱
            if random.random() < 0.3:
                self.active_entities[idx] = 'trap'
            else:
                self.active_entities[idx] = 'mole'
            self.entity_timers[idx] = current_time + self.stay_time
            self.last_spawn_time = current_time

    def spawn_diamond_mole(self, current_time):
        # 每隔固定時間在隨機空位出現一隻頭頂有藍色鑽石的地鼠
        empty_holes = [i for i, entity in enumerate(self.active_entities) if entity is None]
        if empty_holes and current_time - self.last_diamond_spawn_time > self.diamond_spawn_interval:
            idx = random.choice(empty_holes)
            self.active_entities[idx] = 'mole_diamond'
            self.entity_timers[idx] = current_time + self.stay_time
            self.last_diamond_spawn_time = current_time

    def check_level_up(self):
        # 每得 40 分升一級
        new_level = (self.score // 40) + 1
        if new_level > self.level:
            self.level = new_level
            # 增加難度：加快生成速度，縮短停留時間
            self.spawn_rate = max(300, 1000 - (self.level - 1) * 90)
            self.stay_time = max(500, 1500 - (self.level - 1) * 120)

    def handle_click(self, mouse_pos):
        for i, hole_pos in enumerate(HOLES):
            if self.active_entities[i] is not None:
                # 計算滑鼠與洞穴中心的距離
                dist = ((mouse_pos[0] - hole_pos[0])**2 + (mouse_pos[1] - hole_pos[1])**2)**0.5
                if dist < 50:  # 點擊半徑 50 內算擊中
                    entity_hit = self.active_entities[i]
                    points = 0
                    if entity_hit == 'mole':
                        points = 5
                    elif entity_hit == 'mole_diamond':
                        points = 8
                    elif entity_hit == 'trap':
                        points = -10
                    # 加分/扣分
                    self.score += points
                    self.check_level_up()
                    # 記錄擊中特效（使用當前時間）
                    effect = {
                        'start': pygame.time.get_ticks(),
                        'dur': 400,
                        'points': points,
                        'type': entity_hit
                    }
                    self.hit_effects[i] = effect
                    # 實體打中後消失（仍保留特效）
                    self.active_entities[i] = None
                    break

    def run(self):
        while self.running:
            SCREEN.fill(GREEN)
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "PLAYING":
                        self.handle_click(event.pos)

            if self.state == "START":
                self.draw_text("打地鼠遊戲", FONT_LARGE, BLACK, WIDTH/2, HEIGHT/3 - 50)
                self.draw_text("規則：打棕色地鼠 (+5分)，帶有鑽石的地鼠 (+8分)", FONT_SMALL, BLACK, WIDTH/2, HEIGHT/3 + 20)
                self.draw_text("避開兔子陷阱 (-10分)", FONT_SMALL, BLACK, WIDTH/2, HEIGHT/3 + 50)
                if self.draw_button("開始遊戲", 200, 300, 200, 60, GRAY, WHITE, action="START"):
                    self.state = "COUNTDOWN"
                    self.countdown_ticks = current_time
                    # 避免連續點擊判定
                    pygame.time.delay(200) 

            elif self.state == "COUNTDOWN":
                # 倒數 3 秒
                elapsed = (current_time - self.countdown_ticks) / 1000
                if elapsed < 1:
                    self.draw_text("3", FONT_LARGE, BLACK, WIDTH/2, HEIGHT/2)
                elif elapsed < 2:
                    self.draw_text("2", FONT_LARGE, BLACK, WIDTH/2, HEIGHT/2)
                elif elapsed < 3:
                    self.draw_text("1", FONT_LARGE, BLACK, WIDTH/2, HEIGHT/2)
                else:
                    self.state = "PLAYING"
                    self.start_ticks = current_time

            elif self.state == "PLAYING":
                # 計算剩餘時間
                time_passed = (current_time - self.start_ticks) / 1000
                time_left = max(0, self.game_time - int(time_passed))

                if time_left == 0:
                    self.state = "GAME_OVER"

                # 更新實體與生成
                self.spawn_entity(current_time)
                # 每隔一段時間生成一隻頭頂有藍色鑽石的地鼠
                self.spawn_diamond_mole(current_time)
                for i in range(9):
                    if self.active_entities[i] is not None:
                        if current_time > self.entity_timers[i]:
                            self.active_entities[i] = None # 時間到，自動消失

                # 畫洞穴
                for h_pos in HOLES:
                    pygame.draw.ellipse(SCREEN, DARK_BROWN, (h_pos[0]-45, h_pos[1]-20, 90, 40))

                # 補充背景物件：樹與花（美化背景）
                # 畫幾棵樹
                tree_positions = [(60, 100), (540, 120), (80, 360), (520, 420)]
                for tx, ty in tree_positions:
                    pygame.draw.rect(SCREEN, (90,60,30), (tx-8, ty+20, 16, 60))
                    pygame.draw.circle(SCREEN, (30,120,40), (tx, ty), 40)
                    pygame.draw.circle(SCREEN, (35,140,50), (tx-25, ty+10), 28)
                    pygame.draw.circle(SCREEN, (35,140,50), (tx+25, ty+10), 28)

                # 畫地上的小花（隨機但固定樣式）
                flower_positions = [(120,520),(200,500),(260,540),(340,510),(420,540),(480,500)]
                for fx, fy in flower_positions:
                    pygame.draw.circle(SCREEN, (255,200,200), (fx, fy), 6)
                    pygame.draw.circle(SCREEN, (255,150,150), (fx-6, fy), 4)
                    pygame.draw.circle(SCREEN, (255,150,150), (fx+6, fy), 4)

                # 畫實體 (地鼠或陷阱)
                for i, h_pos in enumerate(HOLES):
                    entity = self.active_entities[i]
                    if entity == 'mole':
                        # 畫地鼠 (棕色圓形與眼睛)
                        pygame.draw.circle(SCREEN, BROWN, (h_pos[0], h_pos[1]-15), 35)
                        pygame.draw.circle(SCREEN, BLACK, (h_pos[0]-12, h_pos[1]-25), 5)
                        pygame.draw.circle(SCREEN, BLACK, (h_pos[0]+12, h_pos[1]-25), 5)
                        pygame.draw.ellipse(SCREEN, BLACK, (h_pos[0]-5, h_pos[1]-10, 10, 5))
                    elif entity == 'mole_diamond':
                        # 畫有藍色鑽石的地鼠：先畫地鼠，再在頭上畫藍色菱形
                        pygame.draw.circle(SCREEN, BROWN, (h_pos[0], h_pos[1]-15), 35)
                        pygame.draw.circle(SCREEN, BLACK, (h_pos[0]-12, h_pos[1]-25), 5)
                        pygame.draw.circle(SCREEN, BLACK, (h_pos[0]+12, h_pos[1]-25), 5)
                        pygame.draw.ellipse(SCREEN, BLACK, (h_pos[0]-5, h_pos[1]-10, 10, 5))
                        # 畫藍色鑽石（菱形）
                        diamond_center = (h_pos[0], h_pos[1]-45)
                        diamond_size = 10
                        points = [
                            (diamond_center[0], diamond_center[1]-diamond_size),
                            (diamond_center[0]+diamond_size, diamond_center[1]),
                            (diamond_center[0], diamond_center[1]+diamond_size),
                            (diamond_center[0]-diamond_size, diamond_center[1])
                        ]
                        pygame.draw.polygon(SCREEN, (50,150,255), points)
                        pygame.draw.polygon(SCREEN, BLACK, points, 2)
                    elif entity == 'trap':
                        # 畫白色兔子（白色身體、紅眼睛、明顯耳朵）
                        body_center = (h_pos[0], h_pos[1]-15)
                        pygame.draw.circle(SCREEN, WHITE, body_center, 35)
                        # 眼睛（紅）
                        pygame.draw.circle(SCREEN, RED, (h_pos[0]-12, h_pos[1]-25), 5)
                        pygame.draw.circle(SCREEN, RED, (h_pos[0]+12, h_pos[1]-25), 5)
                        # 鼻子/嘴（黑）
                        pygame.draw.ellipse(SCREEN, BLACK, (h_pos[0]-5, h_pos[1]-10, 10, 5))
                        # 耳朵（白色三角，上方延伸）
                        ear_height = 45
                        ear_width = 14
                        left_ear = [(h_pos[0]-18, h_pos[1]-45), (h_pos[0]-8, h_pos[1]-45-ear_height), (h_pos[0]-4, h_pos[1]-25)]
                        right_ear = [(h_pos[0]+18, h_pos[1]-45), (h_pos[0]+8, h_pos[1]-45-ear_height), (h_pos[0]+4, h_pos[1]-25)]
                        pygame.draw.polygon(SCREEN, WHITE, left_ear)
                        pygame.draw.polygon(SCREEN, WHITE, right_ear)
                        pygame.draw.polygon(SCREEN, BLACK, left_ear, 2)
                        pygame.draw.polygon(SCREEN, BLACK, right_ear, 2)

                # 繪製擊中特效（圈圈、X 眼、彈出分數）
                for i, h_pos in enumerate(HOLES):
                    eff = self.hit_effects[i]
                    if eff is None:
                        continue
                    elapsed = current_time - eff['start']
                    if elapsed > eff['dur']:
                        # 特效結束
                        self.hit_effects[i] = None
                        continue
                    # 計算動畫進度（0..1）
                    prog = elapsed / eff['dur']
                    # 圈圈效果（從頭上放大並微透明，可用寬線表示）
                    head_pos = (h_pos[0], h_pos[1]-15)
                    max_radius = 46
                    radius = int(20 + prog * (max_radius - 20))
                    pygame.draw.circle(SCREEN, (255,220,0), head_pos, radius, 4)

                    # 眼睛變叉叉（兩個叉）
                    left_eye = (h_pos[0]-12, h_pos[1]-25)
                    right_eye = (h_pos[0]+12, h_pos[1]-25)
                    eye_size = 6
                    # left X
                    pygame.draw.line(SCREEN, BLACK, (left_eye[0]-eye_size, left_eye[1]-eye_size), (left_eye[0]+eye_size, left_eye[1]+eye_size), 3)
                    pygame.draw.line(SCREEN, BLACK, (left_eye[0]-eye_size, left_eye[1]+eye_size), (left_eye[0]+eye_size, left_eye[1]-eye_size), 3)
                    # right X
                    pygame.draw.line(SCREEN, BLACK, (right_eye[0]-eye_size, right_eye[1]-eye_size), (right_eye[0]+eye_size, right_eye[1]+eye_size), 3)
                    pygame.draw.line(SCREEN, BLACK, (right_eye[0]-eye_size, right_eye[1]+eye_size), (right_eye[0]+eye_size, right_eye[1]-eye_size), 3)

                    # 彈出分數文字（往上移動）
                    pts = eff['points']
                    sign = '+' if pts > 0 else ''
                    txt = f"{sign}{pts}"
                    # 向上偏移量
                    offset_y = int(-prog * 30)
                    text_color = (135, 206, 235) if pts > 0 else (220,50,50)
                    surf = FONT_MEDIUM_BOLD.render(txt, True, text_color)
                    rect = surf.get_rect()
                    rect.center = (h_pos[0], h_pos[1]-60 + offset_y)
                    SCREEN.blit(surf, rect)

                # 畫 UI
                pygame.draw.rect(SCREEN, BLACK, (0, 0, WIDTH, 50))
                self.draw_text(f"分數: {self.score}", FONT_MEDIUM, WHITE, 20, 10, center=False)
                self.draw_text(f"時間: {time_left}s", FONT_MEDIUM, WHITE, WIDTH/2, 25)
                self.draw_text(f"關卡: {self.level}", FONT_MEDIUM, WHITE, WIDTH - 120, 10, center=False)

            elif self.state == "GAME_OVER":
                # 結算視窗
                pygame.draw.rect(SCREEN, BLACK, (100, 100, 400, 400), border_radius=15)
                pygame.draw.rect(SCREEN, WHITE, (105, 105, 390, 390), border_radius=15)
                
                self.draw_text("遊戲結束!", FONT_LARGE, RED, WIDTH/2, 180)
                self.draw_text(f"最終分數: {self.score}", FONT_MEDIUM, BLACK, WIDTH/2, 260)
                self.draw_text(f"到達關卡: {self.level}", FONT_MEDIUM, BLACK, WIDTH/2, 320)

                # 再玩一次按鈕
                if self.draw_button("再玩一次", 150, 400, 140, 50, GRAY, GREEN, action="RESTART"):
                    self.reset_game()
                    self.state = "START"
                    pygame.time.delay(200)
                
                # 離開按鈕
                if self.draw_button("離開", 310, 400, 140, 50, GRAY, RED, action="QUIT"):
                    self.running = False

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()