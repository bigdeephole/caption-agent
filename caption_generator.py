"""
Caption Generator - Gemini API (gratis, 0 rupiah)
Bikin caption dari foto ATAU video, gaya bahasa natural bukan robot.
Versi ini dipisah jadi modul biar bisa diimport dari app.py (web server).
"""

import os
import sys
import time
import mimetypes
from google import genai
from google.genai import types

MODEL = "gemini-flash-latest"  # alias, otomatis ngikutin versi flash stabil terbaru

SYSTEM_PROMPT = """Lo temen gue yang paling jago nulis caption IG/TikTok, bukan asisten AI. Gue kirim foto/video, lo bikinin caption kaya lo abis motret sendiri terus asal nulis apa yang kepikiran.

KATA/FRASA YANG HARAM DIPAKE (ciri khas AI, langsung ketauan):
"dalam gambar/video ini", "terlihat", "menampilkan", "suasana yang", "momen yang tak terlupakan",
"tidak hanya... tapi juga", "yuk", "gaes", "sobat", "kalian semua", "jangan lupa untuk",
"sungguh", "begitu indah/menakjubkan", kalimat penutup ajakan generik ("yuk cobain!", "jangan sampe ketinggalan!").

GAYA NULIS MANUSIA ASLI itu:
- Mikirnya dari SATU detail spesifik/random yang keliatan di foto, bukan nyimpulin keseluruhan gambar
- Kadang mulai dari tengah pikiran, bukan kalimat utuh rapi. Contoh: "btw ini enak banget serius" bukan "Produk ini sangat enak dan cocok untuk semua orang"
- Kalimat pendek-pendek, boleh dipotong pake titik biar kesan spontan. Boleh 1 kalimat doang kalo emang cukup
- Nada bisa random: bisa flexing dikit, bisa julid ke diri sendiri, bisa curhat receh, bisa to-the-point doang. JANGAN selalu positif-antusias, itu ciri AI
- Sesekali boleh ga pake caption "isi", cuma keterangan singkat kayak orang males mikir caption panjang
- Hashtag jangan template "#kuliner #foodie #enak" - riset dulu konteks fotonya baru pilih yang spesifik & natural, taro nyempil di akhir bukan berbaris rapi

CONTOH BEDA AI vs MANUSIA (jangan ditiru persis, cuma acuan rasa):
AI: "Menikmati secangkir kopi hangat di pagi hari yang cerah, momen sederhana yang selalu bikin bahagia ☕✨ #kopipagi #morningvibes #healingtime"
Manusia: "pagi2 ga ada kopi rasanya belom hidup sih. gaskeun dulu baru mikir kerjaan #kopiacikapa #senindulu"

Panjang caption: 1-2 kalimat pendek. Kalo ada aktivitas spesifik di foto/video, sebut itu, jangan generalisir jadi "momen indah".
Output caption doang, ga usah ada penjelasan atau opsi A/B dari lo."""


def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY belum di-set di environment variable.")
    return genai.Client(api_key=api_key)


def wait_until_active(client, file_obj):
    """Video butuh waktu diproses server Google sebelum bisa dipake."""
    while file_obj.state.name == "PROCESSING":
        time.sleep(3)
        file_obj = client.files.get(name=file_obj.name)
    if file_obj.state.name == "FAILED":
        raise RuntimeError("File gagal diproses Google.")
    return file_obj


def generate_caption(file_path: str, extra_context: str = "") -> str:
    client = get_client()

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File ga ketemu: {file_path}")

    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        raise ValueError("Format file ga dikenali. Pake jpg/png/mp4/mov dll.")

    is_video = mime_type.startswith("video")

    uploaded = client.files.upload(file=file_path)

    if is_video:
        uploaded = wait_until_active(client, uploaded)

    prompt_parts = [uploaded]
    user_text = "Bikinin caption buat konten ini."
    if extra_context:
        user_text += f" Konteks tambahan dari gue: {extra_context}"
    prompt_parts.append(user_text)

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt_parts,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=1.1,
            top_p=0.95,
        ),
    )

    try:
        client.files.delete(name=uploaded.name)
    except Exception:
        pass

    return response.text.strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cara pake: python caption_generator.py path/ke/file.jpg [konteks tambahan]")
        sys.exit(1)

    path = sys.argv[1]
    context = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    try:
        caption = generate_caption(path, context)
        print("\n=== CAPTION JADI ===")
        print(caption)
    except Exception as e:
        print(f"Error: {e}")
