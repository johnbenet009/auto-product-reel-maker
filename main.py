import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont
from tiktok_voice import tts, Voice
import json
import shutil
import concurrent.futures
import moviepy.editor as mpe
from datetime import datetime
import random

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/', methods=['POST'])
def process_data():
    try:
        data = request.get_json()
         maindomain = data['Domain'] 
        domain = data['Domain'].replace(".", "") 
        currency = data['currency']
        products = data['products']
        domain_dir = os.path.join(os.getcwd(), domain)

        if os.path.exists(domain_dir):
            shutil.rmtree(domain_dir)
        os.makedirs(domain_dir, exist_ok=True)

        images_dir = os.path.join(domain_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        font_path = os.path.join(os.getcwd(), 'font2.ttf')
        music_dir = os.path.join(os.getcwd(), 'music')

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for i, product in enumerate(products):
                future = executor.submit(process_product, i+1, product, images_dir, font_path, domain, currency)
                futures.append(future)
            concurrent.futures.wait(futures)

        music_files = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
        if not music_files:
            raise Exception("No MP3 files found in the 'music' directory.")
        random_music_file = random.choice(music_files)
        background_music_path = os.path.join(music_dir, random_music_file)

        now = datetime.now()
        formatted_date = now.strftime("%B %d, %Y")
        intro_text = f"Trending discounted products from {maindomain} today {formatted_date}!"
        intro_audio_filename = os.path.join(images_dir, "intro.mp3")
        tts(intro_text, Voice.US_MALE_4, intro_audio_filename, play_sound=False)
        intro_audio = mpe.AudioFileClip(intro_audio_filename)

        image_files = [f for f in os.listdir(images_dir) if f.endswith(('.jpg','.jpeg','.png'))]
        image_clips = [mpe.ImageClip(os.path.join(images_dir, f)).set_duration(3) for f in image_files]
        final_video = mpe.concatenate_videoclips(image_clips,method="compose")
        background_music = mpe.AudioFileClip(background_music_path)
        final_audio = mpe.concatenate_audioclips([intro_audio, background_music.subclip(0,final_video.duration - intro_audio.duration)])
        final_video.audio = final_audio
        final_video.write_videofile(os.path.join(images_dir, "final.mp4"),fps=24,codec='libx264',audio_codec='aac',temp_audiofile='temp-audio.m4a',remove_temp=True)

        for f in os.listdir(images_dir):
          if f.endswith(('.jpg','.jpeg','.png','.mp3')):
            os.remove(os.path.join(images_dir,f))

        download_link = f"https://vidmaker.cart9.com.ng/{domain}/images/final.mp4"
        return jsonify({"message": "Images downloaded and processed successfully", "download_link": download_link, "currency": currency}), 200

    except KeyError as e:
        return jsonify({"error": f"Missing key in JSON: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route('/download/<domain>/<filename>')
def download_file(domain, filename):
    directory = os.path.join(os.getcwd(), domain, 'images')
    return send_from_directory(directory, filename, as_attachment=True)

def process_product(index, product, images_dir, font_path, domain, currency):
    image_url = product['imagesUrl']
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        ext = os.path.splitext(image_url)[1].lower()
        if ext not in ('.jpg', '.jpeg', '.png'):
            raise Exception(f"Unsupported image format for image {index}: {ext}")
        image_filename = os.path.join(images_dir, f"{index}{ext}")
        with open(image_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        img = Image.open(image_filename)
        width, height = img.size
        target_height = 1080
        target_width = int(target_height / 16 * 9)

        width_scale = target_width / width
        height_scale = target_height / height
        scale_factor = min(width_scale, height_scale)
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        new_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
        left = (target_width - new_width) // 2
        top = (target_height - new_height) // 2
        new_img.paste(resized_img, (left, top))
        border_width = 10
        final_img = Image.new('RGB', (target_width + 2 * border_width, target_height + 2 * border_width), (0, 0, 0))
        final_img.paste(new_img, (border_width, border_width))

        draw = ImageDraw.Draw(final_img)
        text = f"{product['name']} - {currency}{product['amount']}\n{product['description']}"

        font_size = 35
        font = ImageFont.truetype(font_path, font_size)

        lines = []
        line_width = 0
        current_line = ""
        words = text.split()
        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            if test_width < target_width * 0.9:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

        line_height = font.getsize(lines[0])[1]
        line_spacing = int(line_height * 0.1)
        total_height = len(lines) * line_height + (len(lines) - 1) * line_spacing
        
        # Add domain at the top
        domain_width, domain_height = draw.textsize(domain, font=font)
        domain_x = (target_width + 2 * border_width - domain_width) // 2
        domain_y = border_width + 10
        draw.text((domain_x + 2, domain_y + 2), domain, font=font, fill="black")
        draw.text((domain_x, domain_y), domain, font=font, fill="white")

        y_offset = target_height + 2 * border_width - total_height - border_width - 10 - domain_height -10

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (target_width + 2 * border_width - line_width) // 2
            y = y_offset + i * (line_height + line_spacing)
            draw.text((x + 2, y + 2), line, font=font, fill="black")
            draw.text((x, y), line, font=font, fill="white")

        final_img.save(image_filename)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image {index}: {e}")
    except Exception as e:
        print(f"Error processing image {index}: {e}")

if __name__ == '__main__':
    app.run(debug=True)