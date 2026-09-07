"""
Job name : csv-pipeline-etl-job-cf
Engine   : Python Shell (Glue 3.0, Python 3.9, 1/16 DPU)
Purpose  : Reads the most recently uploaded CSV from the input bucket,
           standardizes null values, writes the result to the output
           bucket, and updates the Glue Data Catalog table.

CloudFormation variant of glue/csv-pipeline-etl-job.py - bucket/database/table
names come from --INPUT_BUCKET / --OUTPUT_BUCKET / --GLUE_DATABASE /
--OUTPUT_TABLE job arguments (set as DefaultArguments in the CFN template)
instead of being hardcoded, so the same script works for any stack.

Null-handling rule:
  - Numeric columns -> fill with 0
  - Text columns    -> fill with "UNKNOWN"
"""
import sys
from awsglue.utils import getResolvedOptions
import pandas as pd
import awswrangler as wr
import boto3

args = getResolvedOptions(
    sys.argv, ["INPUT_BUCKET", "OUTPUT_BUCKET", "GLUE_DATABASE", "OUTPUT_TABLE"]
)
INPUT_BUCKET = args["INPUT_BUCKET"]
OUTPUT_BUCKET = args["OUTPUT_BUCKET"]
GLUE_DATABASE = args["GLUE_DATABASE"]
OUTPUT_TABLE = args["OUTPUT_TABLE"]

s3 = boto3.client("s3")

# Find the most recently uploaded CSV in the input bucket
response = s3.list_objects_v2(Bucket=INPUT_BUCKET)
csv_objects = [
    obj for obj in response.get("Contents", [])
    if obj["Key"].endswith(".csv")
]
latest = max(csv_objects, key=lambda o: o["LastModified"])
input_key = latest["Key"]

print(f"Processing s3://{INPUT_BUCKET}/{input_key}")

df = pd.read_csv(f"s3://{INPUT_BUCKET}/{input_key}")

# Standardize nulls per column type, not blanket-wide
for col in df.columns:
    if pd.api.types.is_numeric_dtype(df[col]):
        df[col] = df[col].fillna(0)
    else:
        df[col] = df[col].fillna("UNKNOWN")

remaining_nulls = df.isnull().sum().sum()
print(f"Remaining nulls after fill: {remaining_nulls}")

output_path = f"s3://{OUTPUT_BUCKET}/{OUTPUT_TABLE}/"

# Writes the transformed CSV to S3 AND creates/updates the Glue Catalog
# table in the same call (mode="overwrite" requires s3:DeleteObject on
# the output bucket, since it deletes prior files at this path first).
wr.s3.to_csv(
    df=df,
    path=output_path,
    dataset=True,
    database=GLUE_DATABASE,
    table=OUTPUT_TABLE,
    mode="overwrite",
)

print(f"Wrote transformed data to {output_path} and updated table {OUTPUT_TABLE}")
