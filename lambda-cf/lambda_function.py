"""
Function name : csv-pipeline-trigger-lambda-cf
Trigger        : S3 event notification on the CF-managed input bucket (ObjectCreated, suffix .csv)
Purpose        : Starts the Glue Workflow as soon as a CSV lands in the input bucket.

CloudFormation variant of lambda/csv-pipeline-trigger-lambda.py - same two calls,
but the workflow/trigger names come from environment variables set by the
CloudFormation template instead of being hardcoded, and asynchronous retries
are disabled via the template's EventInvokeConfig-free default (set
MaximumRetryAttempts=0 manually if you add one) to avoid colliding workflow runs.
"""
import os
import boto3

glue = boto3.client("glue")

WORKFLOW_NAME = os.environ["WORKFLOW_NAME"]
START_TRIGGER_NAME = os.environ["START_TRIGGER_NAME"]


def lambda_handler(event, context):
    print("Received event:", event)
    glue.start_workflow_run(Name=WORKFLOW_NAME)
    glue.start_trigger(Name=START_TRIGGER_NAME)
    return {"status": "workflow started"}
