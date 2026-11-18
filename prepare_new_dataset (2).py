import os
import shutil
import random
import xml.etree.ElementTree as ET

# -----------------------------
# SETTINGS
# -----------------------------
SOURCE_DIR = "new_dataset"
OUTPUT_DIR = "dataset_new"

TRAIN_RATIO = 0.8
CLASS_NAME = "potholes"
CLASS_ID = 0

random.seed(42)

# -----------------------------
# CREATE FOLDERS
# -----------------------------
for folder in [
    "images/train",
    "images/val",
    "labels/train",
    "labels/val"
]:
    os.makedirs(os.path.join(OUTPUT_DIR, folder), exist_ok=True)

# -----------------------------
# FIND IMAGES
# -----------------------------
images = [
    f for f in os.listdir(SOURCE_DIR)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
]

random.shuffle(images)

train_count = int(len(images) * TRAIN_RATIO)

train_images = images[:train_count]
val_images = images[train_count:]

print(f"Total images: {len(images)}")
print(f"Training images: {len(train_images)}")
print(f"Validation images: {len(val_images)}")


# -----------------------------
# XML → YOLO
# -----------------------------
def convert_xml_to_yolo(xml_path, image_width, image_height):

    tree = ET.parse(xml_path)
    root = tree.getroot()

    yolo_lines = []

    for obj in root.findall("object"):

        name = obj.find("name").text.strip().lower()

        if name != CLASS_NAME:
            continue

        box = obj.find("bndbox")

        xmin = float(box.find("xmin").text)
        ymin = float(box.find("ymin").text)
        xmax = float(box.find("xmax").text)
        ymax = float(box.find("ymax").text)

        # Convert Pascal VOC → YOLO
        x_center = ((xmin + xmax) / 2) / image_width
        y_center = ((ymin + ymax) / 2) / image_height

        width = (xmax - xmin) / image_width
        height = (ymax - ymin) / image_height

        yolo_lines.append(
            f"{CLASS_ID} "
            f"{x_center:.6f} "
            f"{y_center:.6f} "
            f"{width:.6f} "
            f"{height:.6f}"
        )

    return yolo_lines


# -----------------------------
# PROCESS DATASET
# -----------------------------
def process_images(image_list, split):

    for image_name in image_list:

        image_path = os.path.join(SOURCE_DIR, image_name)

        xml_name = os.path.splitext(image_name)[0] + ".xml"
        xml_path = os.path.join(SOURCE_DIR, xml_name)

        # Skip images without XML
        if not os.path.exists(xml_path):
            print(f"WARNING: Missing XML: {image_name}")
            continue

        # Read image dimensions from XML
        tree = ET.parse(xml_path)
        root = tree.getroot()

        size = root.find("size")

        image_width = int(size.find("width").text)
        image_height = int(size.find("height").text)

        # Convert annotation
        yolo_lines = convert_xml_to_yolo(
            xml_path,
            image_width,
            image_height
        )

        # Destination paths
        output_image = os.path.join(
            OUTPUT_DIR,
            "images",
            split,
            image_name
        )

        label_name = os.path.splitext(image_name)[0] + ".txt"

        output_label = os.path.join(
            OUTPUT_DIR,
            "labels",
            split,
            label_name
        )

        # Copy image
        shutil.copy2(image_path, output_image)

        # Save YOLO label
        with open(output_label, "w") as f:
            f.write("\n".join(yolo_lines))


process_images(train_images, "train")
process_images(val_images, "val")


# -----------------------------
# CREATE data.yaml
# -----------------------------
yaml_content = f"""path: {os.path.abspath(OUTPUT_DIR).replace(chr(92), '/')}
train: images/train
val: images/val

names:
  0: pothole
"""

with open(os.path.join(OUTPUT_DIR, "data.yaml"), "w") as f:
    f.write(yaml_content)

print("\nDataset preparation complete!")
print(f"Dataset created at: {os.path.abspath(OUTPUT_DIR)}")