import pygame
import math
from queue import PriorityQueue

WIDTH:int = 800
WIN = pygame.display.set_mode((WIDTH,WIDTH))
pygame.display.set_caption("A* path Finding Algorithm")

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
ORANGE= (255, 165, 0)
GREY = (128, 128, 128)
TURQUOISE = (64, 224, 208)


class Node:
    def __init__(self,row,col,width,total_rows):
        self.row = row
        self.col = col
        self.x  = col * width
        self.y = row * width
        self.color = WHITE
        self.neighbours = []
        self.width = width
        self.total_rows = total_rows
    
    def get_pos(self):
        return self.row,self.col
    
    def is_closed(self):
        return self.color == RED
    
    def is_open(self):
        return self.color == GREEN
    
    def is_barrier(self):
        return self.color == BLACK
    
    def is_start(self):
        return self.color == ORANGE
    
    def is_end(self):
        return self.color == TURQUOISE
    
    def reset(self):
        self.color = WHITE

    def make_closed(self):
        self.color = RED
    
    def make_start(self):
        self.color = ORANGE

    def make_open(self):
        self.color = GREEN
    
    def make_barrier(self):
        self.color = BLACK
    
    def make_end(self):
        self.color =TURQUOISE

    def make_path(self):
        self.color = PURPLE
    
    def draw(self,WIN):
        pygame.draw.rect(WIN,self.color,(self.x,self.y,self.width,self.width))

    def update_neighbours(self,grid):
        self.neighbours = []
        drow = [0,1,0,-1]
        dcol = [1,0,-1,0]
        for i in range(0,4):
            trow = self.row + drow[i]
            tcol = self.col + dcol[i]
            if 0 <= trow < self.total_rows and 0 <= tcol < self.total_rows:
                if not grid[trow][tcol].is_barrier():
                    self.neighbours.append(grid[trow][tcol])


    def __lt__(self,other):
        return False
    
def h(p1,p2):
    x1 ,y1 = p1
    x2,y2 = p2
    return abs(x1 - x2) + abs(y1 - y2)


def algorithm(draw,grid,start,end):
    count = 0
    open_set = PriorityQueue()
    came_from = {}

    g_score = {}
    f_score = {}

    for row in grid:
        for node in row:
            g_score[node] = float("inf")
            f_score[node] = float("inf")

    g_score[start] = 0    
    f_score[start]= h(start.get_pos(),end.get_pos())
    open_set.put((f_score[start],count,start))
    
    
    came_from[start] = None

    open_set_hash = {start}
    closed_set = set()

    while not open_set.empty():

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        score,count,current = open_set.get()
        open_set_hash.remove(current)

        if current == end:
            while current in came_from and came_from[current] is not None:
                current = came_from[current]
                current.make_path()
            end.make_end()
            return True

        closed_set.add(current)
        if current != start:
            current.make_closed()
        
        for spot in current.neighbours:
            if spot in closed_set:
                continue
            
            #If you later introduce weighted terrain (mud, water, hills):
            # temp_g_score = g_score[current] + spot.weight
            temp_g_score = g_score[current] + 1 

            if temp_g_score < g_score[spot]:
                g_score[spot] = temp_g_score
                f_score[spot] = temp_g_score + h(spot.get_pos(),end.get_pos())
                came_from[spot] = current

                if spot not in open_set_hash:
                    count += 1
                    open_set.put((f_score[spot],count,spot))
                    open_set_hash.add(spot)
                    spot.make_open()

    draw()

    return False




def make_grid(rows , width):
    grid = []
    gap = width // rows
    for i in range(rows):
        grid.append([])
        for j in range(rows):
            spot = Node(i,j,gap,rows)
            grid[i].append(spot)
    return grid

def draw_grid(WIN,rows,width): 
    gap = width // rows
    for i in range(rows):
        pygame.draw.line(WIN, GREY, (0, i * gap), (width, i * gap))   # horizontal
        pygame.draw.line(WIN, GREY, (i * gap, 0), (i * gap, width))  # vertical
        #drawing full line  ((x, 0) → (x, width))


def draw(WIN,grid,rows,width):
    WIN.fill(WHITE)

    for row in grid:
        for spot in row:
            spot.draw(WIN)
    
    draw_grid(WIN,rows,width)
    pygame.display.update()

def get_clicked_pos(pos,rows,width):
    gap = width // rows
    x , y = pos
    row = y // gap
    col = x // gap

    if row >= rows or col >= rows:
        return None,None 

    return row , col


def main(win,width):
    ROWS = 50
    grid = make_grid(ROWS,width)
    start = None
    end = None

    run = True
    while run:
        draw(win,grid,ROWS,width)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if pygame.mouse.get_pressed()[0]:#LEFT
                pos = pygame.mouse.get_pos()
                row,col = get_clicked_pos(pos,ROWS,width)
                if row is None:
                    continue
                spot = grid[row][col]
                if not start and spot != end:
                    start = spot
                    start.make_start()
                elif not end and spot != start:
                    end = spot
                    end.make_end()
                elif spot != end and spot != start:
                    spot.make_barrier()
            elif pygame.mouse.get_pressed()[2]:#RIGHT
                pos = pygame.mouse.get_pos()
                row,col = get_clicked_pos(pos,ROWS,width)
                if row is None:
                    continue
                spot = grid[row][col]
                spot.reset()
                if spot == start:
                    start = None
                elif spot == end:
                    end = None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and start and end:
                    for row in grid:
                        for spot in row:
                            spot.update_neighbours(grid)
                    algorithm(lambda: draw(win,grid,ROWS,width),grid,start,end)

                if event.key == pygame.K_c:
                    start  = None
                    end  = None
                    grid = make_grid(ROWS,width)



    pygame.quit()

main(WIN,WIDTH)














# #open_set_hash guarantees:
# “There is at most one active scheduled instance of this node in the queue.”
# It does not guarantee:
# that the node will never be reinserted
# that old entries never existed
# What actually happens in practice
# Node is inserted into open_set
# Later, a better path is found
# If the node is already scheduled, you update scores but do not reinsert
# If it was already popped, it may be reinserted


#we use count because if f_score for different node is same priority_queue checks for count