"""
Crypto Magnate Feedback System - Backend
Flask API that proxies feedback reports to Asana
"""

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import requests

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

logger.info("=== Crypto Magnate Feedback Backend: успешно задеплоен и запущен ===")

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins != "*":
    allowed_origins = [origin.strip() for origin in allowed_origins.split(",")]
CORS(app, origins=allowed_origins)
logger.info(f"CORS настроен для origins: {allowed_origins}")

# Asana configuration
ASANA_ACCESS_TOKEN = os.getenv("ASANA_ACCESS_TOKEN")
ASANA_PROJECT_GID = os.getenv("ASANA_PROJECT_GID")
ASANA_WORKSPACE_GID = os.getenv("ASANA_WORKSPACE_GID")
ASANA_API_BASE = "https://app.asana.com/api/1.0"

if not ASANA_ACCESS_TOKEN:
    logger.warning("ASANA_ACCESS_TOKEN не задан")
if not ASANA_PROJECT_GID:
    logger.warning("ASANA_PROJECT_GID не задан")
if not ASANA_WORKSPACE_GID:
    logger.warning("ASANA_WORKSPACE_GID не задан")

# File upload limits
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_FILE_TYPES = {
    "image/png", "image/jpeg", "image/webp",
    "video/mp4", "video/quicktime", "video/webm"
}


def create_asana_task(name: str, html_notes: str) -> dict:
    """Create a task in Asana and return the response."""
    logger.info(f"Создание задачи в Asana: '{name}'")

    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "data": {
            "name": name,
            "html_notes": html_notes,
            "projects": [ASANA_PROJECT_GID],
            "workspace": ASANA_WORKSPACE_GID
        }
    }

    response = requests.post(
        f"{ASANA_API_BASE}/tasks",
        headers=headers,
        json=payload
    )

    result = response.json()

    if "errors" in result:
        logger.error(f"Ошибка создания задачи в Asana: {result['errors']}")
    else:
        task_gid = result.get("data", {}).get("gid")
        logger.info(f"Задача в Asana успешно создана: gid={task_gid}")

    return result


def upload_attachment_to_task(task_gid: str, file_data, filename: str, content_type: str) -> dict:
    """Upload an attachment to an Asana task."""
    size_kb = len(file_data) / 1024
    logger.info(f"Загрузка вложения '{filename}' ({size_kb:.1f} КБ) к задаче {task_gid}")

    headers = {
        "Authorization": f"Bearer {ASANA_ACCESS_TOKEN}"
    }

    files = {
        "file": (filename, file_data, content_type)
    }

    response = requests.post(
        f"{ASANA_API_BASE}/tasks/{task_gid}/attachments",
        headers=headers,
        files=files
    )

    result = response.json()

    if "errors" in result:
        logger.error(f"Ошибка загрузки вложения '{filename}': {result['errors']}")
    else:
        logger.info(f"Вложение '{filename}' успешно загружено")

    return result


def build_problem_task(data: dict) -> tuple:
    """Build task name and HTML notes for a problem report."""
    actual_result = data.get("actual_result", "")[:100]
    name = f"[Bug] {actual_result}"
    logger.info(f"Формирование задачи-бага для tg_id={data.get('tg_id')}: '{name}'")

    username = data.get("username", "")
    username_display = f"@{username}" if username else "Unknown"

    html_notes = f"""<body><h2>Bug Report</h2><ul><li><strong>Reporter:</strong> {username_display} (ID: {data.get('tg_id', 'N/A')})</li></ul><h2>Steps to Reproduce</h2><ul><li>{data.get('playback_steps', '').replace(chr(10), ' ')}</li></ul><h2>Actual Result</h2><ul><li>{data.get('actual_result', '')}</li></ul><h2>Expected Result</h2><ul><li>{data.get('expected_result', '')}</li></ul><h2>Technical Details</h2><ul><li>OS: {data.get('os', 'N/A')}</li><li>Device: {data.get('device', 'N/A')}</li><li>Telegram: {data.get('tg_version', 'N/A')}</li><li>ID: {data.get('tg_id', 'N/A')}</li><li>Lang: {data.get('lang', 'N/A')}</li><li>VPN: {data.get('vpn', 'N/A')}</li></ul></body>"""

    return name, html_notes


def build_idea_task(data: dict) -> tuple:
    """Build task name and HTML notes for an idea submission."""
    idea_title = data.get("idea_title", "")[:100]
    name = f"[Idea] {idea_title}"
    logger.info(f"Формирование задачи-идеи для tg_id={data.get('tg_id')}: '{name}'")

    username = data.get("username", "")
    username_display = f"@{username}" if username else "Unknown"

    html_notes = f"""<body><h2>Feature Idea</h2><ul><li><strong>Reporter:</strong> {username_display} (ID: {data.get('tg_id', 'N/A')})</li></ul><h2>Idea</h2><ul><li>{data.get('idea_title', '')}</li></ul><h2>Description</h2><ul><li>{data.get('idea_description', '').replace(chr(10), ' ')}</li></ul><h2>Expected Improvement</h2><ul><li>{data.get('improvement', '').replace(chr(10), ' ')}</li></ul><h2>Reporter Details</h2><ul><li>OS: {data.get('os', 'N/A')}</li><li>Device: {data.get('device', 'N/A')}</li><li>Telegram: {data.get('tg_version', 'N/A')}</li><li>ID: {data.get('tg_id', 'N/A')}</li><li>Lang: {data.get('lang', 'N/A')}</li></ul></body>"""

    return name, html_notes


def validate_problem_data(data: dict) -> list:
    """Validate problem report data. Returns list of errors."""
    errors = []

    playback_steps = data.get("playback_steps", "")
    if len(playback_steps.strip()) < 10:
        errors.append({"field": "playback_steps", "message": "Minimum 10 characters required"})

    actual_result = data.get("actual_result", "")
    if len(actual_result.strip()) < 5:
        errors.append({"field": "actual_result", "message": "Minimum 5 characters required"})

    expected_result = data.get("expected_result", "")
    if len(expected_result.strip()) < 5:
        errors.append({"field": "expected_result", "message": "Minimum 5 characters required"})

    if errors:
        logger.warning(f"Ошибка валидации бага: {errors}")

    return errors


def validate_idea_data(data: dict) -> list:
    """Validate idea submission data. Returns list of errors."""
    errors = []

    idea_title = data.get("idea_title", "")
    if len(idea_title.strip()) < 5:
        errors.append({"field": "idea_title", "message": "Minimum 5 characters required"})

    idea_description = data.get("idea_description", "")
    if len(idea_description.strip()) < 20:
        errors.append({"field": "idea_description", "message": "Minimum 20 characters required"})

    improvement = data.get("improvement", "")
    if len(improvement.strip()) < 10:
        errors.append({"field": "improvement", "message": "Minimum 10 characters required"})

    if errors:
        logger.warning(f"Ошибка валидации идеи: {errors}")

    return errors


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    logger.debug("Запрос health check")
    return jsonify({"status": "ok"})


@app.route("/api/report", methods=["POST"])
def submit_report():
    """
    Submit a feedback report (problem or idea) to Asana.
    Accepts multipart/form-data with optional file attachments.
    """
    try:
        # Get form data
        data = {
            "category": request.form.get("category"),
            "tg_id": request.form.get("tg_id"),
            "username": request.form.get("username"),
            "os": request.form.get("os"),
            "device": request.form.get("device"),
            "tg_version": request.form.get("tg_version"),
            "vpn": request.form.get("vpn", "no"),
            "lang": request.form.get("lang"),
        }

        category = data.get("category")
        logger.info(f"Входящий репорт: category={category}, tg_id={data.get('tg_id')}, username={data.get('username')}")

        # Validate category
        if category not in ("problem", "idea"):
            logger.warning(f"Неверная категория: '{category}'")
            return jsonify({
                "error": "validation_error",
                "details": [{"field": "category", "message": "Must be 'problem' or 'idea'"}]
            }), 422

        # Validate required fields
        if not data.get("tg_id"):
            logger.warning("Отсутствует tg_id в запросе")
            return jsonify({
                "error": "validation_error",
                "details": [{"field": "tg_id", "message": "Telegram ID is required"}]
            }), 422

        if not data.get("lang"):
            data["lang"] = "en"

        # Category-specific data and validation
        if category == "problem":
            data["playback_steps"] = request.form.get("playback_steps", "")
            data["actual_result"] = request.form.get("actual_result", "")
            data["expected_result"] = request.form.get("expected_result", "")

            errors = validate_problem_data(data)
            if errors:
                return jsonify({"error": "validation_error", "details": errors}), 422

            name, html_notes = build_problem_task(data)
        else:
            data["idea_title"] = request.form.get("idea_title", "")
            data["idea_description"] = request.form.get("idea_description", "")
            data["improvement"] = request.form.get("improvement", "")

            errors = validate_idea_data(data)
            if errors:
                return jsonify({"error": "validation_error", "details": errors}), 422

            name, html_notes = build_idea_task(data)

        # Create Asana task
        task_response = create_asana_task(name, html_notes)

        if "errors" in task_response:
            return jsonify({
                "error": "asana_error",
                "message": task_response.get("errors", [{}])[0].get("message", "Unknown error")
            }), 502

        task_gid = task_response.get("data", {}).get("gid")

        if not task_gid:
            logger.error("Asana вернула успех, но task_gid отсутствует")
            return jsonify({
                "error": "asana_error",
                "message": "Failed to create task"
            }), 502

        # Handle file uploads (only for problem reports)
        if category == "problem":
            files = request.files.getlist("files")
            logger.info(f"Обработка {len(files)} файл(ов) для задачи {task_gid}")
            attachment_errors = []

            for file in files:
                if file.filename:
                    # Check file size
                    file.seek(0, 2)
                    size = file.tell()
                    file.seek(0)

                    if size > MAX_FILE_SIZE:
                        logger.warning(f"Файл '{file.filename}' отклонён: слишком большой ({size / 1024 / 1024:.1f} МБ)")
                        attachment_errors.append({
                            "file": file.filename,
                            "error": "File too large (max 50MB)"
                        })
                        continue

                    if file.content_type not in ALLOWED_FILE_TYPES:
                        logger.warning(f"Файл '{file.filename}' отклонён: неподдерживаемый тип '{file.content_type}'")
                        attachment_errors.append({
                            "file": file.filename,
                            "error": "Unsupported file type"
                        })
                        continue

                    try:
                        upload_response = upload_attachment_to_task(
                            task_gid,
                            file.read(),
                            file.filename,
                            file.content_type
                        )

                        if "errors" in upload_response:
                            attachment_errors.append({
                                "file": file.filename,
                                "error": upload_response.get("errors", [{}])[0].get("message", "Upload failed")
                            })
                    except Exception as e:
                        logger.error(f"Исключение при загрузке '{file.filename}': {e}")
                        attachment_errors.append({
                            "file": file.filename,
                            "error": str(e)
                        })

            if attachment_errors:
                logger.warning(f"Предупреждения по вложениям для задачи {task_gid}: {attachment_errors}")

            logger.info(f"Репорт успешно отправлен: task_gid={task_gid}, ошибок вложений={len(attachment_errors)}")
            return jsonify({
                "success": True,
                "task_gid": task_gid,
                "attachment_warnings": attachment_errors if attachment_errors else None
            })

        logger.info(f"Репорт успешно отправлен: task_gid={task_gid}")
        return jsonify({
            "success": True,
            "task_gid": task_gid
        })

    except Exception as e:
        logger.exception(f"Необработанное исключение в submit_report: {e}")
        return jsonify({
            "error": "server_error",
            "message": str(e)
        }), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    logger.warning("Запрос отклонён: файл слишком большой (413)")
    return jsonify({
        "error": "file_too_large",
        "max_size": "50MB"
    }), 413


@app.errorhandler(415)
def unsupported_media_type(error):
    """Handle unsupported file type error."""
    logger.warning("Запрос отклонён: неподдерживаемый тип файла (415)")
    return jsonify({
        "error": "unsupported_file_type"
    }), 415


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
