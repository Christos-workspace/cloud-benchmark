"""
Cloud storage utility module for result uploads.

This module provides a unified interface for uploading files to major cloud
storage platforms—Azure Blob Storage, Amazon S3, and Google Cloud Storage
enabling provider-agnostic handling of scraped result files
in cross-cloud workflows.

Functions:
    upload_file_to_azure_blob(
        local_path,
        dest_blob_name,
        container_name=None,
        connection_string=None,
        data=None
        ):
        Upload a file to Azure Blob Storage.
    upload_file_to_s3(
        local_path,
        dest_key,
        bucket_name=None,
        aws_credentials=None
        ):
        (To be implemented) Upload a file to Amazon S3.
    upload_file_to_gcs(
        local_path,
        dest_blob_name,
        bucket_name=None,
        gcp_credentials=None):
        (To be implemented) Upload a file to Google Cloud Storage.

How to use:
    - Choose the appropriate upload function based on your cloud provider.
    - Provide required credentials and storage parameters either as arguments
      or via environment variables.
    - Extend or modify this module to add support for other storage backends
      or authentication strategies as needed.

Environment Variables:
    Azure:
        AZURE_BLOB_CONTAINER
        AZURE_STORAGE_CONNECTION_STRING
    AWS:
        AWS_ACCESS_KEY_ID
        AWS_SECRET_ACCESS_KEY
        AWS_S3_BUCKET
    GCP:
        GOOGLE_APPLICATION_CREDENTIALS
        GCP_BUCKET

This abstraction enables seamless switching between cloud platforms for result
storage, essential for benchmarking, migration, and multi-cloud deployments.
"""

from azure.storage.blob import BlobServiceClient
import os
from loguru import logger


def upload_file_to_azure_blob(
    dest_blob_name,
    local_path=None,
    data=None,
    container_name=None,
    connection_string=None,
):
    """
    Upload a file or in-memory data to Azure Blob Storage.

    Args:
        dest_blob_name (str): Blob name (path within container).
        local_path (str, optional): Path to the local file.
        data (bytes or file-like, optional): Data to upload directly (in-memory).
        container_name (str, optional): Azure Blob container name.
        connection_string (str, optional): Azure connection string.
    """
    container_name = container_name or os.environ.get("AZURE_BLOB_CONTAINER")
    connection_string = connection_string or os.environ.get(
        "AZURE_STORAGE_CONNECTION_STRING"
    )

    if not container_name or not connection_string or not dest_blob_name:
        raise ValueError(
            "Azure container name, blob name, and connection string must be provided."
        )

    try:
        logger.info(
            f"Uploading to Azure Blob container '{container_name}' as '{
                dest_blob_name
            }'"
        )
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=dest_blob_name
        )

        if data is not None:
            blob_client.upload_blob(data, overwrite=True)
        elif local_path is not None:
            with open(local_path, "rb") as f:
                blob_client.upload_blob(f, overwrite=True)
        else:
            raise ValueError("Either data or local_path must be provided.")

        logger.success(
            f"Upload to Azure Blob '{container_name}/{dest_blob_name}' successful."
        )

    except Exception as e:
        logger.error(f"Failed to upload to Azure Blob: {e}")
        raise
