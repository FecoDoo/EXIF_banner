# %%
import math
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont, ExifTags
from pathlib import Path
from multiprocessing import Pool


# main processing function
def drawing(image_path: Path):
    name = image_path.name
    parent = image_path.parent

    img = Image.open(image_path)
    logo = Image.open(icon_path)

    # basic info
    w = img.size[0]
    h = img.size[1]

    # load fonts
    large_font_size = math.ceil(0.012 * w)
    small_font_size = math.ceil(0.010 * w)

    large_font = ImageFont.truetype(str(font_path), size=large_font_size)
    small_font = ImageFont.truetype(str(font_path), size=small_font_size)

    # transform logo
    logo_ratio = logo.size[1] / logo.size[0]

    new_logo_width = w // RATIO
    logo = logo.resize((new_logo_width, math.ceil(new_logo_width * logo_ratio)))

    # exif
    info = img.getexif()

    exif_data_dict = {}

    for k, v in info.items():
        tag = ExifTags.TAGS.get(k)
        exif_data_dict[tag] = v

    model = exif_data_dict["Model"]
    date = exif_data_dict["DateTime"].replace(":", "-", 2)

    exif_data = info.get_ifd(0x8769)

    ExposureTime = int(1 // float(exif_data.get(33434)))
    ApertureValue = exif_data.get(37378)
    FocalLength = int(exif_data.get(37386))
    iso = int(exif_data.get(34855))

    # generating new image
    new_h = (RATIO + 1) * h // RATIO
    banner_h = new_h - h

    out = Image.new(mode="RGB", size=(w, new_h))

    for i in range(w):  # for every pixel:
        for j in range(h, new_h):
            # change to black if not red
            out.putpixel((i, j), (255, 255, 255))

    # paste orignal image and logo
    out.paste(img)
    out.paste(logo, (math.ceil(0.65 * w), math.ceil(h + 0.4 * banner_h)))

    # drawing exif info
    d = ImageDraw.Draw(out)

    # drawing machine name
    d.text(
        (0.03 * w, h + 0.25 * banner_h),
        model,
        fill="black",
        font=large_font,
        align="left",
    )

    # drawing author
    d.text(
        (0.03 * w, h + 0.55 * banner_h),
        author,
        fill="grey",
        font=small_font,
        align="left",
    )

    # drawing split line
    d.line(
        (0.78 * w, h + 0.2 * banner_h, 0.78 * w, h + 0.8 * banner_h),
        fill=(220, 220, 220),
        width=5,
    )

    # drawing exif info
    d.text(
        (0.8 * w, h + 0.25 * banner_h),
        f"{FocalLength}mm f/{ApertureValue} {ExposureTime}ms ISO {iso}",
        fill="black",
        font=small_font,
        align="left",
    )
    # drawing datetime
    d.text(
        (0.8 * w, h + 0.55 * banner_h), date, fill="grey", font=small_font, align="left"
    )

    # saving
    out.save(parent.joinpath("processed", name))


# init global variables
def init_worker(f, i, r, a):
    global font_path
    global icon_path
    global RATIO
    global author
    font_path = f
    icon_path = i
    RATIO = r
    author = a


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "image_dir",
        help="directory where images are stored for processing",
        default="images",
        type=str,
    )
    parser.add_argument(
        "font",
        help="path to the disired font file (ttf)",
        default="fonts/font.ttf",
        type=str,
    )
    parser.add_argument(
        "icon",
        help="path to the disired brand icon file (jpg)",
        default="icons/icon.jpg",
        type=str,
    )
    parser.add_argument(
        "ratio",
        help="the ratio of original image versus banner (in height)",
        default=10,
        type=int,
    )
    parser.add_argument(
        "author",
        help="name of the author",
        default="Author",
        type=str,
    )
    args = parser.parse_args()

    try:
        image_dir = Path(args.image_dir)
        font_path = Path(args.font)
        icon_path = Path(args.icon)
        RATIO = int(args.ratio)
        author = args.author

        if not image_dir.exists():
            raise FileNotFoundError("image_dir does not exist")

        if not font_path.exists():
            raise FileNotFoundError("font file does not exist")

        if not icon_path.exists():
            raise FileNotFoundError("icon file does not exist")

        proc_dir = image_dir.joinpath("processed")
        proc_dir.mkdir(exist_ok=True)
        images = list(image_dir.glob("*.JPG"))

        if len(images) == 0:
            raise FileNotFoundError(
                f"no images detected under the directory of {str(image_dir)}"
            )

    except Exception as e:
        print(e)
        sys.exit()

    with Pool(
        initializer=init_worker, initargs=(font_path, icon_path, RATIO, author)
    ) as pool:
        res = pool.map(func=drawing, iterable=images)


# %%
# for k in exif_data.get_ifd(0x8769).keys():
#     print(f"{k}: {ExifTags.TAGS.get(k)}")
