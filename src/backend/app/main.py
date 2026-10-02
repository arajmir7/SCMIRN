import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import create_app


if __name__ == "__main__":
    config_name = os.getenv("APP_CONFIG", "development")
    app = create_app(config_name)
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode)
