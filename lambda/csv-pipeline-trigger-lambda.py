"""
Function name : csv-pipeline-trigger-lambda
Trigger        : S3 event notification on upload-csv-1233219898 (ObjectCreated, suffix .csv)
Purpose        : Starts the Glue Workflow as soon as a CSV lands in the input bucket.

Note: Lambda's asynchronous retry (default: 2 automatic retries on failure) was
turned OFF for this function (Configuration -> Asynchronous invocation ->
Maximum retry attempts = 0). Without this, a single failed invocation would
silently retry itself a few minutes later and start a second, colliding
workflow run.
"""
import boto3

glue = boto3.client("glue")


def lambda_handler(event, context):
    print("Received event:", event)
    glue.start_workflow_run(Name="csv-pipeline-workflow")
    glue.start_trigger(Name="csv-pipeline-start-trigger")
    return {"status": "workflow started"}
