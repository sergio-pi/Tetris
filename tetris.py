# -*- coding: utf-8 -*-
import os
import msvcrt
import datetime
from time import sleep
from random import randint

screenSize = (30, 20)
os.system('mode con: cols={0} lines={1}'.format(
    screenSize[0],
    screenSize[1]
))

# Windows keyboard polling from https://stackoverflow.com/a/303976
def kbfunc(): 
   x = msvcrt.kbhit()
   if x: 
      ret = ord(msvcrt.getch()) 
   else: 
      ret = 0 
   return ret

# Set a direction value according to user input
#       2
#   1   0   3   <- arrow keys map
def setDirection():
    global direction
    key = kbfunc()
    if key == 75:
        direction = 1
    elif key == 77:
        direction = 3
    elif key == 72:
        direction = 2
    elif key == 80:
        direction = 0
    elif key == 27:     # Escape key to quit
        direction = 10

def resetGame():
    global setPieces, score, lastTime, currentPiece
    setPieces = []
    score = 0
    lastTime = datetime.datetime.now()
    currentPiece = -1
    changePiece()

# Vector-Matrix multiplication
def vecMatrix(v, m):
    transformed = []
    for vdim in range(len(v)):
        dotp = sum([a*b for a, b in zip(v, [i[vdim] for i in m])])
        transformed.append(dotp)
    return transformed

def rotatePiece(piece):
    newp = []
    for i in piece:
        # Translate the piece to the origin before rotation
        pieceOrigin = [i[0]-piece[0][0], i[1]-piece[0][1]]
        newv = [a+b for a,b in zip(vecMatrix(pieceOrigin, rotationMatrix), piece[0])]
        newp.append(newv)
    return newp

def collisionHit(pieceToTest):
    global setPieces
    hit = False
    for i in pieceToTest:
        # CD against game borders
        if i[1] == screenSize[1]-1:
            hit = True
            break
        if i[0]<2 or i[0]>11:
            hit = True
            break
        # CD against pieces set
        for j in setPieces:
            if i in j:
                hit = True
                break
        else:
            continue    # executed if the (for j) loop ended normally (no break)
        break           # executed if 'continue' was skipped (break the whole nested loop)
    return hit

def heightComponents(piece):
    yComp = []
    for i in piece:
        if i[1] not in yComp:
            yComp.append(i[1])
    return yComp

def getFilledRows(pieces, yComp):
    counted = {key: 0 for key in yComp}
    filled = []
    for i in pieces:
        for j in i:
            if j[1] in yComp:
                counted[j[1]] += 1
    filled = [row for row in counted if counted[row]>=10]
    return filled

def changePiece():
    global movingPiece, currentPiece, nextPiece
    if currentPiece == -1:
        currentPiece = randint(0,len(pieces)-1)
        nextPiece = randint(0,len(pieces)-1)
    # Make a copy of the tetris block
    # list() ensures we make a copy by value and not reference
    movingPiece = [list(part) for part in pieces[nextPiece]]
    currentPiece = nextPiece
    nextPiece = randint(0,len(pieces)-1)

# Game variables
direction = -1
# Our pieces are a list of console coordinates
# The first two coordinates are the center of the piece
# This will be important when we have to move the piece to the origin before rotation and then translate it back
pieces = [
    [[7,2],[6,2],[7,1],[8,1]],
    [[7,1],[8,1],[6,1],[5,1]],
    [[7,2],[8,2],[6,2],[6,1]],
    [[7,2],[8,2],[6,2],[8,1]],
    [[7,2],[8,2],[6,2],[7,1]],
    [[7,2],[8,2],[6,1],[7,1]],
    [[6,2],[7,2],[6,1],[7,1]]
    ]
movingPiece = []
setPieces = []

currentPiece = -1
nextPiece = -1
# 90 degree rotation matrix
rotationMatrix = ((0,1),(-1,0))
# Keep track of the time when the moving piece was last translated down
# This will be used to move the piece down after some amount of time passed
lastTime = datetime.datetime.now()
hitCount = 0
score = 0
scoreText = "SCORE"
gameOverText = "GAME OVER"
continueText = "spacebar: retry"
gameOver = False

# First piece spawned
changePiece()
while(1):
    if gameOver:
        while kbfunc() != 32:   # Wait for user to press the space bar to continue
            sleep(0.07)
        gameOver = False
        resetGame()
    # Instead of a simple sleep() that prevents any input to be read we make use of the "sleep time" to gather user input
    timeNow = datetime.datetime.now()
    while( (datetime.datetime.now() - timeNow).total_seconds() < (0.02 if direction == 0 else 0.07) ):
        setDirection()
        # Let the process sleep a little anyway so the CPU doesn't poll too frequently
        sleep(0.01)

    # Move the tetris block
    # x direction to translate the piece to
    newxDirection = 0
    if direction == 1:
        newxDirection = -1
    elif direction == 3:
        newxDirection = 1
    # Rotate if no collision occurred
    elif direction == 2 and currentPiece != 6:
        rotated = rotatePiece(movingPiece)
        rotatedHit = collisionHit(rotated)
        if not rotatedHit:
            movingPiece = rotated
    elif direction == 10:
        break               # Exit the game

    # Collision detection
    # Make a copy of the current moving piece and translate it to check for sideways collisions
    nextMove = [list(part) for part in movingPiece]

    for i in nextMove:
        i[0] += newxDirection

    hitSideways = collisionHit(nextMove)

    if not hitSideways:
        for i in movingPiece:
            i[0] += newxDirection
    else:
        # Restore nextMove because the x translation intersected with already set pieces
        nextMove = [list(part) for part in movingPiece]
        
    # Now translate the copy of the moving piece downwards to check for CD against the bottom and the pieces already set
    for i in nextMove:
        i[1] += 1

    # block-bottom CD
    hitBottom = collisionHit(nextMove)
    if hitBottom:
        hitCount += 1
    # If the CD did not hit anything, reset the hit counter so in the next frame we can continue moving the piece down
    else: hitCount = 0

    if hitCount == 4 or (hitCount and direction == 0):
        hitCount = 0
        for i in movingPiece:
            if i[1]<=2 and i[0]>4 and i[0]<8:   # Game over if the piece hit the spawn of the next one
                gameOver = True
                break
        else:
            setPieces.append(movingPiece)
            # Get a list of all the filled rows within the height of the last piece that was placed then
            # sort it to translate down in an ordered manner everything above said rows, starting from the highest (lower Y/row in console)
            filled = getFilledRows(setPieces, heightComponents(movingPiece))
            filled.sort()
            for i in filled:
                setPieces = [[sub for sub in j if sub[1] != i] for j in setPieces]                          # Delete component of setPieces if is part of a filled row
                setPieces = [[[x, y+1] if y<i else [x,y] for (x,y) in sub] for sub in setPieces if sub]     # Translate down everything that is above the deleted row
                score += 100
            changePiece()
    if not gameOver:
        # Translate the piece down if some amount of time has passed or if we are holding the down key
        if (datetime.datetime.now() - lastTime).total_seconds() > 0.5 or direction == 0:
            lastTime = datetime.datetime.now()
            # Only translate the piece down if the collision detection did not hit anything!
            if hitCount == 0:
                for i in movingPiece:
                    i[1]+= 1
        
    # Set a direction value that will not count until new user input
    direction = -1

    # Drawing   --    FULL BLOCK u"\u2588"   BLACK SQUARE u"\u25A0"     DARK SHADE u"\u2593"    LIGHT SHADE u"\u2591"
    # Our screen buffer is a list of console rows containing column characters
    sBuffer = [[u"\u2591" if j>1 and j<12 and i>0 else ' ' for j in range(screenSize[0]) ] for i in range(screenSize[1]-1)]
    # Draw moving piece
    for i in movingPiece:
        sBuffer[i[1]][i[0]] = 	u"\u2593"
    # Draw set pieces
    for i in setPieces:
        for j in i:
            sBuffer[j[1]][j[0]] = 	u"\u2593"
    # Draw game borders
    for i in range(2,screenSize[1]-1):
        sBuffer[i][1] = u"\u2502"
        sBuffer[i][12] = u"\u2502"
    # Draw score text
    for i,c in enumerate(scoreText):
        sBuffer[2][18+i] = c
    # Draw score
    scoreToStr = str(score)
    for i,c in enumerate(scoreToStr):
        xPos = 20 - (len(scoreToStr)/2) + i
        if xPos < screenSize[0]:
            sBuffer[4][xPos] = c
    # Draw next piece box
    for i in range(4):
        sBuffer[13+i][17] = u"\u2502"
        sBuffer[13+i][23] = u"\u2502"
        sBuffer[12][17] =   u"\u250C"
        sBuffer[17][17] =   u"\u2514"
        sBuffer[12][18+i] = u"\u2500"
        sBuffer[12][22] = u"\u2500"
        sBuffer[12][23] = u"\u2510"
        sBuffer[17][18+i] = u"\u2500"
        sBuffer[17][22] = u"\u2500"
        sBuffer[17][23] = u"\u2518"
    # Draw next piece
    for i in pieces[nextPiece]:
        sBuffer[i[1]+13][i[0]+13] = u"\u2593"
    # Draw game over
    if gameOver:
        for i,c in enumerate(gameOverText):
            sBuffer[7][16+i] = c
        for i,c in enumerate(continueText):
            sBuffer[9][14+i] = c
    # Display
    # Join every row in a single string to print all at once in the console
    cBuffer = ''
    for i in sBuffer:
        cBuffer += ''.join(j for j in i)
    print cBuffer