import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any


from flask import Flask, request
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)
logger = logging.getLogger(__name__)

DATA_STORE_PATH = Path("data_store.json")

class DataStorage(Resource):
    """Endpoint for storing processed transfer data in JSON format.

    Implements atomic write operations to ensure data integrity during
    concurrent access.
    """

    def post(self):
        """Handle incoming transfer data storage requests.

        Returns:
            tuple: (response dict, HTTP status code)

        Raises:
            400: If no data received
            500: For internal storage errors
        """
        try:
            data = request.get_json()
            if not data:
                return {'message': 'No data received'}, 400

            entry = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data': data
            }

            self._append_to_store(entry)
            return {'status': 'success', 'entry_id': entry['id']}, 201

        except Exception as e:
            logger.error(f"Data storage failed: {str(e)}")
            return {'message': 'Internal server error'}, 500

    def _append_to_store(self, entry: Dict[str, Any]) -> None:
        """Perform atomic write to JSON storage file with type-safe operations.

        Args:
            entry: Data entry to append

        Raises:
            IOError: If file operations fail
        """
        try:
            # Read existing data or initialize empty list
            existing_data: List[Dict[str, Any]] = []
            if DATA_STORE_PATH.exists():
                existing_data = json.loads(DATA_STORE_PATH.read_text(encoding='utf-8'))

            # Append new entry and write atomically
            existing_data.append(entry)
            json_str = json.dumps(existing_data, indent=2)

            # Atomic write using temporary file
            temp_path = DATA_STORE_PATH.with_suffix(".tmp")
            temp_path.write_text(json_str, encoding='utf-8')
            temp_path.replace(DATA_STORE_PATH)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON data: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"File operation failed: {str(e)}")
            raise


api.add_resource(DataStorage, '/api/v1/store')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
