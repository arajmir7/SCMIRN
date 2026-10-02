"""Serve citizen-uploaded issue evidence through the API service."""

from flask import Blueprint, current_app, send_from_directory

bp = Blueprint("uploads", __name__)


@bp.route("/uploads/<path:filename>", methods=["GET"])
def uploaded_file(filename: str):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
