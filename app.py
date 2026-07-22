import os
import tempfile
from flask import Flask, request, render_template, jsonify

from caption_generator import generate_caption

app = Flask(__name__)

# batasi ukuran upload (default 20MB, bisa diubah lewat env var)
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_UPLOAD_MB", 20)) * 1024 * 1024


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/caption", methods=["POST"])
def api_caption():
    if "file" not in request.files:
        return jsonify({"error": "Ga ada file yang diupload."}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "Nama file kosong."}), 400

    context = request.form.get("context", "")

    suffix = os.path.splitext(f.filename)[1] or ""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name

    try:
        caption = generate_caption(tmp_path, context)
        return jsonify({"caption": caption})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
