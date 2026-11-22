"""Rebuild the illustrative local PNG symbols; no AI generation or downloads.

Writes new assets only. Requires Pillow and the skill's local prepare helper.
"""
from pathlib import Path
import importlib.util
import tempfile


def main():
    from PIL import Image, ImageDraw
    root=Path(__file__).resolve().parents[2]
    spec=importlib.util.spec_from_file_location('prepare_icon',root/'scripts/prepare_icon.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    output=Path(__file__).parent/'assets'
    with tempfile.TemporaryDirectory() as tmp:
        for name,colour in [('records','#0072B2'),('review','#E69F00'),('summary','#009E73')]:
            image=Image.new('RGBA',(512,512),'white');draw=ImageDraw.Draw(image)
            if name=='review':
                draw.ellipse((96,76,340,320),outline=colour,width=24)
                draw.line((312,292,420,400),fill=colour,width=24)
                draw.ellipse((408,388,432,412),fill=colour)
                draw.rounded_rectangle((152,158,284,178),radius=10,fill=colour)
                draw.rounded_rectangle((152,216,252,236),radius=10,fill=colour)
            else:
                draw.rounded_rectangle((114,60,398,452),radius=32,outline=colour,width=24)
                for y in (156,232,308):
                    draw.rounded_rectangle((172,y,340,y+22),radius=11,fill=colour)
                if name=='summary':
                    draw.line((172,378,204,404,258,354),fill=colour,width=22)
                    for x,y in [(172,378),(258,354)]:draw.ellipse((x-11,y-11,x+11,y+11),fill=colour)
            raw=Path(tmp)/f'{name}.png';image.save(raw)
            # All fixture marks use this one exact foreground colour.
            helper.prepare(raw,output/f'{name}.png',foreground=colour)
    print('Prepared three locally authored illustrative icons; inspect assets/*-background-check.png')


if __name__=='__main__':
    main()
