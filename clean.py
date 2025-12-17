from PIL import Image
from collections import Counter
import os
import math


flagsource='testflags'
flagdest='cleanflags'
numcolors=9

index=0
for filename in os.listdir(flagsource):
    index+=1
    print(index)
    if filename==".DS_Store":
        continue
    with Image.open(os.path.join(flagsource, filename)).convert('RGB') as img: # open in readonly mode
        size=img.size
        pixels = list(img.getdata())  # List of all (R, G, B) tuples
        color_counts = [(v,k) for k,v in Counter(pixels).items()]
        color_counts.sort(reverse=True)
        palette=[e[1] for e in color_counts[:numcolors]]
        
        
        cleanPixels=pixels[0:1]
        for p in pixels[1:]:
            if p in palette:
                cleanPixels.append(p)
            else:
                cleanPixels.append(cleanPixels[-1])
            
        
        cleanImg = Image.new("RGB", size)
        cleanImg.putdata(cleanPixels)
        
        # Save or show the image
        cleanImg.save(os.path.join(flagdest, filename))


