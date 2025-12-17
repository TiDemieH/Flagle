import pygame
import sys
import PIL.Image
import os
import random
import numpy
import time
import pickle

debug = []

class IconButton:
    def __init__(self, domain, image_path, pos, callback, nat_scale, hover_scale=1.1):
        self.domain = domain
        self.image_original = pygame.transform.smoothscale(pygame.image.load(image_path).convert_alpha(), nat_scale)
        self.image = self.image_original
        self.rect = self.image.get_rect(center=pos)
        self.callback = callback
        self.hover_scale = hover_scale
        self.pos = pos

    def update(self, mouse_pos, mouse_down):
        hovering = self.rect.collidepoint(mouse_pos)

        if hovering:
            scale = self.hover_scale
            new_size = (int(self.image_original.get_width() * scale),
                        int(self.image_original.get_height() * scale))
            self.image = pygame.transform.smoothscale(self.image_original, new_size)
            self.rect = self.image.get_rect(center=self.pos)

            if mouse_down:
                self.callback()
        else:
            self.image = self.image_original
            self.rect = self.image.get_rect(center=self.pos)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
    def getDomain(self):
        return self.domain

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS  # PyInstaller creates this temporary dir
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Constants
H_EDGE = 80
FLAG_SIZE = 2560//4
GUESS_SIZE = 2560//10
HOMEFLAG_SIZE = 150
FLAG_GAP = 50
GUESS_GAP = 9
ICON_GAP = 26
ICON_ALIGN = 53
TITLE = 50
TEXTBOX = 40
SUGGBOX = 30


WIDTH, HEIGHT = H_EDGE + ICON_GAP + FLAG_SIZE + FLAG_GAP + 2*(GUESS_SIZE) + GUESS_GAP + H_EDGE, TITLE + FLAG_SIZE + GUESS_GAP + TEXTBOX + 4*SUGGBOX + 2*GUESS_GAP
WHITE, LGRAY, GRAY, DGRAY, BLACK = (255,)*3, (234,)*3, (214,)*3, (175,)*3, (0,)*3
BLUE, GREEN, YELLOW, RED, DRED, DGREEN = (40, 120, 210), (0, 200, 0), (250, 180, 20), (220, 20, 20), (140, 0, 0), (0, 140, 0)
titleColors = (WHITE, GREEN, YELLOW, RED, DRED)
CALI = lambda size: pygame.font.SysFont("Calibri", size)
CAMB = lambda size: pygame.font.SysFont("Cambria", size)
ZAPF = lambda size: pygame.font.SysFont("Zapfino", size)


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flagle")
clock = pygame.time.Clock()
target, targets, targetFlag, inputText, counter, guessFlags, hintFlags, lastHint, hintView, clicked, titleColor, qImage, isDaily, dailyRecord, inftyMode = (True,)*15
mode = "h"


titleRect = pygame.Rect(0,0,WIDTH,TITLE)
titleText = CAMB(TITLE-20).render("Flagle", True, BLACK)
titleTextRect = titleText.get_rect(center=titleRect.center)
flagRect = pygame.Rect(H_EDGE + ICON_GAP,TITLE,FLAG_SIZE,FLAG_SIZE)
guessLocs = [(flagRect.x + FLAG_SIZE + FLAG_GAP + (i%2)*(GUESS_SIZE + GUESS_GAP) , TITLE + (i//2)*(GUESS_SIZE + GUESS_GAP)) for i in range(6)]
guessRects = [pygame.Rect(coord[0],coord[1],GUESS_SIZE,GUESS_SIZE) for coord in guessLocs]
textboxRect = pygame.Rect(flagRect.x, TITLE+FLAG_SIZE+GUESS_GAP, FLAG_SIZE, TEXTBOX)
clearSugRect = pygame.Rect(flagRect.x, TITLE+FLAG_SIZE+GUESS_GAP+TEXTBOX+GUESS_GAP, FLAG_SIZE, 30*5)

suggestions = None
matched_suggestions = []
with open(resource_path("pools/all.txt"),"r") as f:
    temp = f.readlines()
    suggestions = [e[:-5] for e in temp]
suggestionsL = [s.lower() for s in suggestions]

def textBox(text, point, font, color, align="left"):
    text = font.render(text, True, color)
    textRect = text.get_rect(midleft=point) if align=="left" else text.get_rect(center=point)
    return (text, textRect)

buttons = dict()
buttons["reset"] = IconButton(("e", ), resource_path("images/refresh.png"), pos=(ICON_ALIGN, 821), callback=lambda: resetGame((),repeat=True), nat_scale=(88,88))
buttons["up"] = IconButton(("g","e", ), resource_path("images/up.png"), pos=(ICON_ALIGN, TITLE+FLAG_SIZE//2-61), callback=lambda: bumpHintView(True), nat_scale=(100,100))
buttons["down"] = IconButton(("g","e", ), resource_path("images/down.png"), pos=(ICON_ALIGN, TITLE+FLAG_SIZE//2+61), callback=lambda: bumpHintView(False), nat_scale=(100,100))
buttons["home"] = IconButton(("g","e", ), resource_path("images/home.png"), pos=(ICON_ALIGN, 204), callback=lambda: setMode("h"), nat_scale=(120,120))
buttons["q"] = IconButton(("g",), resource_path("images/q.png"), pos=(ICON_ALIGN, 110), callback=lambda: None, nat_scale=(75,75))
buttons["infty"] = IconButton(("g",), resource_path("images/infty.png"), pos=(ICON_ALIGN, 530), callback=lambda: infty(), nat_scale=(90,60))
buttons["giveup"] = IconButton(("g",), resource_path("images/giveup.png"), pos=(ICON_ALIGN, 821), callback=lambda: finish(False), nat_scale=(71,71))

homeLocs = [HOMEFLAG_SIZE*(n+0.5) + (HEIGHT-5*HOMEFLAG_SIZE)*((n+1)/6) for n in range(5)]
buttons["easy"] = IconButton(("h", ), resource_path("images/easy.png"), pos=(100, homeLocs[1]), callback=lambda: resetGame(('easy',)), nat_scale=(HOMEFLAG_SIZE,HOMEFLAG_SIZE))
buttons["med"] = IconButton(("h", ), resource_path("images/med.png"), pos=(100, homeLocs[2]), callback=lambda: resetGame(('easy', 'med',)), nat_scale=(HOMEFLAG_SIZE,HOMEFLAG_SIZE))
buttons["hard"] = IconButton(("h", ), resource_path("images/hard.png"), pos=(100, homeLocs[3]), callback=lambda: resetGame(('easy', 'med', 'hard',)), nat_scale=(HOMEFLAG_SIZE,HOMEFLAG_SIZE))
buttons["poopoo"] = IconButton(("h", ), resource_path("images/poopoo.png"), pos=(100, homeLocs[4]), callback=lambda: resetGame(('easy', 'med', 'hard','poopoo',)), nat_scale=(HOMEFLAG_SIZE,HOMEFLAG_SIZE))

homeTexts = []
homeTexts.append(textBox("Daily", (210, homeLocs[0]), CAMB(50), BLACK))
homeTexts.append(textBox("Easy", (210, homeLocs[1]), CAMB(50), BLACK))
homeTexts.append(textBox("Medium", (210, homeLocs[2]), CAMB(48), BLACK))
homeTexts.append(textBox("Hard", (210, homeLocs[3]), CAMB(45), BLACK))
homeTexts.append(textBox("??????", (210, homeLocs[4]), CAMB(50), BLACK))
homeTexts.append(textBox("The Daily Flag. One chance per day", (500, homeLocs[0]), CAMB(34), BLACK))
homeTexts.append(textBox("Flags the average American might know", (500, homeLocs[1]), CAMB(34), BLACK))
homeTexts.append(textBox("Also includes lesser known flags", (500, homeLocs[2]), CAMB(34), BLACK))
homeTexts.append(textBox("For flag enthusiasts", (500, homeLocs[3]), CAMB(34), BLACK))
homeTexts.append(textBox("These places exist?", (500, homeLocs[4]), CAMB(34), BLACK))

with open(resource_path("data/daily.pkl"), "rb") as f:
    dailyRecord = pickle.loads(pickle.load(f))


def load(flag):
    return PIL.Image.open(resource_path(os.path.join('cleanflags',flag+'.png'))).convert("RGBA")

def guess(target, guess, current):
    # size=target.size
    # if not(target.size==guess.size and target.size==current.size):
    #     raise Exception()
    
    # pixels = zip(list(target.getdata()), list(guess.getdata()), list(current.getdata()))
    
    # retData = []
    # for p in pixels:
    #     tp, gp, cp = p[0], p[1], p[2]
    #     newp = cp
    #     if not (gp[3]==0 or tp[3]==0):
    #         gd, cd = math.dist(tp[:3],gp[:3]), 1000 if cp[3]==0 else math.dist(tp[:3],cp[:3])
    #         if gd<75 and gd<=cd:
    #             newp = gp
    #     retData.append(newp)
    
    # retImg = PIL.Image.new("RGBA", size)
    # retImg.putdata(retData)
    # return retImg

    if not (target.size == guess.size == current.size):
        raise Exception("Image sizes don't match")

    t = numpy.array(target,dtype=int)  # shape: (H, W, 4)
    g = numpy.array(guess,dtype=int)
    c = numpy.array(current,dtype=int)

    # Create mask: where both target and guess are not fully transparent
    mask = (t[:, :, 3] > 0) & (g[:, :, 3] > 0)

    # Compute RGB distances: dist(target, guess) and dist(target, current)
    tg_diff = numpy.linalg.norm(t[:, :, :3] - g[:, :, :3], axis=2)
    store,store2 = t,tg_diff
    tc_diff = numpy.full(tg_diff.shape, 1000.0)
    tc_mask = c[:, :, 3] > 0
    tc_diff[tc_mask] = numpy.linalg.norm(t[:, :, :3][tc_mask] - c[:, :, :3][tc_mask], axis=1)

    # Determine where guess is a good replacement
    replace_mask = (tg_diff < 75) & (tg_diff <= tc_diff) & mask
    # Apply the replacements
    c[replace_mask] = g[replace_mask]

    # Convert back to PIL image
    return PIL.Image.fromarray(c.astype(numpy.uint8), mode="RGBA")

def finish(won):
    global mode
    scaledHintFlag = pygame.transform.scale(pygame.image.fromstring(targetFlag.tobytes(), targetFlag.size, targetFlag.mode), (FLAG_SIZE, FLAG_SIZE))
    hintFlags.append(scaledHintFlag)
    if isDaily:
        if won:
            dailyRecord[day()] = len(hintFlags) - 1
        else:
            dailyRecord[day()] = "X"
    
    feedbacks.append((1e13,"You Won in "+str(len(hintFlags)-1)+("!" if len(hintFlags)<=3 else ""),DGREEN) if won else (1e13,"You Lose",DRED))
    mode = "e"
    
def resetGame(pools, preset=None, repeat=False):
    global target, targets, targetFlag, inputText, counter, guessFlags, hintFlags, lastHint, mode, hintView, titleColor, isDaily, feedbacks, inftyMode
    mode = "g"
    
    if not repeat:
        titleColor = titleColors[len(pools)]
        targets=[]
        if preset==None:
            for pool in pools:
                with open(resource_path((os.path.join("pools",pool+".txt"))),"r") as f:
                    for flag in f.readlines():
                        targets.append(flag[:-5])
            target = random.choice(targets)
            isDaily = False
        elif preset=="daily":
            random.seed(day())
            for pool in ('easy', 'med', 'hard',):
                with open(resource_path((os.path.join("pools",pool+".txt"))),"r") as f:
                    for flag in f.readlines():
                        targets.append(flag[:-5])
            target = random.choice(targets)
            random.seed(time.time())
            isDaily = True
        else:
            for pool in ('all',):
                with open(resource_path((os.path.join("pools",pool+".txt"))),"r") as f:
                    for flag in f.readlines():
                        targets.append(flag[:-5])
            target = preset
            isDaily = False
    else:
        target = random.choice(targets)
        
    targetFlag = load(target)
    inputText = ""
    counter = 0
    inftyMode = False
    feedbacks = []
    
    guessFlags, hintFlags = [],[]
    lastHint = PIL.Image.new("RGBA", (2560, 2560))
    lastHint.putdata([(0,0,0,0)]*(2560**2))
    scaledHintFlag = pygame.transform.scale(pygame.image.fromstring(lastHint.tobytes(), lastHint.size, lastHint.mode), (FLAG_SIZE, FLAG_SIZE))
    hintFlags.append(scaledHintFlag)
    hintView = -1
    unclick()
    
def bumpHintView(up):
    global hintView, hintFlags
    if up and hintView > -len(hintFlags)+1:
        hintView-=1
    elif not up and hintView < -1:
        hintView+=1
    unclick()
        
def setMode(setTo):
    global mode
    mode = setTo
    unclick()
        
def unclick():
    global clicked
    clicked = False        
        
def day():
    return time.time()//86400

def t():
    return time.time() - startTime
        
def infty():
    global inftyMode, feedbacks
    if inftyMode:
        feedbacks.remove((1e12,"Infinite Mode Enabled",DRED))
    else:
        feedbacks = [(1e12,"Infinite Mode Enabled",DRED)] + feedbacks
    inftyMode = not inftyMode


running = True
startTime = time.time()
if day() in dailyRecord.keys():
    homeTexts.append(textBox(str(dailyRecord[day()]), (103, homeLocs[0]+8), CAMB(88), RED, align = "c"))
else:
    homeTexts.append(textBox("?", (103, homeLocs[0]+8), CAMB(88), RED, align = "c"))

while running:
    clicked = False
    mx, my = pygame.mouse.get_pos()
    screen.fill(WHITE)
    
    
    if mode == "h":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                clicked = True
        for text,textRect in homeTexts:
            screen.blit(text, textRect)
            
        if "daily" in buttons.keys() and day() in dailyRecord.keys():
            buttons.pop("daily")
            homeTexts.append(textBox(str(dailyRecord[day()]), (103, homeLocs[0]+8), CAMB(88), RED, align = "c"))
        elif not "daily" in buttons.keys() and not day() in dailyRecord.keys():
            buttons["daily"] = IconButton(("h", ), "images/daily.png", pos=(100, homeLocs[0]), callback=lambda: resetGame((),preset='daily'), nat_scale=(HOMEFLAG_SIZE,HOMEFLAG_SIZE))
            homeTexts = homeTexts[:-1]
        
    elif mode == "q":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        if qImage==True:
            qImage = pygame.image.load("images/screenshot.png").convert_alpha()
        screen.blit(qImage, (0,0))
        if not buttons["q"].rect.collidepoint((mx,my)):
            setMode("g")
        
    else:
        feedbacks.sort(reverse = True)
        if feedbacks and feedbacks[-1][0]<t():
            feedbacks = feedbacks[:-1]
        for i in range(len(feedbacks)):
            timer,text,c = feedbacks[i]
            text = CAMB(30).render(text, True, c)
            alpha = min(200*(timer-t()),255)
            text.set_alpha(alpha)
            frameRect = pygame.Rect(textboxRect.x + 3, textboxRect.y + TEXTBOX + SUGGBOX*i + 3, textboxRect.width, 30)
            textRect = text.get_rect(midleft=frameRect.midleft)
            screen.blit(text, textRect)
            
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                clicked = True
    
            elif mode == "g":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        inputText = inputText[:-1]
                    elif event.key == pygame.K_RETURN:
                        if inputText in suggestions:
                            guessFlag = load(inputText)
                            scaledGuessFlag = pygame.transform.scale(pygame.image.fromstring(guessFlag.tobytes(), guessFlag.size, guessFlag.mode), (GUESS_SIZE, GUESS_SIZE))
                            pos = len(guessFlags) if len(guessFlags)<=5 else 5
                            frameRect = pygame.Rect(guessLocs[pos][0], guessLocs[pos][1]+GUESS_SIZE-25, GUESS_SIZE, 25)
                            guessText = CALI(20).render(inputText[:24], True, BLACK)
                            guessTextRect = guessText.get_rect(center=frameRect.center)
                            guessFlags.append((scaledGuessFlag, guessText, guessTextRect))
                            feedbacks.append((t()+4, "Guessed "+inputText, BLACK))
                            
                            
                            if inputText==target:
                                finish(True)
                            elif len(guessFlags)>=6 and not inftyMode:
                                finish(False)                      
                            else:
                                lastHint = guess(targetFlag, guessFlag, lastHint)
                                scaledHintFlag = pygame.transform.scale(pygame.image.fromstring(lastHint.tobytes(), lastHint.size, lastHint.mode), (FLAG_SIZE, FLAG_SIZE))
                                hintFlags.append(scaledHintFlag)
                            inputText = ""
                            hintView = -1
                            
                                
        
                        elif matched_suggestions:
                            inputText = matched_suggestions[0]
                            
                        else:
                            feedbacks.append((t()+4,"Not a Valid Flag",DRED))

                        
                    else:
                        inputText += event.unicode

                
        # Backspace faster
        if pygame.key.get_pressed()[pygame.K_BACKSPACE]:
            counter += 1
            if counter >= 14:
                counter = 0
                inputText = ""
        else:
            counter = 0
        
        pygame.draw.rect(screen, titleColor, titleRect, 0)
        screen.blit(titleText, titleTextRect)
        
        pygame.draw.rect(screen, GRAY, flagRect, 0)
        screen.blit(hintFlags[hintView], (flagRect.x, flagRect.y))
        if mode=="e":
            tempRect = pygame.Rect(flagRect.x, flagRect.y+FLAG_SIZE-50, FLAG_SIZE, 50)
            tempText = CAMB(40).render(target, True, BLACK)
            tempTextRect = tempText.get_rect(center=tempRect.center)
            screen.blit(tempText, tempTextRect)
        
        for rect in guessRects:
            pygame.draw.rect(screen, GRAY, rect, 0)
        for i in range(len(guessFlags)):
            if not i == len(guessFlags)-1 and i>4:
                continue
            guessFlag, guessText, guessTextRect = guessFlags[i]
            if i<=5:
                screen.blit(guessFlag, guessLocs[i])
                screen.blit(guessText, guessTextRect)
            else:
                screen.blit(guessFlag, guessLocs[5])
                screen.blit(guessText, guessTextRect)
    
    
        # Match suggestions
        matched_suggestions = [s for s in suggestions if inputText.lower() == s.lower()] if inputText.lower() in suggestionsL else [s for s in suggestions if inputText.lower() in s.lower() and inputText]
    
        pygame.draw.rect(screen, LGRAY, textboxRect, 0)
        pygame.draw.rect(screen, BLACK, textboxRect, 2)
        txtSurface = CALI(TEXTBOX-10).render(inputText, True, BLACK)
        screen.blit(txtSurface, (textboxRect.x + 5, textboxRect.y + 4))
        
        cursorPoint = txtSurface.get_rect().topright
        cursor = pygame.Rect((cursorPoint[0] + textboxRect.x + 5, cursorPoint[1] + textboxRect.y + 5), (3,TEXTBOX-10))
        if t()%2<1:
            pygame.draw.rect(screen, BLACK, cursor, 0)
        
        txt_surface = CALI(TEXTBOX-17).render("Press Enter to Guess", True, BLACK)
        txt_surface.set_alpha(100)
        screen.blit(txt_surface, (textboxRect.x + 408, textboxRect.y + 6))
    
        if mode=="g":
            for i, suggestion in enumerate(matched_suggestions[:4]):
                sugRect = pygame.Rect(textboxRect.x, textboxRect.y + TEXTBOX + SUGGBOX*i, textboxRect.width, 30)
                if sugRect.collidepoint((mx, my)):
                    pygame.draw.rect(screen, BLUE if suggestion in targets else DGRAY, sugRect, 0)
                    if clicked:
                        inputText = suggestion
                else:
                    pygame.draw.rect(screen, LGRAY if suggestion in targets else GRAY, sugRect, 0)
                pygame.draw.rect(screen, DGRAY, sugRect, 1)
                sugSurface = CALI(SUGGBOX-10).render(suggestion, True, BLACK)
                screen.blit(sugSurface, (sugRect.x + 5, sugRect.y + 4))
        if mode=="g":       
            if buttons["q"].rect.collidepoint((mx,my)):
                setMode("q")


    #in both modes
    for key in buttons:
        if key == "reset" and isDaily:
            continue
        if key == "infty" and isDaily:
            continue
        button = buttons[key]
        if mode in button.getDomain():
            button.update((mx,my), clicked)
            button.draw(screen)


    pygame.display.flip()
    clock.tick(30)


with open(resource_path("data/daily.pkl"), "wb") as f:
    pickle.dump(pickle.dumps(dailyRecord), f)


pygame.quit()
sys.exit()







