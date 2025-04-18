from flask import Flask, jsonify, render_template
from routes import frames, upload, videos, visualizations

def create_app():
    app = Flask(__name__)

    app.config["UPLOAD_FOLDER"] = "/app/videos"
    app.config["ALLOWED_EXTENSIONS"] = {"mp4", "avi", "mov", "mkv"}

    app.register_blueprint(frames.bp)
    app.register_blueprint(upload.bp)
    app.register_blueprint(videos.bp)
    app.register_blueprint(visualizations.bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)