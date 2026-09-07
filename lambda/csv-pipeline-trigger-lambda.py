"""
Function name : csv-pipeline-trigger-lambda
Trigger        : S3 event notification on upload-csv-1233219898 (ObjectCreated, suffix .csv)
Purpose        : Starts the Glue Workflow as soon as a CSV lands in the input bucket.

Handles back-to-back uploads: if the crawler is still busy from a previous
upload, this waits (polling every 5s) instead of crashing outright with
CrawlerRunningException. Function timeout must be set to at least 60s in
Lambda's Configuration > General configuration for this wait budget to fit.
"""
import time
import boto3

glue = boto3.client("glue")

CRAWLER_NAME = "csv-pipeline-crawler"
WORKFLOW_NAME = "csv-pipeline-workflow"
START_TRIGGER_NAME = "csv-pipeline-start-trigger"

MAX_WAIT_SECONDS = 50   # keep comfortably under the function's 60s timeout
POLL_INTERVAL_SECONDS = 5


def crawler_is_ready(crawler_name):
    state = glue.get_crawler(Name=crawler_name)["Crawler"]["State"]
    print(f"Crawler state: {state}")
    return state == "READY"


def lambda_handler(event, context):
    print("Received event:", event)

    waited = 0
    while not crawler_is_ready(CRAWLER_NAME) and waited < MAX_WAIT_SECONDS:
        print(f"Crawler busy, waiting {POLL_INTERVAL_SECONDS}s (waited {waited}s so far)...")
        time.sleep(POLL_INTERVAL_SECONDS)
        waited += POLL_INTERVAL_SECONDS

    if not crawler_is_ready(CRAWLER_NAME):
        print(
            f"Crawler still busy after waiting {MAX_WAIT_SECONDS}s. "
            "Skipping this invocation rather than erroring. "
            "The uploaded file remains in the input bucket."
        )
        return {"status": "skipped - crawler busy"}

    glue.start_workflow_run(Name=WORKFLOW_NAME)
    glue.start_trigger(Name=START_TRIGGER_NAME)
    return {"status": "workflow started"}