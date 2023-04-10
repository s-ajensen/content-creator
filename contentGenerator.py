from pytube import YouTube
from pytube.cli import on_progress
from json import load
from itertools import cycle
from enum import Enum
from random import shuffle
from moviepy.editor import *
from moviepy.video.fx import *
from moviepy.audio.fx.all import volumex

CONFIG_FILE = "./config.json"

def get_config_section(key: str):
    file = open(CONFIG_FILE)
    return load(file)[key]

FILLER_DIR = get_config_section('filler_dir')
CONTENT_DIR = get_config_section('content_dir')
OUTPUT_DIR = get_config_section('output_dir')
SOUNDS_DIR = get_config_section('sounds_dir')
FILE_RES = get_config_section('res')

MediaType = Enum('MediaType', ['mp3', 'mp4'])

def download_content(url: str, out_dir: str, media_type: MediaType):
    yt = YouTube(url, on_progress_callback=on_progress)
    streams = yt.streams.filter(file_extension='mp4', res=FILE_RES) if media_type == MediaType['mp4'] else yt.streams.filter(only_audio=True)

    media = streams.first()
    media.download(out_dir)
    return f'{out_dir}/{media.default_filename}'

def fetch_filler_videos() -> list[str]:
    for file in get_config_section('fillers'):
        yield download_content(file, FILLER_DIR, MediaType['mp4'])

def fetch_sounds() -> list[str]:
    for file in get_config_section('sounds'):
        yield download_content(file, SOUNDS_DIR, MediaType['mp3'])

def trim_fillers(content_length: int, fillers: list[VideoFileClip]) -> VideoFileClip:
    filler_clip = concatenate_videoclips(fillers)
    sound_clips = [AudioFileClip(file) for file in fetch_sounds()]
    shuffle(sound_clips)
    sound = concatenate_audioclips(sound_clips)

    while (filler_clip.duration < content_length):
        filler_clip = concatenate_videoclips([filler_clip, filler_clip])

    filler_clip = filler_clip.without_audio().subclip(0, content_length)

    while (sound.duration < content_length):
        sound = concatenate_audioclips([sound, sound])

    sound = sound.subclip(0, content_length).fx(volumex, 0.2)
    filler_clip.audio = sound

    return filler_clip

def fill_content(content_path, output_file_name):
    content = VideoFileClip(content_path)
    fillers = [VideoFileClip(file) for file in fetch_filler_videos()]
    shuffle(fillers)

    final = clips_array([[content], [trim_fillers(content.duration, fillers)]])
    final.write_videofile(f'{OUTPUT_DIR}/{output_file_name}.mp4')

def main():
    link = input('Enter Url:')
    file_name = input('Enter Output Filename:')
    content_path = download_content(link, CONTENT_DIR, MediaType['mp4'])

    fill_content(content_path, file_name)

if __name__ == "__main__":
    main()