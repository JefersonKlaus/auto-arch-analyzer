"""SES helpers for sending analysis report e-mails."""

import boto3
from botocore.exceptions import ClientError


class SesReportMailer:
    """Sends the generated report by e-mail."""

    def __init__(self, source_email: str, region: str = "us-east-1"):
        if not source_email:
            raise ValueError("SES_FROM_EMAIL environment variable not set")

        self.source_email = source_email
        self.ses_client = boto3.client("ses", region_name=region)

    def send_report_email(self, recipient_email: str, subject: str, text_body: str, html_body: str) -> str:
        try:
            response = self.ses_client.send_email(
                Source=self.source_email,
                Destination={"ToAddresses": [recipient_email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": text_body, "Charset": "UTF-8"},
                        "Html": {"Data": html_body, "Charset": "UTF-8"},
                    },
                },
            )
        except ClientError as exc:
            raise RuntimeError(f"Failed to send report e-mail via SES: {exc}") from exc

        return response.get("MessageId", "")
