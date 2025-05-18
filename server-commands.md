# SERVER COMMANDS CHEAT SHEET


## SET MIN/MID/MAX STEER/SPEED
btw it sets the speed/steer for all boards

cmdId 0

0 [speedOption] [steerOption]

both options work as follows:

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

cornervalue = <-1000, 1000>

*cornerValue must be positive or the controls will be flipped!!*

The program sets the steer/speed values like this:

steerValues = (cornerValue, 0, -cornerValue)

## SETTING SPEED/STEER USING JOYSTICK VALUES

cmdId 4

4 [speedPercentage] [steerPercentage]

The values must be between 0 and 100


## STARTING CAM LIVE STREAM

cmdId 5

no other arguments needed

## CHANGING CAMERA

cmdId 6

6 [camID]

camID must be present in a list of some sort, that I need to create...