"""
Job name : csv-pipeline-etl-job
Engine   : Python Shell (Glue 3.0, Python 3.9, 1/16 DPU)
Purpose  : Reads the most recently uploaded CSV from the input bucket,
           standardizes null values, writes the result to the output
           bucket, and updates the Glue Data Catalog table.

Null-handling rule:
  - Numeric columns -> fill with 0
  - Text columns    -> fill with "UNKNOWN"

Saved directly through Glue's Script Editor (Save button) so Glue
manages the script's S3 location itself - avoids pointing the job at
a script path that doesn't exist.
"""
import boto3
import pandas as pd
import awswrangler as wr

INPUT_BUCKET = "upload-csv-1233219898"
OUTPUT_BUCKET = "dest-csv-1233219898"
GLUE_DATABASE = "pipeline_db"
OUTPUT_TABLE = "csv_output_data"

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

output_path = f"s3://{OUTPUT_BUCKET}/csv_output_data/"

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
