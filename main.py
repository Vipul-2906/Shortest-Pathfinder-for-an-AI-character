import pygame
import heapq
import random
import time


# Globals
last_path_steps = None


# Constants
WIDTH = 640
ROWS = 20
GAP = WIDTH // ROWS

pygame.init()
WIN = pygame.display.set_mode((WIDTH, WIDTH + 100))
pygame.display.set_caption("Pathfinding Visualizer (Dijkstra)")
font = pygame.font.SysFont("Arial", 18)
character_img = pygame.image.load("robot.png").convert_alpha()
character_img = pygame.transform.scale(character_img, (80, 120))  # Adjust size
img_w, img_h = character_img.get_size()

# Themes
LIGHT = {"BG": (245, 245, 245), "GRID": (200, 200, 200), "TEXT": (0, 0, 0), "BTN": (180, 180, 180)}
DARK = {"BG": (30, 30, 30), "GRID": (60, 60, 60), "TEXT": (240, 240, 240), "BTN": (80, 80, 80)}
THEME = LIGHT

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (100, 255, 100)
BLUE = (100, 180, 255)
RED = (255, 100, 100)
ORANGE = (255, 165, 0)
PURPLE = (160, 32, 240)

class Node:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.x = col * GAP
        self.y = row * GAP
        self.color = WHITE
        self.distance = float("inf")
        self.f = float("inf")
        self.weight = random.choice([1, 2, 3])
        self.parent = None
        self.neighbors = []

    def get_pos(self): return self.row, self.col
    def is_barrier(self): return self.color == BLACK
    def is_start(self): return self.color == ORANGE
    def is_end(self): return self.color == PURPLE
    def reset(self): self.color = WHITE
    def make_start(self): self.color = ORANGE
    def make_closed(self): self.color = RED
    def make_open(self): self.color = GREEN
    def make_barrier(self): self.color = BLACK
    def make_end(self): self.color = PURPLE
    def make_path(self): self.color = BLUE
    def draw(self, win):
        pygame.draw.rect(win, self.color, (self.x, self.y, GAP, GAP), border_radius=3)

    
    # Show indices on start and end nodes
        if self.is_start() or self.is_end():
            index_text = font.render(f"{self.row},{self.col}", True, (0, 0, 0) if self.color != WHITE else (255, 255, 255))
            win.blit(index_text, (self.x + 5, self.y + 5))

    def update_neighbors(self, grid):
        self.neighbors = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            r, c = self.row + dr, self.col + dc
            if 0 <= r < ROWS and 0 <= c < ROWS and not grid[r][c].is_barrier():
                self.neighbors.append(grid[r][c])

def h(p1, p2): return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])
def make_grid(): return [[Node(i, j) for j in range(ROWS)] for i in range(ROWS)]

def draw_grid(win):
    for i in range(ROWS):
        pygame.draw.line(win, THEME["GRID"], (0, i * GAP ), (WIDTH, i * GAP  ))
        pygame.draw.line(win, THEME["GRID"], (i * GAP , 0), (i * GAP,  + WIDTH))


def draw_buttons(win, algo):
    for label, x in [("Start", 10), ("Clear", 90), ("Random", 170), ("Theme", 260), ("Algo: " + algo, 350)]:
        pygame.draw.rect(win, THEME["BTN"], (x, WIDTH + 10, 75, 35), border_radius=5)
        text = font.render(label, True, THEME["TEXT"])
        win.blit(text, (x + 8, WIDTH + 18))

def draw(win, grid, algo="Dijkstra", steps=None, robot_pos=None, state = None):
    win.fill(THEME["BG"])

    for row in grid:
        for node in row:
            node.draw(win)

    draw_grid(win)
    draw_buttons(win, algo)

    if steps is not None:
        label = font.render(f"Steps: {steps}", True, THEME["TEXT"])
        win.blit(label, (10, WIDTH + 50))

        stats = state.get("stats", {}) if state else {}
        time_label = font.render(f"Time: {int(stats.get('time', 0))}ms", True, THEME["TEXT"])
        visited_label = font.render(f"Visited: {stats.get('visited', 0)}", True, THEME["TEXT"])
        cost_label = font.render(f"Cost: {stats.get('cost', 0)}", True, THEME["TEXT"])

        win.blit(time_label, (150, WIDTH + 50))
        win.blit(visited_label, (300, WIDTH + 50))
        win.blit(cost_label, (450, WIDTH + 50))


    if robot_pos:
        cell_center_x = robot_pos.x + GAP // 2
        cell_center_y = robot_pos.y + GAP // 2
        img_x = cell_center_x - img_w // 2
        img_y = cell_center_y - img_h + GAP // 2
        win.blit(character_img, (img_x, img_y))

    pygame.display.update()


def get_button(pos):
    x, y = pos
    return x if y > WIDTH else -1

def reconstruct_path(current, start):
    path = []
    while current.parent:
        path.append(current)
        current = current.parent
    path.append(start)
    path.reverse()
    return path



def animate_robot_path(win, grid, path_nodes, fps=120, speed=7):
    clock = pygame.time.Clock()

    for i in range(len(path_nodes) - 1):
        current = path_nodes[i]
        next_node = path_nodes[i + 1]
        
        start_x = current.x + GAP // 2
        start_y = current.y + GAP // 2
        end_x = next_node.x + GAP // 2
        end_y = next_node.y + GAP // 2

        steps = speed  # Number of frames to move between tiles
        for step in range(steps):
            t = step / steps
            interp_x = (1 - t) * start_x + t * end_x
            interp_y = (1 - t) * start_y + t * end_y

            draw(win, grid)  # Background + grid + buttons
            img_x = interp_x - img_w // 2
            img_y = interp_y - img_h + GAP // 2
            win.blit(character_img, (img_x, img_y))

            pygame.display.update()
            clock.tick(fps)  # Control frame rate


def a_star(draw, grid, start, end):
    start_time = time.time()
    count = 0
    open_set = [(0, count, start)]
    start.distance = 0
    start.f = h(start.get_pos(), end.get_pos())
    visited_order = []

    while open_set:
        _, _, current = heapq.heappop(open_set)

        if current == end:
            break

        for neighbor in current.neighbors:
            temp_g = current.distance + neighbor.weight
            if temp_g < neighbor.distance:
                neighbor.distance = temp_g
                neighbor.f = temp_g + h(neighbor.get_pos(), end.get_pos())
                neighbor.parent = current
                heapq.heappush(open_set, (neighbor.f, count, neighbor))
                count += 1
                if neighbor != end:
                    neighbor.make_open()

        visited_order.append(current)
        draw()
        pygame.time.delay(8)
        if current != start:
            current.make_closed()

    for node in visited_order:
        if not node.is_start() and not node.is_end():
            node.reset()

    draw()
    pygame.time.delay(100)
    path = reconstruct_path(end, start)
    for node in path:
        if node != start and node != end:
            node.make_path()
    animate_robot_path(WIN, grid, path)
    elapsed_time = (time.time() - start_time) * 1000  # in milliseconds
    visited_count = len(visited_order)
    return len(path), path[-1], elapsed_time, visited_count, end.distance

def dijkstra(draw, grid, start, end):
    start_time = time.time()
    count = 0
    pq = [(0, count, start)]
    start.distance = 0
    visited_order = []
    while pq:
        _, _, current = heapq.heappop(pq)
        if current == end:
            break
        for neighbor in current.neighbors:
            temp = current.distance + neighbor.weight
            if temp < neighbor.distance:
                neighbor.distance = temp
                neighbor.parent = current
                heapq.heappush(pq, (neighbor.distance, count, neighbor))
                count += 1
                if neighbor != end:
                    neighbor.make_open()
        visited_order.append(current)
        draw()
        pygame.time.delay(8)
        if current != start:
            current.make_closed()
    for node in visited_order:
        if not node.is_start() and not node.is_end():
            node.reset()
    draw()
    pygame.time.delay(100)
    path = reconstruct_path(end, start)
    for node in path:
        if node != start and node != end:
            node.make_path()

    # Animate robot movement
    animate_robot_path(WIN, grid, path)
    elapsed_time = (time.time() - start_time) * 1000  # in milliseconds
    visited_count = len(visited_order)
    return len(path), path[-1], elapsed_time, visited_count, end.distance

def get_cell(pos):
    x, y = pos
    row = y // GAP
    col = x // GAP
    if 0 <= row < ROWS and 0 <= col < ROWS:
        return row, col
    return None

def main(win):
    state = {"robot_pos": None}
    state["stats"] = {"time": 0, "visited": 0, "cost": 0}
    global THEME, last_path_steps
    grid = make_grid()
    start = end = None
    algo = "Dijkstra"
    running = True
    while running:
        draw(win, grid, algo, steps=last_path_steps, robot_pos=state["robot_pos"],  state=state)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if pygame.mouse.get_pressed()[0]:
                pos = pygame.mouse.get_pos()
                if pos[1] > WIDTH:
                    x = get_button(pos)
                    if 10 <= x <= 85 and start and end:
                        for row in grid:
                            for node in row:
                                node.update_neighbors(grid)
                                node.distance = float("inf")
                                node.f = float("inf")
                                node.parent = None

                        if algo == "Dijkstra":
                            last_path_steps, state["robot_pos"], t, v, c = dijkstra(
                                lambda current=None: draw(win, grid, algo, steps=last_path_steps, robot_pos=current or state["robot_pos"],  state=state),
                                grid, start, end
                            )
                            state["stats"] = {"time": t, "visited": v, "cost": c}
                        else:
                            last_path_steps, state["robot_pos"], t, v, c = a_star(
                                lambda current=None: draw(win, grid, algo, steps=last_path_steps, robot_pos=current or state["robot_pos"],  state=state),
                                grid, start, end
                            )
                            state["stats"] = {"time": t, "visited": v, "cost": c}
                    elif 90 <= x <= 165:
                        start = end = None
                        last_path_steps = None
                        grid = make_grid()
                    elif 170 <= x <= 245:
                       for row in grid:
                            for node in row:
                                if node != start and node != end:
                                    barrier_chance = random.uniform(0, 0.5)  # random chance between 0% and 50%
                                    if random.random() < barrier_chance:
                                        node.make_barrier()
                                    else:
                                        node.weight = random.choice([1, 2, 3])
                                        node.reset()
                    elif 260 <= x <= 335:
                        THEME = DARK if THEME == LIGHT else LIGHT
                    elif 350 <= x <= 460:
                        algo = "A*" if algo == "Dijkstra" else "Dijkstra"

                else:
                    row, col = get_cell(pos)
                    node = grid[row][col]
                    if node.is_start():
                        node.reset()
                        start = None
                        state["robot_pos"] = None
                    elif node.is_end():
                        node.reset()
                        end = None
                    elif node.is_barrier():
                        node.reset()
                    elif not start and node != end:
                        start = node
                        start.make_start()
                        state["robot_pos"] = start
                    elif not end and node != start:
                        end = node
                        end.make_end()
                    elif node != start and node != end:
                        node.make_barrier()
            elif pygame.mouse.get_pressed()[2]:
                row, col = get_cell(pygame.mouse.get_pos())
                node = grid[row][col]
                node.reset()
                if node == start: start = None
                elif node == end: end = None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and start and end:
                for row in grid:
                    for node in row:
                        node.update_neighbors(grid)
                        node.distance = float("inf")
                        node.f = float("inf")
                        node.parent = None

                if algo == "Dijkstra":
                    last_path_steps, state["robot_pos"], t, v, c = dijkstra(
                        lambda current=None: draw(win, grid, algo, steps=last_path_steps, robot_pos=current or state["robot_pos"],  state=state),
                        grid, start, end
                    )
                    state["stats"] = {"time": t, "visited": v, "cost": c}
                else:
                    last_path_steps, state["robot_pos"], t, v, c = a_star(
                        lambda current=None: draw(win, grid, algo, steps=last_path_steps, robot_pos=current or state["robot_pos"],  state=state),
                        grid, start, end
                    )
                    state["stats"] = {"time": t, "visited": v, "cost": c}


    pygame.quit()

if __name__ == "__main__":
    main(WIN)
