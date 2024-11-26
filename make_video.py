from moviepy.editor import (
    ImageClip, VideoClip, AudioFileClip, concatenate_audioclips, concatenate_videoclips, CompositeVideoClip, vfx, VideoFileClip
)
from PIL import Image
import os
import random
from natsort import natsorted

VIDEO_TITLE = "Video title - comparison"

VOLUME = 0.4
SPEED = 5

# Параметры видео
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 30
PRE_DELAY = 3  # Задержка перед началом движения (секунды)
POST_DELAY = 5  # Задержка после окончания движения (секунды)
OVERLAY_START_TIME = 15  # Время начала наложения видео (секунды)

# Пути к папкам и файлам
folder_path = "video creation/comparisons/make_image/output"
music_folder_path = "video creation/comparisons/make_video/music"
outro_footage_path = "video creation/comparisons/make_video/video/outro.mp4"
action_video_path = "video creation/comparisons/make_video/video/action.mp4"

def create_panoramic_image(folder_path):
    """Создает панорамное изображение, объединяя все изображения по ширине."""
    # Get list of images sorted in human (natural) order
    images = [Image.open(os.path.join(folder_path, img)) for img in natsorted(os.listdir(folder_path)) if img.endswith(('.jpg', '.png'))]
    
    if not images:
        raise ValueError("Нет изображений для обработки. Проверьте путь к папке и наличие файлов.")
    
    total_width = sum(img.width for img in images)
    max_height = max(img.height for img in images)
    
    panoramic_image = Image.new('RGB', (total_width, max_height))
    
    x_offset = 0
    for img in images:
        panoramic_image.paste(img, (x_offset, 0))
        x_offset += img.width
    
    os.makedirs("video creation/comparisons/make_video/frames", exist_ok=True)
    panoramic_image_path = "video creation/comparisons/make_video/frames/panoramic_image.png"
    panoramic_image.save(panoramic_image_path)
    
    return panoramic_image_path, total_width, len(images) * SPEED

def create_panning_video(panoramic_image_path, output_path, video_duration):
    """Создает видео с горизонтальным панорамированием по изображению и добавляет задержки."""
    panoramic_clip = ImageClip(panoramic_image_path)
    panoramic_width, panoramic_height = panoramic_clip.size

    def make_frame(t):
        x_position = -(panoramic_width - SCREEN_WIDTH) * (t / video_duration)
        return panoramic_clip.crop(x1=-x_position, width=SCREEN_WIDTH, height=SCREEN_HEIGHT).get_frame(t)
    
    # Создаем VideoClip с панорамированием
    panning_clip = VideoClip(make_frame, duration=video_duration).set_fps(FPS)

    # Добавляем фоновую музыку
    audio = create_background_music(video_duration + PRE_DELAY + POST_DELAY)
    panning_clip = panning_clip.set_audio(audio)
    
    # Добавляем начальную и конечную задержки
    start_delay = panning_clip.get_frame(0)
    start_delay_clip = ImageClip(start_delay, duration=PRE_DELAY).set_fps(FPS)
    
    end_delay = panning_clip.get_frame(video_duration - 1)
    end_delay_clip = ImageClip(end_delay, duration=POST_DELAY).set_fps(FPS)
    
    # Объединяем с начальной и конечной задержками
    full_panning_video = concatenate_videoclips([start_delay_clip, panning_clip, end_delay_clip])

    # Загрузка дополнительного футажа и объединение его с панорамным видео
    additional_footage = VideoFileClip(outro_footage_path).set_duration(video_duration).set_fps(FPS)
    base_video = concatenate_videoclips([full_panning_video, additional_footage])

    # Наложение видео с вырезанным зеленым фоном на 30-й секунде
    action_clip = VideoFileClip(action_video_path).resize((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    # Загружаем дополнительный футаж и задаем его фиксированную продолжительность
    additional_footage = VideoFileClip(outro_footage_path).set_duration(20.7).set_fps(FPS)

    # Добавляем футаж к основному панорамному видео
    base_video = concatenate_videoclips([full_panning_video, additional_footage])

    # Наложение action_clip на основное видео с 30-й секунды
    action_clip = (
        VideoFileClip(action_video_path)
        .resize((SCREEN_WIDTH, SCREEN_HEIGHT))
        .fx(vfx.mask_color, color=[0, 255, 22], thr=100, s=5)  # Удаление зеленого фона
        .set_start(OVERLAY_START_TIME)
        .set_position(("center", "center"))
    )

    # Установка точной длительности на основе base_video
    final_video_duration = base_video.duration
    final_video = CompositeVideoClip([base_video, action_clip]).set_duration(final_video_duration)

    # Экспорт финального видео с точной продолжительностью
    final_video.write_videofile(output_path, fps=FPS)



def create_background_music(video_duration):
    """Создает аудиотрек, выбирая случайные музыкальные файлы и объединяя их для фона."""
    music_files = [os.path.join(music_folder_path, f) for f in os.listdir(music_folder_path) if f.endswith(('.mp3', '.wav'))]
    if not music_files:
        raise ValueError("Нет музыкальных файлов для обработки. Проверьте путь к папке и наличие файлов.")

    random.shuffle(music_files)
    
    clips = []
    total_duration = 0
    
    while total_duration < video_duration:
        for music_file in music_files:
            audio_clip = AudioFileClip(music_file).volumex(VOLUME)
            clips.append(audio_clip)
            total_duration += audio_clip.duration
            if total_duration >= video_duration:
                break

    # Объединение аудиоклипов
    final_audio = concatenate_audioclips(clips).set_duration(video_duration)
    return final_audio

def main():
    panoramic_image_path, panoramic_width, video_duration = create_panoramic_image(folder_path)
    create_panning_video(panoramic_image_path, f"video creation/comparisons/make_video/{VIDEO_TITLE}.mp4", video_duration)

if __name__ == "__main__":
    main()
