# %%
import math
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont, ExifTags
from pathlib import Path
from multiprocessing import Pool


# main processing function
def drawing(image_path: Path):
    # detecting image path
    name = image_path.name
    parent = image_path.parents[1]
    
    try:
        # loading image and camera brand
        img = Image.open(image_path)
        logo = Image.open(icon_path)

        # loading image shape
        w = img.size[0]
        h = img.size[1]

        # loading fonts
        large_font_size = math.ceil(0.012 * w)
        small_font_size = math.ceil(0.010 * w)

        large_font = ImageFont.truetype(str(font_path), size=large_font_size)
        small_font = ImageFont.truetype(str(font_path), size=small_font_size)

        # resizing logo
        logo_ratio = logo.size[1] / logo.size[0]
        new_logo_width = w // Ratio
        logo = logo.resize((new_logo_width, math.ceil(new_logo_width * logo_ratio)))

        # EXIF
        info = img.getexif()

        # load camera model info
        exif_data_dict = {}

        for k, v in info.items():
            tag = ExifTags.TAGS.get(k)
            exif_data_dict[tag] = v
        model = exif_data_dict["Model"]

        # load EXIF info
        exif_data = info.get_ifd(0x8769)
        Date = exif_data.get(36867).replace(":", "-", 2)
        ExposureTime = int(1 // float(exif_data.get(33434)))
        ApertureValue = round(int(exif_data.get(37378)), 2)
        FocalLength = int(exif_data.get(37386))
        Lens = exif_data.get(42036)
        iso = int(exif_data.get(34855))

        # generating new image
        new_h = (Ratio + 1) * h // Ratio
        banner_h = new_h - h

        out = Image.new(mode="RGB", size=(w, new_h))

        for i in range(w):  # for every pixel:
            for j in range(h, new_h):
                # change to black if not red
                out.putpixel((i, j), (255, 255, 255))

        # pasting orignal image
        out.paste(img)
        # adding camera brand
        out.paste(logo, (math.ceil(0.65 * w), math.ceil(h + 0.4 * banner_h)))

        # adding EXIF info
        d = ImageDraw.Draw(out)

        # adding camera name
        d.text(
            (0.03 * w, h + 0.25 * banner_h),
            model,
            fill="black",
            font=large_font,
            align="left",
        )

        # adding author name
        d.text(
            (0.03 * w, h + 0.55 * banner_h),
            Author,
            fill="grey",
            font=small_font,
            align="left",
        )

        # adding description
        d.text(
            (0.2 * w, h + 0.3 * banner_h),
            Description,
            fill="grey",
            font=small_font,
            align="left",
        )

        # adding split line
        d.line(
            (0.78 * w, h + 0.2 * banner_h, 0.78 * w, h + 0.8 * banner_h),
            fill=(220, 220, 220),
            width=5,
        )

        # adding exif info
        d.text(
            (0.8 * w, h + 0.25 * banner_h),
            f"{FocalLength}mm  f/{ApertureValue}  {ExposureTime}ms  ISO {iso}",
            fill="black",
            font=small_font,
            align="left",
        )
        # adding datetime
        d.text(
            (0.8 * w, h + 0.55 * banner_h), Date, fill="grey", font=small_font, align="left"
        )

        # saving image
        out.save(parent.joinpath("processed", name))
    
    except Exception as e:
        print(f"{name}: {e}")


# init global variables
def init_worker(f, i, r, a, d):
    global font_path
    global icon_path
    global Ratio
    global Author
    global Description
    font_path = f
    icon_path = i
    Ratio = r
    Author = a
    Description = d


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "image_dir",
        help="directory where images are stored for processing",
        default="images",
        type=str,
    )
    parser.add_argument(
        "author",
        help="name of the author",
        default="Author",
        type=str,
    )
    parser.add_argument(
        "-d",
        help="Description",
        default="",
        type=str,
    )
    parser.add_argument(
        "-f",
        help="path to the disired font file (ttf)",
        default="fonts/font.ttf",
        type=str,
    )
    parser.add_argument(
        "-i",
        help="path to the disired brand icon file (jpg)",
        default="icons/icon.jpg",
        type=str,
    )
    parser.add_argument(
        "-r",
        help="the ratio of original image versus banner (in height)",
        default=10,
        type=int,
    )
    args = parser.parse_args()

    try:
        # load args
        image_dir = Path(args.image_dir)
        Author = args.author
        Description = args.d
        font_path = Path(args.f)
        icon_path = Path(args.i)
        Ratio = int(args.r)

        # create directories if not exist
        if not image_dir.exists():
            raise FileNotFoundError("image_dir does not exist")

        if not font_path.exists():
            raise FileNotFoundError("font file does not exist")

        if not icon_path.exists():
            raise FileNotFoundError("icon file does not exist")

        proc_dir = Path(sys.path[0]).joinpath("processed")
        proc_dir.mkdir(exist_ok=True)

        # detect jpg files under the given image_dir
        images = list(image_dir.glob("*.jpg"))

        if len(images) == 0:
            raise FileNotFoundError(
                f"no images detected under the directory of {str(image_dir)}, only jpg format is supported."
            )

    except Exception as e:
        print(e)
        sys.exit()

    # start processing
    with Pool(
        initializer=init_worker,
        initargs=(font_path, icon_path, Ratio, Author, Description),
    ) as pool:
        res = pool.map(func=drawing, iterable=images)
