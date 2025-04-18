from flask import Blueprint, send_from_directory

bp = Blueprint('visualizations', __name__)

@bp.route('/outputs/<path:filename>', methods=['GET'])
def serve_output_image(filename):
    return send_from_directory('/app/outputs', filename)