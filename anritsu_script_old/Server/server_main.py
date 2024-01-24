from flask import Flask, request, jsonify
import os

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Desktop", "SweeptronServer")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400



        # Salva il file nella cartella specificata
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

        return jsonify({"success": "File uploaded successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
