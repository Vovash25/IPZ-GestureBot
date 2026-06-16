import pygame
import random

class Shape:
    def __init__(self, x, y):
        self.type = random.choice(['triangle', 'square', 'circle'])
        self.size = 100  
        half = self.size // 2 
        bright = random.randint(80, 255)
        self.color = (0, bright, 0)
        self.thickness = random.choice([0, 3])
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x - half, y - half, self.size, self.size)

    def update_pos(self, x, y):
        self.x = x
        self.y = y
        self.rect.center = (x, y)

    def draw(self, surf):
        half = self.size // 2
        if self.type == 'circle':
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), half, self.thickness)
        elif self.type == 'square':
            pygame.draw.rect(surf, self.color, (self.x - half, self.y - half, self.size, self.size), self.thickness)
        elif self.type == 'triangle':
            pts = [
                (self.x, self.y - half),
                (self.x - half, self.y + half),
                (self.x + half, self.y + half)
            ]
            pygame.draw.polygon(surf, self.color, pts, self.thickness)

def run_display(conveyor_running, conveyor_speed, app_mode):
    pygame.init()
    monitor_info = pygame.display.Info()
    WIDTH = int(monitor_info.current_w * 0.8)
    HEIGHT = int(monitor_info.current_h * 0.5)
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Robot System Simulator")
    clock = pygame.time.Clock()

    conveyor_shapes = []
    manual_shape = Shape(WIDTH // 4, HEIGHT // 2)
    target_rect = pygame.Rect(WIDTH - 200, HEIGHT // 4, 150, 150)
    dragging = False

    running = True
    while running:
        current_mode = app_mode.value
        screen.fill((10, 10, 10))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.size
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                target_rect.x = WIDTH - 200
                target_rect.y = HEIGHT // 4

            if current_mode == 1:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if manual_shape.rect.collidepoint(event.pos):
                        dragging = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragging:
                        dragging = False
                        if target_rect.collidepoint(event.pos):
                            manual_shape = Shape(WIDTH // 4, HEIGHT // 2)
                elif event.type == pygame.MOUSEMOTION:
                    if dragging:
                        manual_shape.update_pos(event.pos[0], event.pos[1])

        if current_mode == 0:
            if conveyor_running.is_set():
                if len(conveyor_shapes) == 0 or conveyor_shapes[-1].x > (WIDTH // 3):
                    conveyor_shapes.append(Shape(-50, HEIGHT // 2))
                for s in conveyor_shapes[:]:
                    s.update_pos(s.x + conveyor_speed.value, s.y)
                    s.draw(screen)
                    if s.x > WIDTH + 100: conveyor_shapes.remove(s)
            else:
                for s in conveyor_shapes: s.draw(screen)
        else:
            pygame.draw.rect(screen, (50, 50, 50), target_rect, 2)
            font = pygame.font.SysFont("Arial", 18)
            txt = font.render("DROP HERE", True, (100, 100, 100))
            text_x = target_rect.x + (target_rect.width - txt.get_width()) // 2
            text_y = target_rect.y + (target_rect.height - txt.get_height()) // 2
            screen.blit(txt, (text_x, text_y))
            manual_shape.draw(screen)

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
