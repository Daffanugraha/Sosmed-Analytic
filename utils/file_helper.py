import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_VIDEO = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
ALLOWED_IMAGE = {'jpg', 'jpeg', 'png', 'gif', 'webp'}


def allowed_file(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in ALLOWED_VIDEO | ALLOWED_IMAGE


def get_media_type(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext in ALLOWED_VIDEO:
        return 'video'
    if ext in ALLOWED_IMAGE:
        return 'image'
    return 'unknown'


def save_uploaded_file(file_obj, user_id: int) -> dict:
    """Save an uploaded file and return metadata dict."""
    original_name = secure_filename(file_obj.filename)
    ext = original_name.rsplit('.', 1)[-1].lower()
    unique_name = f"{user_id}_{uuid.uuid4().hex}.{ext}"
    user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    save_path = os.path.join(user_dir, unique_name)
    file_obj.save(save_path)
    media_type = get_media_type(original_name)
    rel_path = f"uploads/{user_id}/{unique_name}"
    return {
        'filename': unique_name,
        'original_name': original_name,
        'path': save_path,
        'url': f"/static/{rel_path}",
        'media_type': media_type,
        'size': os.path.getsize(save_path),
    }


def delete_file(rel_url: str):
    """Delete a file given its /static/... URL."""
    try:
        base = current_app.static_folder
        sub = rel_url.replace('/static/', '', 1)
        full = os.path.join(base, sub)
        if os.path.exists(full):
            os.remove(full)
    except Exception:
        pass
