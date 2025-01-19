Python Script for Creating Product Promotion Videos

This Python script automates the creation of short promotional videos for products, ideal for platforms like TikTok, Instagram Reels, or YouTube Shorts. It takes product data as JSON input, downloads product images, adds text overlays, generates voiceovers, and merges everything into a single MP4 video. The final video is ready for direct upload to social media.

Functionality:

JSON Input: The script accepts a JSON payload containing product details:

{
  "Domain": "example.com",          // Your website domain
  "Website Name": "Example Website", // Your website name (optional)
  "currency": "NGN",                // Currency symbol
  "products": [
    {
      "name": "Gicci Shoe",          // Product name
      "amount": 800,                // Product price
      "description": "something short about the product", // Product description
      "imagesUrl": "https://ayoolamipalace.com/product_images/BI0L0ov1x1.jpg" // URL of product image
    },
    {
      "name": "3d Wallpapper",
      "amount": 2300,
      "imagesUrl": "https://demo.cultaz.com/product_images/z0t77x1qaq.jpg"
    },
    {
      "name": "Nokia Charger",
      "amount": 2300,
      "imagesUrl": "https://ayoolamipalace.com/product_images/MxMsxIMerR.jpg"
    },
    {
      "name": "Used iphone 12",
      "amount": 32300,
      "imagesUrl": "https://ayoolamipalace.com/product_images/4nBaPok5Kz.jpg"
    }
  ]
}
content_copy
Use code with caution.
Json

Image Processing: Downloads product images, resizes them to a 9:16 aspect ratio (suitable for vertical videos), adds black padding to maintain aspect ratio, and overlays text (product name, price, description, and domain name) with a white-text-with-black-shadow style.

Voiceover Generation: Uses the tiktok_voice library to generate a voiceover for the intro text and product descriptions (optional, can be adapted).

Video Creation: Combines the processed images and audio using moviepy into a single MP4 video. A random background music track is selected from the "music" folder (must be created and populated with mp3 files).

File Cleanup: Deletes the individual image and audio files after video creation to reduce clutter.

API Endpoint: A Flask API endpoint (/) accepts the JSON data and returns the download link for the final video.

Download Link: A dedicated route (/download/<domain>/<filename>) allows direct download of the video.

Prerequisites:

Python 3.7+

Install necessary libraries:

pip install Flask requests Pillow moviepy tiktok-voice
content_copy
Use code with caution.
Bash

FFmpeg installed and accessible in your system's PATH.

A font2.ttf font file in the project's root directory.

A music directory in the project's root directory containing MP3 files for background music.

To Run:

Clone the repository.

Install required libraries.

Configure the font path and music directory.

Run the script using python app.py.

Send a POST request to the / endpoint with the JSON payload.

Usage: This script is a useful tool for quickly generating social media product promotion videos, saving time and effort compared to manual video editing. The concurrent processing using ThreadPoolExecutor helps speed up video creation for many products. Error handling is implemented to provide useful error messages.


## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
