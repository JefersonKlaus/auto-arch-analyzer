import json
from decimal import Decimal


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def success_response(body, status_code=200, encoder=CustomJSONEncoder):
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, PUT, PATCH, POST, DELETE, OPTIONS",
        },
        "body": json.dumps(body, cls=encoder),
    }


def error_response(error_message, status_code=500):
    error_body = error_message if isinstance(error_message, dict) else {"error": error_message}
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, PUT, PATCH, POST, DELETE, OPTIONS",
        },
        "body": json.dumps(error_body, cls=CustomJSONEncoder),
    }
