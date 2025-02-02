#fixed size headers for socket communication to differentiate types of data being sent
#lze použít všechny hodnoty 0-127 včetně, jinak to dělá problémy :) 
#Nah už se může používat 0-255, já mega smartaas jse mto zpravil

HEADERS = {
    "CMD": 0,
    "IMG": 1,
    "STATUS": 2,
    "IMG_SIZE": 3,
    "IMG_DECODED": 4
}