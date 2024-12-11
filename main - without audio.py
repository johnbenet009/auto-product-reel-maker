import os
import requests
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import json
import shutil

app = Flask(__name__)

@app.route('/', methods=['POST'])
def process_data():
    try:
        data = request.get_json()
        domain = data['Domain']
        products = data['products']
        domain_dir = os.path.join(os.getcwd(), domain)

        if os.path.exists(domain_dir):
            shutil.rmtree(domain_dir)
        os.makedirs(domain_dir, exist_ok=True)

        images_dir = os.path.join(domain_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        font_path = os.path.join(os.getcwd(), 'font2.ttf')

        for i, product in enumerate(products):
            image_url = product['imagesUrl']
            try:
                response = requests.get(image_url, stream=True)
                response.raise_for_status()
                ext = os.path.splitext(image_url)[1].lower()
                if ext not in ('.jpg', '.jpeg', '.png'):
                    return jsonify({"error": f"Unsupported image format for image {i+1}: {ext}"}), 400
                image_filename = os.path.join(images_dir, f"{i+1}{ext}")
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
                text = f"{product['name']} for just {product['amount']}\n{product['description']}"
                if i == 0:
                    text = "Trending discounted products from " + domain + "!\n\n" + text

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
                y_offset = target_height + 2 * border_width - total_height - border_width - 10 # Bottom alignment

                for i, line in enumerate(lines):
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    x = (target_width + 2 * border_width - line_width) // 2
                    y = y_offset + i * (line_height + line_spacing)
                    draw.text((x + 2, y + 2), line, font=font, fill="black")
                    draw.text((x, y), line, font=font, fill="white")

                final_img.save(image_filename)

            except requests.exceptions.RequestException as e:
                return jsonify({"error": f"Error downloading image {i+1}: {e}"}), 500
            except Exception as e:
                return jsonify({"error": f"Error processing image {i+1}: {e}"}), 500

        return jsonify({"message": "Images downloaded and processed successfully"}), 200

    except KeyError as e:
        return jsonify({"error": f"Missing key in JSON: {e}"}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)