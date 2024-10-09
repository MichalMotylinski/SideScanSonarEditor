import json
import os
from PIL import Image, ImageDraw
from processing.xtf_to_image import * 
from shutil import rmtree, copyfile
import pickle
import time
import cv2

"""with open("test_file_list_10.txt", "r") as f:
    data = f.readlines()

print(', '.join(['"'+ x.strip() + '"' for x in data]))"""
#print([x.strip() for x in data])
test_files = ["SSS_MS_M13405_RAW_jsf-CH34.json", "SSS_MS_M13406_RAW_jsf-CH34.json", "SSS_MS_M13408_RAW_jsf-CH34.json", "SSS_MS_M13409_RAW_jsf-CH34.json", "SSS_MS_M13411_RAW_jsf-CH34.json",
              "SSS_MS_M13412_RAW_jsf-CH34.json", "te_a100h_xtf-ch12.json", "te_a101h_xtf-ch12.json", "te_a102.001h_xtf-ch12.json", "te_a102h_xtf-ch12.json",
              "te_a103h_xtf-ch12.json", "te_a104h_xtf-ch12.json", "te_a105.001h_xtf-ch12.json", "te_a105h_xtf-ch12.json", "te_a106h_xtf-ch12.json",
              "te_a107h_xtf-ch12.json", "te_a108h_xtf-ch12.json", "te_a109h_xtf-ch12.json", "te_a10h_xtf-ch12.json", "te_a110h_xtf-ch12.json",
              "te_a111h_xtf-ch12.json", "te_a112h_xtf-ch12.json", "te_a113h_xtf-ch12.json", "te_a114h_xtf-ch12.json", "te_a115h_xtf-ch12.json",
              "te_a116ah_xtf-ch12.json", "te_a117h_xtf-ch12.json", "A4-A5_IS_25_A_jsf-CH34.json", "A4-A5_IS_X02_jsf-CH34.json", "A_65_Rev01_jsf-CH34.json",
              "A_CL_Rev03_jsf-CH34.json", "B_-25_jsf-CH34.json", "B_65.001_jsf-CH34-to-B_65_jsf-CH34.json", "B_65_SSS_.001_jsf-CH34-to-B_65_SSS__jsf-CH34.json"]

valid_files = ["SSS_MS_I13357_RAW_jsf-CH34-SPL000.json", "SSS_MS_I13429_RAW_jsf-CH34.json", "SSS_MS_I13430_RAW_jsf-CH34.json", "SSS_MS_I13432_RAW_jsf-CH34.json", "SSS_MS_I13438_RAW_jsf-CH34.json",
               "SSS_MS_I13440_RAW_jsf-CH34.json", "SSS_MS_M13353A_RAW_jsf-CH34.json", "SSS_MS_M13353_RAW_jsf-CH34.json", "SSS_MS_M13354_RAW_jsf-CH34.json", "SSS_MS_M13355_RAW_jsf-CH34.json",
               "SSS_MS_M13391_RAW_jsf-CH34.json", "SSS_MS_M13403_RAW_jsf-CH34.json", "te_a117.001h_xtf-ch12.json", "te_a118h_xtf-ch12.json", "te_a119h_xtf-ch12.json",
               "te_a120h_xtf-ch12.json", "te_a121h_xtf-ch12.json", "te_a122h_xtf-ch12.json", "te_a123.001h_xtf-ch12.json", "te_a123h_xtf-ch12.json",
               "te_a124h_xtf-ch12.json", "te_a125h_xtf-ch12.json", "te_a126h_xtf-ch12.json", "te_a127.001h_xtf-ch12.json", "te_a127h_xtf-ch12.json",
               "te_a128h_xtf-ch12.json", "te_a129h_xtf-ch12.json", "te_a130h_xtf-ch12.json", "te_b11h_xtf-ch12.json", "te_b12h_xtf-ch12.json",
               "te_b13h_xtf-ch12.json", "te_b14h_xtf-ch12.json", "te_b15h_xtf-ch12.json", "te_b16h_xtf-ch12.json", "te_b17h_xtf-ch12.json",
               "te_b18h_xtf-ch12.json", "te_b19ah_xtf-ch12.json", "te_b1h_xtf-ch12.json", "te_b20h_xtf-ch12.json", "te_b21h_xtf-ch12.json",
               "te_b22h_xtf-ch12.json", "te_b2h_xtf-ch12.json", "te_b3ah_xtf-ch12.json", "te_b3h_xtf-ch12.json", "te_b4h_xtf-ch12.json",
               "te_b5h_xtf-ch12.json", "te_b6h_xtf-ch12.json", "te_b8h_xtf-ch12.json", "te_b9h_xtf-ch12.json", "A4-A5_IS_-145_jsf-CH34.json",
               "A4-A5_IS_185_jsf-CH34.json", "A4-A5_IS_X03_jsf-CH34.json", "A_-250_Rev01_jsf-CH34.json", "A_-65_Rev01-U_jsf-CH34.json", "A_190_Rev01_jsf-CH34.json",
               "A_250_Rev01_jsf-CH34.json", "B_-25.001_jsf-CH34.json"]

test_files = ["SSS_MS_M13408_RAW_jsf-CH34.json", "SSS_MS_M13409_RAW_jsf-CH34.json", "SSS_MS_M13412_RAW_jsf-CH34.json", "te_a103h_xtf-ch12.json", 
              "te_a104h_xtf-ch12.json", "te_a106h_xtf-ch12.json", "te_a107h_xtf-ch12.json", "te_a108h_xtf-ch12.json", 
              "te_a109h_xtf-ch12.json", "A4-A5_IS_25_A_jsf-CH34.json", "A_CL_Rev03_jsf-CH34.json", "B_-25_jsf-CH34.json", "B_65.001_jsf-CH34-to-B_65_jsf-CH34.json"]
valid_files = ["SSS_MS_I13357_RAW_jsf-CH34-SPL000.json", "SSS_MS_I13429_RAW_jsf-CH34.json", "SSS_MS_I13430_RAW_jsf-CH34.json", "SSS_MS_I13432_RAW_jsf-CH34.json", 
               "SSS_MS_I13438_RAW_jsf-CH34.json", "SSS_MS_M13354_RAW_jsf-CH34.json", "SSS_MS_M13391_RAW_jsf-CH34.json", "te_a118h_xtf-ch12.json", 
               "te_a119h_xtf-ch12.json", "te_a120h_xtf-ch12.json", "te_a121h_xtf-ch12.json", "te_a122h_xtf-ch12.json", 
               "te_a123.001h_xtf-ch12.json", "te_a123h_xtf-ch12.json", "te_a125h_xtf-ch12.json", "te_a126h_xtf-ch12.json", 
               "te_a127h_xtf-ch12.json", "te_a128h_xtf-ch12.json", "te_a130h_xtf-ch12.json", "A4-A5_IS_-145_jsf-CH34.json", 
               "A_190_Rev01_jsf-CH34.json", "A_250_Rev01_jsf-CH34.json", "B_-25.001_jsf-CH34.json"]

def draw_masks(path, anns, filename):
    # Create RGB image with an object mask displayed
    grayscale_img = cv2.imread(os.path.join(path, "images", filename), cv2.IMREAD_GRAYSCALE)
    rgb_img = cv2.cvtColor(grayscale_img, cv2.COLOR_GRAY2RGB)
    print(anns)
    masks = []
    for polygon_points in anns:
        mask = np.zeros_like(rgb_img)
        cv2.fillPoly(mask, np.int32([[[int(polygon_points[i]), int(polygon_points[i+1])] for i in range(0, len(polygon_points), 2)]]), (255, 0, 255))
        masks.append(mask)
    
    # Apply transparency to each mask and overlay it on the original image
    alpha = 0.5  # Transparency factor (0: fully transparent, 1: fully opaque)
    for mask in masks:
        overlay = np.uint8(mask * alpha)
        rgb_img = cv2.addWeighted(rgb_img, 1, overlay, 1 - alpha, 0)
    cv2.imwrite(os.path.join(path, "color", filename), rgb_img)


train_images = []
valid_images = []
test_images = []
train_annotations = []
valid_annotations = []
test_annotations = []
train_image_idx = 0
valid_image_idx = 0
test_image_idx = 0
train_ann_idx = 0
valid_ann_idx = 0
test_ann_idx = 0

decimation = 1
auto_stretch = False
stretch = 1
shift = 0
compute_bac = False

dataset_dir = "sss_dataset"
if os.path.exists(dataset_dir):
    rmtree(dataset_dir)
os.mkdir(dataset_dir)
for i in ["train", "valid", "test"]:
    os.makedirs(os.path.join(dataset_dir, i, "images"))
    os.makedirs(os.path.join(dataset_dir, i, "data"))
    os.makedirs(os.path.join(dataset_dir, i, "color"))

input_dir = "processed_tagged"

files = []
for dir in sorted(os.listdir(input_dir)):
    for file in sorted(os.listdir(os.path.join(input_dir, dir, "Proc XTF - No Gains"))):
        if ".xtf" in file or "labels" in file or "tiles" in file or "BAC" in file:
            continue
        files.append(os.path.join(input_dir, dir, "Proc XTF - No Gains", file))

train_data = {}
valid_data = {}
test_data = {}
kkk=0
start = time.perf_counter()
stretches = []
for input_filename in files:
    print(input_filename)
    #if "Barnegat" in input_filename:
        #if kkk > 10:
            #continue

    #####################################################################################
    # Load xtf data
    #####################################################################################
    xtf_filename = f"{input_filename.rsplit('.', 1)[0]}.xtf"
    port_data,starboard_data,coords,splits,stretch,packet_size,full_image_height,full_image_width,accross_interval,along_interval = read_xtf(xtf_filename, 0, decimation, auto_stretch, stretch, shift, compute_bac)
    stretches.append(stretch)
    stretch = 1
    port_data = np.fliplr(port_data)

    gs_min = 0
    gs_max = 255

    upper_limit = 2 ** 14
    #port_data.clip(0, upper_limit-1, out=port_data)
    #starboard_data.clip(0, upper_limit-1, out=starboard_data)

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

    # Normalize data to obtain an image
    """mean_intensity = np.mean(port_data)
    # Bring the intensity values closer to the mean
    compression_factor = 0.9 # Adjust this factor to control how close to the mean you want to bring the values
    port_data = mean_intensity + compression_factor * (port_data- mean_intensity)
    # Normalize data to obtain an image
    mean_intensity = np.mean(starboard_data)
    # Bring the intensity values closer to the mean
    compression_factor = 0.9 # Adjust this factor to control how close to the mean you want to bring the values
    starboard_data = mean_intensity + compression_factor * (starboard_data- mean_intensity)"""

    #####################################################################################

    # Load annotations file
    with open(input_filename, "r") as f:
        data = json.load(f)
        #if image_idx == 0:
        #    base_data = data
        
        for image_anns in data["images"]:
            xmin, ymin, width, height = image_anns["rectangle"]
            xmax = int(xmin + width)
            ymax = int(ymin + height)
            xmin = int(xmin)
            ymin = int(ymin)
            
            # Load port and starboard data
            if image_anns["side"] == "port":
                tile = port_data[ymin:ymax, xmin:xmax]
                channel_min = port_min
                scale = port_scale
            else:
                tile = starboard_data[ymin:ymax, xmin - starboard_data.shape[1]:xmax - starboard_data.shape[1]]
                channel_min = starboard_min
                scale = starboard_scale
            
            raw_data = tile

            
            channel = np.log10(tile + 0.00001, dtype=np.float32)
            channel = np.subtract(channel, channel_min)
            channel = np.multiply(channel, scale)
            channel = np.add(gs_min, channel)
            print(channel[0, :10])
            #channel = np.subtract(gs_max, channel)
            #if "Barnegat" in input_filename:
                #channel = np.add(gs_min, channel)
                #kkk+=1
            #else:
                #channel = np.subtract(gs_max, channel)
            img_anns = []
            for annotation_data1 in data["annotations"]:
                annotation_data = annotation_data1.copy()
                # Filter out all classes but the Boulder
                if annotation_data["category_id"] != 5:
                    continue
                if annotation_data["image_id"] - 1 != image_anns["id"]:
                    continue
                if input_filename.rsplit("/")[-1] in test_files:
                    annotation_data["id"] = test_ann_idx
                    annotation_data["image_id"] = test_image_idx
                    test_ann_idx += 1
                elif input_filename.rsplit("/")[-1] in valid_files:
                    annotation_data["id"] = valid_ann_idx
                    annotation_data["image_id"] = valid_image_idx
                    valid_ann_idx += 1
                else:
                    annotation_data["id"] = train_ann_idx
                    annotation_data["image_id"] = train_image_idx
                    train_ann_idx += 1

                if input_filename.rsplit("/")[-1] in test_files:
                    test_annotations.append(annotation_data)
                elif input_filename.rsplit("/")[-1] in valid_files:
                    valid_annotations.append(annotation_data)
                else:
                    train_annotations.append(annotation_data)

                
                seg = []
                # Convert to COCO segmentation format and flip annotations if port side
                for i, val in enumerate(annotation_data["segmentation"]):
                    if not i % 2:
                        if image_anns["side"] == "port":
                            seg.append(128-val)
                        else:
                            seg.append(val)
                    else:
                        seg.append(val)
                annotation_data["segmentation"] = seg
                img_anns.append(seg)

            
            
            # Add data to dataset
            print(input_filename.rsplit("/")[-1])
            if input_filename.rsplit("/")[-1] in test_files:
                with open(os.path.join(dataset_dir, "test", "data", f"{str(test_image_idx).zfill(5)}.pickle"), "wb") as f:
                    pickle.dump(raw_data, f)
                cv2.imwrite(os.path.join(dataset_dir, "test", "images", f"{str(test_image_idx).zfill(5)}.png"), channel)
                image_anns["id"] = test_image_idx
                image_anns["file_name"] = f"{str(test_image_idx).zfill(5)}.png"
                test_images.append(image_anns)
                draw_masks(os.path.join(dataset_dir, "test"), img_anns, f"{str(test_image_idx).zfill(5)}.png")
                test_image_idx += 1
            elif input_filename.rsplit("/")[-1] in valid_files:
                with open(os.path.join(dataset_dir, "valid", "data", f"{str(valid_image_idx).zfill(5)}.pickle"), "wb") as f:
                    pickle.dump(raw_data, f)
                cv2.imwrite(os.path.join(dataset_dir, "valid", "images", f"{str(valid_image_idx).zfill(5)}.png"), channel)
                image_anns["id"] = valid_image_idx
                image_anns["file_name"] = f"{str(valid_image_idx).zfill(5)}.png"
                valid_images.append(image_anns)
                draw_masks(os.path.join(dataset_dir, "valid"), img_anns, f"{str(valid_image_idx).zfill(5)}.png")
                valid_image_idx += 1
            else:
                with open(os.path.join(dataset_dir, "train", "data", f"{str(train_image_idx).zfill(5)}.pickle"), "wb") as f:
                    pickle.dump(raw_data, f)
                cv2.imwrite(os.path.join(dataset_dir, "train", "images", f"{str(train_image_idx).zfill(5)}.png"), channel)
                image_anns["id"] = train_image_idx
                image_anns["file_name"] = f"{str(train_image_idx).zfill(5)}.png"
                train_images.append(image_anns)
                draw_masks(os.path.join(dataset_dir, "train"), img_anns, f"{str(train_image_idx).zfill(5)}.png")
                train_image_idx += 1

train_data["images"] = train_images
train_data["annotations"] = train_annotations
with open(os.path.join(dataset_dir, "train", "annotations.json"), "w") as f:
    json.dump(train_data, f, indent=4)

valid_data["images"] = valid_images
valid_data["annotations"] = valid_annotations
with open(os.path.join(dataset_dir, "valid", "annotations.json"), "w") as f:
    json.dump(valid_data, f, indent=4)

test_data["images"] = test_images
test_data["annotations"] = test_annotations
with open(os.path.join(dataset_dir, "test", "annotations.json"), "w") as f:
    json.dump(test_data, f, indent=4)

end = time.perf_counter()

print(min(stretches), max(stretches))
print(end-start)