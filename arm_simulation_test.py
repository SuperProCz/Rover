import pygame


pygame.init()
 
fps = 60
fpsClock = pygame.time.Clock()

WIDTH, HEIGHT = 640, 480
BLACK = (0,0,0)
BLUE = (0,0,255)
WHITE = (255,255,255)
RED = (255,0,0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Robo arm simulation')

class Rectangle():
    def __init__(self, coords: tuple, color: tuple, size: tuple) -> None:
        self.coords = coords
        self.color = color
        self.size = size
        self.points = 0

    def getPos(self):
       return (self.coords[0], self.coords[1])
    
    def setPose(self, coords: tuple):
       self.coords = coords

    def getColor(self):
       return self.color
    
    def getSize(self):
       return self.size
    
    def draw(self):
        pygame.draw.rect(screen, self.color, pygame.Rect(self.coords[0]-self.size[0]//2, self.coords[1]-self.size[1]//2, self.size[0], self.size[1]), 0)
    
    def getRect(self):
        return pygame.Rect(self.coords[0]-self.size[0]//2, self.coords[1]-self.size[1]//2, self.size[0], self.size[1])



class Arm(Rectangle):
    def __init__(self, coords: tuple, color: tuple, size: tuple, angle: float, parent) -> None:
        super().__init__(coords, color, size)
        self.angle = angle
        self.parent = parent

    def rotate(self, angle):
        self.angle += angle

    def draw(self): 
        pygame.draw.rect(screen, self.color, pygame.Rect(self.coords[0]-self.size[0]//2, self.coords[1]-self.size[1]//2, self.size[0], self.size[1]), 0)
    