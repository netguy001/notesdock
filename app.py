from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import json
import logging

# Configuration
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt", "ppt", "pptx", "jpg", "jpeg", "png"}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# Create upload directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE
app.config["SECRET_KEY"] = "your-secret-key-change-this-in-production"

# Enable CORS with specific configuration
CORS(
    app,
    origins=[
        "http://127.0.0.1:5000",
        "http://localhost:5000",
        "http://192.168.79.252:5000",
        "http://0.0.0.0:5000",
    ],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    supports_credentials=True,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for file metadata (use database in production)
files_db = []


# Load existing files if any
def load_files_db():
    global files_db
    db_file = "files_db.json"
    if os.path.exists(db_file):
        try:
            with open(db_file, "r") as f:
                files_db = json.load(f)
                logger.info(f"Loaded {len(files_db)} files from database")
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            files_db = []


# Save files database
def save_files_db():
    db_file = "files_db.json"
    try:
        with open(db_file, "w") as f:
            json.dump(files_db, f, indent=2)
            logger.info("Database saved successfully")
    except Exception as e:
        logger.error(f"Error saving database: {e}")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_size(file_path):
    try:
        return os.path.getsize(file_path)
    except:
        return 0


# Initialize database
def initialize_database():
    load_files_db()
    logger.info("Application initialized")


# Serve the main page
@app.route("/")
def index():
    return render_template("index.html")


# Test endpoint
@app.route("/api/test", methods=["GET", "POST"])
def test():
    logger.info("=== TEST ENDPOINT HIT ===")
    logger.info(f"Method: {request.method}")
    return jsonify(
        {
            "status": "success",
            "method": request.method,
            "message": "Flask backend is working!",
            "timestamp": datetime.now().isoformat(),
        }
    )


# Upload endpoint
@app.route("/api/files", methods=["POST"])
def upload_file():
    logger.info("=== UPLOAD REQUEST RECEIVED ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"Content-Type: {request.content_type}")

    try:
        # Check authorization (simple token check - improve for production)
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or "dummy-token" not in auth_header:
            logger.warning("Unauthorized upload attempt")
            return jsonify({"error": "Unauthorized"}), 401

        # Get form data
        title = request.form.get("title", "").strip()
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        url = request.form.get("url", "").strip()

        logger.info(f"Upload data - Title: '{title}', Subject: '{subject}'")

        # Validate required fields
        if not title or not subject:
            logger.error("Missing required fields")
            return jsonify({"error": "Title and subject are required"}), 400

        # Handle file upload
        if "file" not in request.files:
            logger.error("No file part in request")
            return jsonify({"error": "No file part"}), 400

        uploaded_file = request.files["file"]

        if uploaded_file.filename == "":
            logger.error("No file selected")
            return jsonify({"error": "No file selected"}), 400

        logger.info(f"File received: {uploaded_file.filename}")

        # Validate file type
        if not allowed_file(uploaded_file.filename):
            logger.error(f"File type not allowed: {uploaded_file.filename}")
            return (
                jsonify(
                    {
                        "error": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
                    }
                ),
                400,
            )

        # Generate unique filename
        original_filename = uploaded_file.filename
        file_extension = original_filename.rsplit(".", 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}_{secure_filename(original_filename)}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        logger.info(f"Saving file to: {file_path}")

        # Save the file
        try:
            uploaded_file.save(file_path)
            logger.info("File saved successfully!")
        except Exception as save_error:
            logger.error(f"Error saving file: {save_error}")
            return jsonify({"error": f"Failed to save file: {str(save_error)}"}), 500

        # Verify file was saved and get size
        if not os.path.exists(file_path):
            logger.error("File was not saved properly")
            return jsonify({"error": "File save verification failed"}), 500

        file_size = get_file_size(file_path)
        logger.info(f"File size: {file_size} bytes")

        # Create file record
        file_record = {
            "id": str(uuid.uuid4()),
            "title": title,
            "subject": subject,
            "description": description,
            "url": url,
            "originalName": original_filename,
            "filename": unique_filename,
            "size": file_size,
            "type": file_extension.upper(),
            "uploadDate": datetime.now().isoformat(),
            "unit": title,  # For compatibility with frontend
        }

        # Store in memory and save to file
        files_db.append(file_record)
        save_files_db()

        logger.info(f"File record created with ID: {file_record['id']}")
        logger.info("=== UPLOAD SUCCESSFUL ===")

        return jsonify(file_record), 201

    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# List files endpoint
@app.route("/api/files", methods=["GET"])
def list_files():
    logger.info("=== LIST FILES REQUEST ===")

    try:
        subject_filter = request.args.get("subject")

        if subject_filter:
            filtered_files = [
                f
                for f in files_db
                if f.get("subject", "").lower() == subject_filter.lower()
            ]
            logger.info(
                f"Returning {len(filtered_files)} files for subject: {subject_filter}"
            )
            return jsonify(filtered_files)

        logger.info(f"Returning all {len(files_db)} files")
        return jsonify(files_db)

    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({"error": "Failed to retrieve files"}), 500


# Download file by ID endpoint
@app.route("/api/files/<file_id>/download", methods=["GET"])
def download_file(file_id):
    logger.info(f"=== DOWNLOAD REQUEST for ID: {file_id} ===")

    try:
        # Find file record
        file_record = next((f for f in files_db if f["id"] == file_id), None)
        if not file_record:
            logger.error("File record not found")
            return jsonify({"error": "File not found"}), 404

        filename = file_record.get("filename")
        if not filename:
            logger.error("No filename in record")
            return jsonify({"error": "File not available"}), 404

        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            logger.error(f"Physical file not found: {file_path}")
            return jsonify({"error": "File not found on disk"}), 404

        logger.info(f"Sending file: {file_path}")
        return send_from_directory(
            UPLOAD_FOLDER,
            filename,
            as_attachment=True,
            download_name=file_record["originalName"],
        )

    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({"error": "Failed to download file"}), 500


# Update file endpoint
@app.route("/api/files/<file_id>", methods=["PUT"])
def update_file(file_id):
    logger.info(f"=== UPDATE REQUEST for ID: {file_id} ===")

    try:
        # Check authorization
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or "dummy-token" not in auth_header:
            return jsonify({"error": "Unauthorized"}), 401

        # Find file record
        file_record = next((f for f in files_db if f["id"] == file_id), None)
        if not file_record:
            return jsonify({"error": "File not found"}), 404

        # Get update data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Update fields
        updatable_fields = ["title", "subject", "description", "url"]
        for field in updatable_fields:
            if field in data:
                file_record[field] = data[field]

        # Save database
        save_files_db()

        logger.info("File updated successfully")
        return jsonify(file_record)

    except Exception as e:
        logger.error(f"Error updating file: {e}")
        return jsonify({"error": "Failed to update file"}), 500


# Delete file endpoint
@app.route("/api/files/<file_id>", methods=["DELETE"])
def delete_file(file_id):
    logger.info(f"=== DELETE REQUEST for ID: {file_id} ===")

    try:
        # Check authorization
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or "dummy-token" not in auth_header:
            return jsonify({"error": "Unauthorized"}), 401

        # Find and remove file record
        file_record = next((f for f in files_db if f["id"] == file_id), None)
        if not file_record:
            return jsonify({"error": "File not found"}), 404

        # Delete physical file
        filename = file_record.get("filename")
        if filename:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted physical file: {file_path}")
            except Exception as e:
                logger.warning(f"Error deleting physical file: {e}")

        # Remove from memory and save
        files_db.remove(file_record)
        save_files_db()

        logger.info("File record removed from database")
        return jsonify({"success": True, "message": "File deleted successfully"})

    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({"error": "Failed to delete file"}), 500


# Debug endpoint
@app.route("/api/debug/files", methods=["GET"])
def debug_files():
    logger.info("=== DEBUG REQUEST ===")

    try:
        # List physical files
        physical_files = []
        if os.path.exists(UPLOAD_FOLDER):
            physical_files = [
                f
                for f in os.listdir(UPLOAD_FOLDER)
                if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))
            ]

        debug_info = {
            "upload_folder": os.path.abspath(UPLOAD_FOLDER),
            "folder_exists": os.path.exists(UPLOAD_FOLDER),
            "files_in_memory": len(files_db),
            "physical_files_count": len(physical_files),
            "physical_files": physical_files,
            "memory_files": [
                {
                    "id": f["id"],
                    "filename": f.get("filename"),
                    "originalName": f.get("originalName"),
                    "subject": f.get("subject"),
                    "title": f.get("title"),
                }
                for f in files_db
            ],
            "allowed_extensions": list(ALLOWED_EXTENSIONS),
            "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024),
        }

        logger.info(
            f"Debug info: {len(files_db)} files in memory, {len(physical_files)} physical files"
        )
        return jsonify(debug_info)

    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return jsonify({"error": "Debug endpoint failed"}), 500


# Health check
@app.route("/api/health", methods=["GET"])
def health_check():
    try:
        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "upload_folder": os.path.abspath(UPLOAD_FOLDER),
                "files_count": len(files_db),
                "disk_space_mb": get_disk_space(),
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


def get_disk_space():
    """Get available disk space in MB"""
    try:
        import shutil

        total, used, free = shutil.disk_usage(UPLOAD_FOLDER)
        return round(free / (1024 * 1024), 2)
    except:
        return "unknown"


# Error handlers
@app.errorhandler(413)
def file_too_large(e):
    return (
        jsonify(
            {
                "error": f"File too large. Maximum size is {MAX_FILE_SIZE/(1024*1024):.1f}MB"
            }
        ),
        413,
    )


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "API endpoint not found"}), 404
    return render_template("index.html")  # Serve main page for non-API routes


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("FLASK BACKEND STARTING")
    print(f"Upload folder: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"Max file size: {MAX_FILE_SIZE / (1024*1024):.1f}MB")
    print(f"Allowed extensions: {ALLOWED_EXTENSIONS}")
    print("=" * 50)

    # Load existing data
    initialize_database()

    # Run the app
    app.run(host="0.0.0.0", port=5000, debug=True)
