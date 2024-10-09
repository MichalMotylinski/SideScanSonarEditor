import json
import os
from PIL import Image, ImageDraw
from processing.xtf_to_image import * 
from shutil import rmtree, copyfile
import pickle
import time
import cv2

images = []
annotations = []
image_idx = 0
ann_idx = 0

decimation = 1
auto_stretch = False
stretch = 1
shift = 0
compute_bac = False

dataset_dir = "sss_dataset"
if os.path.exists(dataset_dir):
    rmtree(dataset_dir)
os.mkdir(dataset_dir)
os.mkdir(os.path.join(dataset_dir, "images"))
os.mkdir(os.path.join(dataset_dir, "data"))
os.mkdir(os.path.join(dataset_dir, "color"))

input_dir = "processed_tagged"
input_filepath = "processed_tagged/Erebus/Proc XTF - No Gains"
#input_filepath = "Proc XTF - Gains"
input_filename = "te_a35h_xtf-ch12.xtf"

files = []#sorted(os.listdir(input_filepath))
for dir in sorted(os.listdir(input_dir)):
    for file in sorted(os.listdir(os.path.join(input_dir, dir, "Proc XTF - No Gains"))):
        if ".xtf" in file or "labels" in file or "tiles" in file or "BAC" in file:
            continue
        files.append(os.path.join(input_dir, dir, "Proc XTF - No Gains", file))

base_data = 0
#for file in files:
    #print(file)

start = time.perf_counter()
stretches = []
for input_filename in files:
    

    #if "a160h" not in input_filename:
    #    continue
    xtf_filename = f"{input_filename.rsplit('.', 1)[0]}.xtf"
    
    port_data,starboard_data,coords,splits,stretch,packet_size,full_image_height,full_image_width,accross_interval,along_interval = read_xtf(xtf_filename, 0, decimation, auto_stretch, stretch, shift, compute_bac)
    print(input_filename, port_data.shape,starboard_data.shape, stretch)
    stretches.append(stretch)
    stretch = 1
    port_data = np.fliplr(port_data)

    gs_min = 0
    gs_max = 255

    port_min = port_data.min()
    port_max = port_data.max()
    starboard_min = starboard_data.min()
    starboard_max = starboard_data.max()

    if port_min > 0:
        port_min = math.log10(port_min)
    else:
        port_min = 0
    if port_max > 0:
        port_max = math.log10(port_max)
    else:
        port_max = 0

    if starboard_min > 0:
        starboard_min = math.log10(starboard_min)
    else:
        starboard_min = 0
    if starboard_max > 0:
        starboard_max = math.log10(starboard_max)
    else:
        starboard_max = 0

    if (port_max - port_min) != 0:
        port_scale = (gs_max - gs_min) / (port_max - port_min)
    
    if (starboard_max - starboard_min) != 0:
        starboard_scale = (gs_max - gs_min) / (starboard_max - starboard_min)

    """port_channel = np.log10(port_data + 0.00001, dtype=np.float32)
    port_channel = np.subtract(port_channel, port_min)
    port_channel = np.multiply(port_channel, port_scale)
    port_channel = np.add(gs_min, port_channel)

    starboard_channel = np.log10(starboard_data + 0.00001, dtype=np.float32)
    starboard_channel = np.subtract(starboard_channel, starboard_min)
    starboard_channel = np.multiply(starboard_channel, starboard_scale)
    starboard_channel = np.add(gs_min, starboard_channel)"""

    """channel = np.concatenate([port_channel[::-1], starboard_channel], axis=1)

    image = Image.fromarray(channel).convert('L')

    image.save("check_image.png")
    cv2.imwrite("check_image1.png", channel)"""

    with open(input_filename, "r") as f:
        data = json.load(f)
        if image_idx == 0:
            base_data = data
        
        img_ids = {}
        
        for image_data in data["images"]:
            xmin, ymin, width, height = image_data["rectangle"]
            #xmin = port_data.shape[1] - xmin
            xmax = int(xmin + width)
            ymax = int(ymin + height)
            xmin = int(xmin)
            ymin = int(ymin)
            
            if image_data["side"] == "port":
                tile = port_data[ymin:ymax, xmin:xmax]
                channel_min = port_min
                scale = port_scale
            else:
                tile = starboard_data[ymin:ymax, xmin - starboard_data.shape[1]:xmax - starboard_data.shape[1]]
                channel_min = starboard_min
                scale = starboard_scale
            
            with open(os.path.join(dataset_dir, "data", f"{str(image_idx).zfill(5)}.pickle"), "wb") as f:
                pickle.dump(tile, f)

            #channel = np.log(tile)
            channel = np.log10(tile + 0.00001, dtype=np.float32)

            channel = np.subtract(channel, channel_min)
            channel = np.multiply(channel, scale)

            #channel = np.subtract(gs_max, channel)
            channel = np.add(gs_min, channel)

            #image = Image.fromarray(channel)
            #if image_data["side"] == "port":
                #image = image.transpose(Image.FLIP_LEFT_RIGHT)
            #image.convert('L').save(os.path.join(dataset_dir, "images", f"{str(image_idx).zfill(5)}.png"))
            #channel = cv2.GaussianBlur(channel, (1,1), 0)
            #channel = cv2.medianBlur(channel, 3)
            #channel = cv2.bilateralFilter(channel, 10, 75, 75)
            #channel = cv2.Laplacian(channel.astype(np.uint8), cv2.CV_64F)
            #channel = cv2.cvtColor(channel.astype(np.uint8), cv2.COLOR_GRAY2BGR)
            #channel = cv2.fastNlMeansDenoisingColored(channel, None, 10, 10, 7, 21)

            cv2.imwrite(os.path.join(dataset_dir, "images", f"{str(image_idx).zfill(5)}.png"), channel)
            grayscale_img = cv2.imread(os.path.join(dataset_dir, "images", f"{str(image_idx).zfill(5)}.png"), cv2.IMREAD_GRAYSCALE)
            rgb_img = cv2.cvtColor(grayscale_img, cv2.COLOR_GRAY2RGB)
    
            """rgb_img = []
            for row in rgb_img1:
                rgb_img.append(row)
                rgb_img.append(row)
            rgb_img = np.array(rgb_img)"""
            
            #if image_idx == 484:
            #    print("DSSD",input_filename)
            polygons = []
            
            img_ids[image_data["id"]] = image_idx
            #print("IMG", image_idx)
            for annotation_data1 in data["annotations"]:
                annotation_data = annotation_data1.copy()
                if annotation_data["category_id"] != 5:
                    continue
                #if annotation_data["image_id"]
                if annotation_data["image_id"] - 1 != image_data["id"]:
                    continue
                annotation_data["id"] = ann_idx
                annotation_data["image_id"] = image_idx#img_ids[annotation_data["image_id"] - 1]

                annotations.append(annotation_data)
                #print("ANN", ann_idx)
                #print(annotation_data)
                #print(annotations)
                ann_idx += 1
                seg = []
                for i, val in enumerate(annotation_data["segmentation"]):
                    if not i % 2:
                        if image_data["side"] == "port":
                            seg.append(128-val)
                        else:
                            seg.append(val)
                    else:
                        seg.append(val)
                polygons.append(seg)
                annotation_data["segmentation"] = seg
                #polygons.append(annotation_data["segmentation"])

            masks = []
            for polygon_points in polygons:
                mask = np.zeros_like(rgb_img)
                cv2.fillPoly(mask, np.int32([[[int(polygon_points[i]), int(polygon_points[i+1])] for i in range(0, len(polygon_points), 2)]]), (255, 0, 255))
                masks.append(mask)
            
            # Apply transparency to each mask and overlay it on the original image
            alpha = 0.5  # Transparency factor (0: fully transparent, 1: fully opaque)
            for mask in masks:
                overlay = np.uint8(mask * alpha)
                rgb_img = cv2.addWeighted(rgb_img, 1, overlay, 1 - alpha, 0)

            cv2.imwrite(os.path.join(dataset_dir, "color", f"{str(image_idx).zfill(5)}.png"), rgb_img)
            

            image_data["id"] = image_idx
            image_data["file_name"] = f"{str(image_idx).zfill(5)}.png"

            images.append(image_data)

            #print(f"{str(image_idx).zfill(5)}.png - {image_data['side']}" )

            image_idx += 1


base_data["images"] = images
base_data["annotations"] = annotations
#print(base_data)
with open(os.path.join(dataset_dir, "annotations.json"), "w") as f:
    json.dump(base_data, f, indent=4)
end = time.perf_counter()

print(min(stretches), max(stretches))
print(end-start)
"""for image_data in data["images"]:
    xmin, ymin, width, height = image_data["rectangle"]
    xmax = int(xmin + width)
    ymax = int(ymin + height)
    xmin = int(xmin)
    ymin = int(ymin)
    print(port_data.shape, xmin, ymin, ymin,ymax)
    if image_data["side"] == "port":
        tile = port_data[ymin:ymax, xmin:xmax]
    else:
        tile = starboard_data[ymin:ymax, xmin:xmax]

    channel = np.log(tile)

    channel = np.subtract(channel, channel_min)
    channel = np.multiply(channel, scale)

    channel = np.subtract(gs_max, channel)

    image = Image.fromarray(channel)

    for annotation_data in data["annotations"]:
        if annotation_data["image_id"] != image_data["id"]:
            continue
        xmin, ymin, width, height = annotation_data["bbox"]

        img1 = ImageDraw.Draw(image)  
        img1.rectangle([xmin, ymin, xmin+width, ymin+height], fill ="#ffff33", outline ="red")
        image.convert('L').save(os.path.join(dataset_dir, f"{str(image_data['id'])}.png"))
"""