# SERVER COMMANDS CHEAT SHEET


## SET MIN/MID/MAX STEER/SPEED
btw it sets the speed/steer for all boards

cmdId 0

0 [speedOption] [steerOption]

both optiona work as follows:

-1 = minimum value
0 = middle value
1 = maximum value

## PRINT BOARD FEEDBACK (DOESN'T WORK)

cmdId 1

## ESTOP

cmdId 2

no other arguments needed

## CHANGING DEFAULT STEER/SPEED VALUES

cmdId 3 

3 [cornerValue]


*cornerValue must be positive or the controls will be flipped!!*

The program sets the steer/speed values like this:

steerValues = (cornerValue, 0, -cornerValue)

## SETTING SPEED/STEER USING JOYSTICK VALUES

cmdId 4

4 [speedPercentage] [steerPercentage]

The