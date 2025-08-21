"""
Azure Benchmark Airflow DAG
---------------------------
This DAG provisions Azure resources using Terraform, pushes a Docker image to Azure Container Registry,
deploys the container instance to run a scraper, waits for output, destroys resources, and generates a markdown benchmark report.

Steps:
1. Record DAG start time.
2. Provision resources with Terraform.
3. Store Azure info from outputs as Airflow Variables.
4. Push scraper Docker image to Azure Container Registry.
5. Deploy Azure Container Instance with the scraper.
6. Wait for output blob.
7. Destroy all resources.
8. Generate a markdown report with timing and resource info.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.python import PythonSensor
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.bash import BashOperator
from airflow.hooks.base import BaseHook
from docker.types import Mount
from airflow.models import Variable
from datetime import datetime, timedelta
import json
import logging
import os
from azure.storage.blob import BlobServiceClient

# Get Azure connection info from Airflow Connection "azure_terraform"
azure_conn = BaseHook.get_connection("azure_terraform")

ARM_CLIENT_ID = azure_conn.login
ARM_CLIENT_SECRET = azure_conn.password
ARM_TENANT_ID = azure_conn.extra_dejson.get("tenantId")
ARM_SUBSCRIPTION_ID = azure_conn.extra_dejson.get("subscriptionId")

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}


def set_azure_vars(**context):
    """
    Loads Terraform outputs and saves essential Azure resource info as Airflow Variables.
    """
    outputs_path = "/opt/airflow/terraform/azure/outputs.json"
    with open(outputs_path, "r") as f:
        outputs = json.load(f)
    connection_string = outputs["storage_account_connection_string"]["value"]
    container_name = outputs["blob_container_name"]["value"]

    # Store connection info for other tasks
    Variable.set("AZURE_STORAGE_CONNECTION_STRING", connection_string)
    Variable.set("AZURE_BLOB_CONTAINER", container_name)
    Variable.set("ACR_LOGIN_SERVER", outputs["acr_login_server"]["value"])
    Variable.set("ACR_ADMIN_USERNAME", outputs["acr_admin_username"]["value"])
    Variable.set("ACR_ADMIN_PASSWORD", outputs["acr_admin_password"]["value"])

    # Save essential resource info for reporting
    Variable.set(
        "AZURE_RESOURCE_GROUP_NAME",
        outputs.get("resource_group_name", {}).get("value", ""),
    )
    Variable.set(
        "AZURE_STORAGE_ACCOUNT_NAME",
        outputs.get("storage_account_name", {}).get("value", ""),
    )
    Variable.set(
        "AZURE_ACR_LOGIN_SERVER", outputs.get("acr_login_server", {}).get("value", "")
    )
    acr_login_server = outputs.get("acr_login_server", {}).get("value", "")
    Variable.set(
        "AZURE_DOCKER_IMAGE", f"{acr_login_server}/cloudbenchmark-scraper:latest"
    )


def check_blob_exists(**context):
    """
    Checks if 'articles.json' exists in the Azure blob container.
    Used by PythonSensor to wait for scraper output.
    """
    AZURE_CONNECTION_STRING = Variable.get("AZURE_STORAGE_CONNECTION_STRING")
    BLOB_CONTAINER = Variable.get("AZURE_BLOB_CONTAINER")
    blob_service_client = BlobServiceClient.from_connection_string(
        AZURE_CONNECTION_STRING
    )
    container_client = blob_service_client.get_container_client(BLOB_CONTAINER)
    blob_list = [b.name for b in container_client.list_blobs()]
    logging.info(f"Blobs found in container '{BLOB_CONTAINER}': {blob_list}")
    return "articles.json" in blob_list


def record_start_time(**context):
    """Records the start time of the DAG run (UTC) as an Airflow Variable."""
    start_time = datetime.utcnow().isoformat()
    Variable.set("AZURE_RUN_START_TIME", start_time)
    logging.info(f"DAG start time recorded: {start_time}")


def generate_report(**context):
    """
    Generates a markdown report of DAG run timing and essential Azure resource info.
    Saves report to the project root as 'azure_run_report.md'.
    """
    end_time = datetime.utcnow()
    start_time_str = Variable.get("AZURE_RUN_START_TIME", None)
    start_time = datetime.fromisoformat(start_time_str) if start_time_str else None
    elapsed = end_time - start_time if start_time else None

    resource_group = Variable.get("AZURE_RESOURCE_GROUP_NAME", "")
    storage_account = Variable.get("AZURE_STORAGE_ACCOUNT_NAME", "")
    blob_container = Variable.get("AZURE_BLOB_CONTAINER", "")
    acr_login_server = Variable.get("AZURE_ACR_LOGIN_SERVER", "")
    docker_image = Variable.get("AZURE_DOCKER_IMAGE", "")

    report_lines = [
        "# Azure Deployment Benchmark Report",
        "",
        f"**Start Time:** {start_time.isoformat() if start_time else 'N/A'}",
        f"**End Time:**   {end_time.isoformat()}",
        f"**Total Elapsed Time:** {str(elapsed) if elapsed else 'N/A'}",
        "",
        "## Resources",
        "",
        f"- Resource Group: `{resource_group}`",
        f"- Storage Account: `{storage_account}`",
        f"- Blob Container: `{blob_container}`",
        f"- Container Registry: `{acr_login_server}`",
        f"- Docker Image: `{docker_image}`",
        "",
        "## Steps",
        "",
        "- Terraform provisioned resources",
        "- Docker image pushed to ACR",
        "- Container group deployed and scraper ran",
        "- Resources destroyed",
        "",
        "*This report was auto-generated by Airflow DAG `azure_workflow_dag`.*",
    ]
    report_md = "\n".join(report_lines)
    report_path = os.path.join(os.path.dirname(__file__), "..", "azure_run_report.md")
    # Ensure absolute path in project root
    report_path = os.path.abspath(report_path)
    with open(report_path, "w") as f:
        f.write(report_md)
    logging.info(f"Azure benchmark report written to {report_path}")


with DAG(
    dag_id="azure_workflow_dag",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    # 1. Record DAG start time
    record_start = PythonOperator(
        task_id="record_start_time",
        python_callable=record_start_time,
    )

    # 2. Provision Azure resources with Terraform (without container group)
    provision_azure = DockerOperator(
        task_id="terraform_apply_acr",
        image="hashicorp/terraform:light",
        api_version="auto",
        entrypoint="/bin/sh",
        command="-c 'terraform init && terraform apply -auto-approve -var=\"create_container_group=false\" && terraform output -json > outputs.json'",
        working_dir="/opt/airflow/terraform/azure",
        mounts=[
            Mount(
                source="/home/dataframed/projects/personal-projects/cloud-benchmark/terraform/azure",
                target="/opt/airflow/terraform/azure",
                type="bind",
            )
        ],
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        environment={
            "TF_VAR_client_id": ARM_CLIENT_ID,
            "TF_VAR_client_secret": ARM_CLIENT_SECRET,
            "TF_VAR_tenant_id": ARM_TENANT_ID,
            "TF_VAR_subscription_id": ARM_SUBSCRIPTION_ID,
        },
    )

    # 3. Store Azure info from outputs as Airflow Variables
    set_azure_variables = PythonOperator(
        task_id="set_azure_vars",
        python_callable=set_azure_vars,
    )

    # 4. Push scraper Docker image to Azure Container Registry
    acr_login_server = "{{ var.value.ACR_LOGIN_SERVER }}"
    acr_admin_username = "{{ var.value.ACR_ADMIN_USERNAME }}"
    acr_admin_password = "{{ var.value.ACR_ADMIN_PASSWORD }}"
    acr_image_ref = "{{ var.value.ACR_LOGIN_SERVER }}/cloudbenchmark-scraper:latest"

    push_image_to_acr = BashOperator(
        task_id="push_image_to_acr",
        bash_command=f"""
          docker login {acr_login_server} -u {acr_admin_username} -p {acr_admin_password} &&
          docker tag chrisworkspace/cloudbenchmark-scraper:latest {acr_image_ref} &&
          docker push {acr_image_ref}
        """,
    )

    # 5. Deploy Azure Container Instance with scraper
    deploy_command = (
        "-c 'terraform apply -auto-approve "
        '-var="create_container_group=true" '
        '-var="docker_image={{ var.value.ACR_LOGIN_SERVER }}/cloudbenchmark-scraper:latest"\''
    )
    deploy_container_group = DockerOperator(
        task_id="terraform_apply_container_group",
        image="hashicorp/terraform:light",
        api_version="auto",
        entrypoint="/bin/sh",
        command=deploy_command,
        working_dir="/opt/airflow/terraform/azure",
        mounts=[
            Mount(
                source="/home/dataframed/projects/personal-projects/cloud-benchmark/terraform/azure",
                target="/opt/airflow/terraform/azure",
                type="bind",
            )
        ],
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        environment={
            "TF_VAR_client_id": ARM_CLIENT_ID,
            "TF_VAR_client_secret": ARM_CLIENT_SECRET,
            "TF_VAR_tenant_id": ARM_TENANT_ID,
            "TF_VAR_subscription_id": ARM_SUBSCRIPTION_ID,
        },
    )

    # 6. Wait for output blob from scraper
    wait_for_blob = PythonSensor(
        task_id="wait_for_scraped_data",
        python_callable=check_blob_exists,
        poke_interval=60,  # Check every 60 seconds
        timeout=60 * 30,  # Timeout after 30 minutes
        mode="poke",
    )

    # 7. Destroy all resources
    destroy_azure = DockerOperator(
        task_id="terraform_destroy",
        image="hashicorp/terraform:light",
        api_version="auto",
        entrypoint="/bin/sh",
        command="-c 'terraform destroy -auto-approve'",
        working_dir="/opt/airflow/terraform/azure",
        mounts=[
            Mount(
                source="/home/dataframed/projects/personal-projects/cloud-benchmark/terraform/azure",
                target="/opt/airflow/terraform/azure",
                type="bind",
            )
        ],
        auto_remove=True,
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        trigger_rule="all_success",
        environment={
            "TF_VAR_client_id": ARM_CLIENT_ID,
            "TF_VAR_client_secret": ARM_CLIENT_SECRET,
            "TF_VAR_tenant_id": ARM_TENANT_ID,
            "TF_VAR_subscription_id": ARM_SUBSCRIPTION_ID,
        },
    )

    # 8. Generate markdown report with timing and resource info
    generate_report_task = PythonOperator(
        task_id="generate_report",
        python_callable=generate_report,
        trigger_rule="all_success",
    )

# DAG task order: strictly sequential
(
    record_start
    >> provision_azure
    >> set_azure_variables
    >> push_image_to_acr
    >> deploy_container_group
    >> wait_for_blob
    >> destroy_azure
    >> generate_report_task
)
