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
from azure.storage.blob import BlobServiceClient


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
    outputs_path = "/opt/airflow/terraform/azure/outputs.json"
    with open(outputs_path, "r") as f:
        outputs = json.load(f)
    connection_string = outputs["storage_account_connection_string"]["value"]
    container_name = outputs["blob_container_name"]["value"]
    Variable.set("AZURE_STORAGE_CONNECTION_STRING", connection_string)
    Variable.set("AZURE_BLOB_CONTAINER", container_name)
    Variable.set("ACR_LOGIN_SERVER", outputs["acr_login_server"]["value"])
    Variable.set("ACR_ADMIN_USERNAME", outputs["acr_admin_username"]["value"])
    Variable.set("ACR_ADMIN_PASSWORD", outputs["acr_admin_password"]["value"])


def check_blob_exists(**context):
    AZURE_CONNECTION_STRING = Variable.get("AZURE_STORAGE_CONNECTION_STRING")
    BLOB_CONTAINER = Variable.get("AZURE_BLOB_CONTAINER")
    blob_service_client = BlobServiceClient.from_connection_string(
        AZURE_CONNECTION_STRING
    )
    container_client = blob_service_client.get_container_client(BLOB_CONTAINER)
    blob_list = [b.name for b in container_client.list_blobs()]
    logging.info(f"Blobs found in container '{BLOB_CONTAINER}': {blob_list}")
    return "articles.json" in blob_list


with DAG(
    dag_id="azure_workflow_dag",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
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
    set_azure_variables = PythonOperator(
        task_id="set_azure_vars",
        python_callable=set_azure_vars,
    )

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

    wait_for_blob = PythonSensor(
        task_id="wait_for_scraped_data",
        python_callable=check_blob_exists,
        poke_interval=60,  # Check every 60 seconds
        timeout=60 * 30,  # Timeout after 30 minutes
        mode="poke",
    )

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
(
    provision_azure
    >> set_azure_variables
    >> push_image_to_acr
    >> deploy_container_group
    >> wait_for_blob
    >> destroy_azure
)
