#fixed size headers for socket communication to differentiate types of data being sent
#lze použít všechny hodnoty 0-127 včetně, jinak to dělá problémy :) 
#Nah už se může používat 0-255, já mega smartaas jse mto zpravil

HEADERS = {
    "CMD": (0).to_bytes(1, byteorder='big'),
    "IMG": (1).to_bytes(1, byteorder='big'),
    "STATUS": (2).to_bytes(1, byteorder='big'),
    "IMG_SIZE": (3).to_bytes(1, byteorder='big'),
    
}