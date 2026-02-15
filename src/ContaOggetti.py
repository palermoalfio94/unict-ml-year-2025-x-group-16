from PIL import Image
import os
import csv

LABELLED_PATH = "C:/tmp/etichettate"
output_csv = "C:/tmp/objects_count.csv"
idForCoco=0;
with open(output_csv, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Id","Image", "ObjectsCount"])

    for img_name in os.listdir(LABELLED_PATH):
        if img_name.endswith(".png"):
            img_path = os.path.join(LABELLED_PATH, img_name)
            img = Image.open(img_path)
            pixels = list(img.getdata())
            pixels = [p for p in pixels if p != (0,0,0,255)]  # escludo sfondo
            unique_colors = set(pixels)
           
            writer.writerow([idForCoco,img_name.replace("_label",""), len(unique_colors)])
            idForCoco=idForCoco+1;
