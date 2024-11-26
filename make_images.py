from PIL import Image, ImageDraw, ImageFont
from loguru import logger
import os
from pathlib import Path
from natsort import natsorted


# Пути к файлам
input_folder = Path("video creation/comparisons/make_image/input")
output_folder = Path("video creation/comparisons/make_image/output")
template_path = Path("video creation/comparisons/make_image/1orange.png")
font_path = Path("video creation/comparisons/make_image/Bebas-Regular.ttf")
texts_file = Path("video creation/comparisons/make_image/texts.txt")

# Настройки размеров для изображений
image_frame_width = 600
image_frame_height = 600
additional_image_size = (100, 100)

# Настройки шрифтов
font_size_main = 72
font_size_additional = 48

def parse_texts(file_path):
    """Читает файл и возвращает список настроек текста и изображений для обработки."""
    lines = []
    
    if not file_path.exists():
        logger.error(f"Файл с текстом {file_path} не найден.")
        return lines

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue

                parts = line.strip().split(":")
                main_text = parts[0].replace("\\n", "\n") if len(parts) > 0 else ""
                additional_text = parts[1].replace("\\n", "\n") if len(parts) > 1 else ""
                
                # Преобразуем путь к изображению в объект Path
                additional_image_path = Path(":".join(parts[2:])) if len(parts) > 2 else None
                
                lines.append((main_text, additional_text, additional_image_path))
                logger.info(f"Строка {line_number} успешно обработана: {main_text[:20]}...")
    
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {e}")
    
    return lines

def draw_centered_text(draw, text, font, x, y, max_width):
    """
    Центрирует текст и рисует его строка за строкой.
    """
    lines = text.split("\n")
    y_offset = y
    for line in lines:
        # Получаем ширину и высоту строки для центрирования
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_width = line_bbox[2] - line_bbox[0]
        line_height = line_bbox[3] - line_bbox[1]
        
        line_x = x + (max_width - line_width) // 2  # Центрирование по ширине
        draw.text((line_x, y_offset), line, font=font, fill="white")
        y_offset += line_height + 5  # Добавляем отступ между строками


def process_image(img_path, template, font_main, font_additional, main_text, additional_text, additional_image_path, output_path):
    try:
        img = Image.open(img_path).resize((image_frame_width, image_frame_height)).convert("RGBA")
    except Exception as e:
        logger.error(f"Ошибка при открытии изображения {img_path.name}: {e}")
        return  # Exit if the image cannot be opened
    
    canvas = Image.new("RGBA", template.size)
    image_x = (template.width - image_frame_width) // 2
    image_y = 20
    canvas.paste(img, (image_x, image_y))
    combined = Image.alpha_composite(canvas, template)
    
    draw = ImageDraw.Draw(combined)

    # Draw the main text
    if main_text:
        try:
            main_text_bbox = draw.textbbox((0, 0), main_text, font=font_main)
            main_text_x = (template.width - (main_text_bbox[2] - main_text_bbox[0])) // 2
            main_text_y = image_y + image_frame_height #+ 10
            draw.text((main_text_x, main_text_y), main_text, font=font_main, fill="white")
        except Exception as e:
            logger.error(f"Ошибка при рисовании основного текста: {e}")

    # Check if additional_image_path is not None and exists
    if additional_image_path and additional_image_path.exists():
        try:
            additional_img = Image.open(additional_image_path).resize(additional_image_size).convert("RGBA")
            logo_x = (template.width - additional_image_size[0]) // 2
            logo_y = template.height - additional_image_size[1] - 20
            combined.paste(additional_img, (logo_x, logo_y), additional_img)
        except Exception as e:
            logger.error(f"Ошибка при открытии дополнительного изображения {additional_image_path.name}: {e}")

    # Draw the additional text
    if additional_text:
        try:
            additional_text_y = main_text_y + 100  # Offset under the main text
            draw_centered_text(draw, additional_text, font_additional, 0, additional_text_y, template.width)
        except Exception as e:
            logger.error(f"Ошибка при рисовании дополнительного текста: {e}")

    # Save the combined image
    try:
        combined.save(output_path)
        logger.info(f"Изображение {img_path.name} обработано и сохранено как {output_path}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении изображения {output_path}: {e}")



def main():
    # Проверка существования путей
    if not template_path.exists():
        logger.error(f"Файл шаблона {template_path} не найден.")
        return
    if not font_path.exists():
        logger.error(f"Файл шрифта {font_path} не найден.")
        return
    if not input_folder.exists():
        logger.error("Папка input не найдена.")
        return
    
    # Создаем папку output, если она не существует
    output_folder.mkdir(parents=True, exist_ok=True)

    # Открываем шаблон и загружаем шрифты
    template = Image.open(template_path).convert("RGBA")
    try:
        font_main = ImageFont.truetype(str(font_path), font_size_main)
        font_additional = ImageFont.truetype(str(font_path), font_size_additional)
    except OSError:
        logger.error("Не удалось загрузить шрифт.")
        return

    # Парсим текстовые данные
    text_entries = parse_texts(texts_file)
    if not text_entries:
        logger.error("Нет данных для обработки.")
        return

    # # Получаем список изображений, фильтруем по файлам и сортируем по имени
    # image_files = sorted(
    #     (file for file in input_folder.glob("*.png") if file.is_file()),
    #     key=lambda x: x.stem
    # )

    image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
    # Получаем список изображений, фильтруем по файлам и сортируем по имени с помощью natsort
    image_files = natsorted(
        (file for file in input_folder.glob("*") if file.is_file() and file.suffix.lower() in image_extensions),
        key=lambda x: x.stem
    )

    # Перебираем изображения и текстовые данные
    for img_path, (main_text, additional_text, additional_image_path) in zip(image_files, text_entries):
        try:
            output_path = output_folder / f"output_{img_path.stem}.png"
            process_image(img_path, template, font_main, font_additional, main_text, additional_text, additional_image_path, output_path)
        except Exception as e:
            logger.error(f"Ошибка при обработке изображения {img_path.name}: {e}")

    logger.info("Процесс завершен!")


if __name__ == "__main__":
    main()
