import json


def lambda_handler(event, context):
    print("Workflow error captured:")
    print(json.dumps(event, default=str))
    return {}
