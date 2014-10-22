import glob
import json
import os
import subprocess

import Image


def optimize_png(filename):
    with open(os.path.devnull, 'w') as devnull:
        subprocess.check_call(("/usr/bin/optipng", filename), stdout=devnull)


class SpriteSheet():
    def __init__(self, max_width):
        self.max_width = max_width
        self.width = 0
        self.height = 0
        self.x_offset = 0
        self.y_offset = 0
        self.row_height = 0
        self.sprites = []
  
    def add_sprite(self, name, image):
        sprite = Sprite(name, image, self.x_offset, self.y_offset)

        if (sprite.x + sprite.width > self.max_width):
            sprite.x = 0
            sprite.y = self.y_offset + self.row_height
            self.row_height = sprite.height
        else:
            self.width = max(self.width, sprite.x + sprite.width)
            self.row_height = max(self.row_height, sprite.height)

        self.height = sprite.y + self.row_height
        self.x_offset = sprite.x + sprite.width
        self.y_offset = sprite.y
        self.sprites.append(sprite)

        return sprite

    def save(self, spritesheet_path):
        background_color = (255, 69, 0, 0)  # transparent orangered
        image = Image.new('RGBA', (self.width, self.height), background_color)

        for sprite in self.sprites:
            image.paste(sprite.image, (sprite.x, sprite.y))

        image.save(spritesheet_path, optimize=True)
        optimize_png(spritesheet_path)


class Sprite():
    def __init__(self, name, image, x, y):
        self.name = name
        self.image = image
        self.width = image.size[0]
        self.height = image.size[1]
        self.x = x
        self.y = y

    def to_dict(self):
        # is there a better way to do this? I really just need to get a dict of
        # everything but the `image` property, as that doesn't serialize to json
        return {
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'x': self.x,
            'y': self.y,
        }


def spritify(sprite_folder, spritesheet_output_path, tailor_output_path):
    sprite_folder = os.path.abspath(sprite_folder)
    spritesheet_output_path = os.path.abspath(spritesheet_output_path)
    tailor_output_path = os.path.abspath(tailor_output_path)
    sprite_directories = os.walk(sprite_folder).next()[1]
    tailors = []
    
    # each folder == a tailor
    for directory in sprite_directories:
        # each directory can contain a tailor.json file to override defaults
        tailor_config_path = os.path.join(sprite_folder, directory, 'tailor.json')
        tailor = None
        if os.path.isfile(tailor_config_path):
            with open(tailor_config_path) as config_file:    
                tailor = json.load(config_file)
        if not tailor:
            tailor = {}
        if not 'name' in tailor:
            tailor['name'] = directory
        if not 'allow_clear' in tailor:
            tailor['allow_clear'] = True
        if not 'spritesheet' in tailor:
            tailor['spritesheet'] = directory
        # was relying on order in json for rendering order, but can't rely on
        # that if its generated
        if not 'z-index' in tailor:
            tailor['z-index'] = 100
        
        spritesheet_name = tailor['spritesheet']
        tailor['dressings'] = []
        spritesheet = SpriteSheet(6400)
        sprite_paths = glob.glob(os.path.join(
            sprite_folder, directory, '*.png'))
        for sprite_path in image_paths:
            image = Image.open(sprite_path)
            name = os.path.splitext(os.path.basename(sprite_path))[0]
            sprite = spritesheet.add_sprite(name, image)
            tailor['dressings'].append(sprite.to_dict())
        tailors.append(tailor)
        spritesheet.save(os.path.join(
            spritesheet_output_path, spritesheet_name + '.png'))

    with open(tailor_output_path, 'w') as output_file:
        json.dump(tailors, output_file, indent=4)


if __name__ == '__main__':
    import sys
    print spritify(sys.argv[1], sys.argv[2], sys.argv[3])
