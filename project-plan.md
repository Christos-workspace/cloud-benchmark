# Cloud-Benchmark Project Plan: Cross-Cloud Scraping, Benchmarking, and Automation

## Goal

Benchmark and compare the end-to-end performance of running a news scraper container
across Azure, AWS, and GCP using infrastructure as code and automated orchestration,
and collect/compare results.

## High-Level Workflow

1. **Provision Cloud Resources**
   - Use **Terraform** (triggered by Airflow) to provision
     the necessary resources for each provider:
     - Compute (e.g., Azure Container Instance, AWS ECS Fargate/EC2, GCP Cloud Run/VM)
     - Object storage (e.g., Azure Blob Storage, AWS S3, GCP Cloud Storage)
     - Networking as required

2. **Deploy and Run the Scraper Container**
   - Airflow launches the containerized scraper job on the provisioned cloud infrastructure,
     passing required environment variables (for storage credentials, settings, etc.).
   - The scraper:
     - Fetches news articles as per configs
     - Serializes results as JSON
     - Uploads results directly to the configured cloud storage
       (provider-agnostic code, using environment variables)

3. **Post-Processing & Notification**
   - After the job completes and results are uploaded, Airflow:
     - Sends an email notification (or other alert)
     - Records the total elapsed time for the run

4. **Teardown Cloud Resources**
   - Airflow triggers Terraform to destroy the resources,
     ensuring cost control and clean benchmarking.

5. **Benchmark and Comparison**
   - Airflow aggregates timing/results for each provider
   - Generates a summary report comparing provisioning, run, and teardown times

## Architecture Components

- **Airflow (Orchestrator)**
  - Runs locally
  - Controls workflow: provisions infrastructure, deploys scraper,
    handles teardown, collects metrics, sends notifications

- **Terraform**
  - Managed by Airflow locally
  - Provisions/destroys all cloud resources declaratively for each provider

- **Scraper Container**
  - Runs on the cloud (infrastructure provisioned by Terraform)
  - Reads storage credentials/configs from environment variables injected
    by Airflow at launch
  - Uploads results to cloud storage (Azure Blob, S3, or GCS)

- **Credentials/Secrets**
  - Managed centrally in Airflow Variables, Connections, or a Secrets Backend
  - Passed as environment variables to Terraform tasks and scraper containers

- **Results/Benchmarking**
  - Results and timing metrics collected by Airflow and
    stored locally (or in a results bucket)
  - Final report compares performance across all providers

## Project Structure (Recommended)

```
cloud-benchmark/
├── airflow_dags/                # Airflow DAGs for workflow
├── container/                   # Scraper code, Dockerfile, requirements
│   ├── main.py
│   ├── scraper.py
│   ├── models.py
│   ├── storage.py
│   └── Dockerfile
├── terraform/                   # IaC for each provider
│   ├── aws/
│   ├── azure/
│   └── gcp/
├── credentials/                 # (for local dev only, not production)
│   ├── azure.env
│   ├── aws.env
│   └── gcp.env
├── results/                     # Aggregated benchmark results (optional)
│   └── summary_report.md
├── report.py                    # Utility for result comparison/reporting
├── README.md
└── LICENSE
```

## Secrets and Environment Variables Management

- In **production/cloud workflow**:
  - All secrets (cloud credentials, storage connection strings, etc.) are stored
   in Airflow Variables, Connections, or via a Secrets Backend
   (e.g., Azure Key Vault, AWS Secrets Manager).
  - Airflow injects these as environment variables into:
    - The Terraform task/operator (for provisioning/teardown)
    - The container/job that runs the scraper on the cloud
- **.env files** are only for local development/testing.

## Example Airflow DAG Sequence

1. **Terraform Apply** (provision cloud resources)
2. **Run Scraper Container** (with appropriate credentials/config)
3. **Collect Result & Timing**
4. **Notification** (email/slack/etc.)
5. **Terraform Destroy** (teardown resources)
6. **Aggregate & Compare Results** (optional: generate report)

## Best Practices Recap

- **Provider-agnostic scraper code:** All cloud-specific logic is handled via environment/config.
- **No sensitive info in code or Docker images.**
- **All credentials managed by Airflow and injected at runtime.**
- **Terraform resources are ephemeral.**
- **All results are uploaded directly to cloud storage,
  not stored locally in the container.**
- **Airflow is the single orchestrator and secrets manager.**

## Future Extensions

- Add more cloud providers or resource types easily.
- Integrate with more advanced benchmarking/reporting tools.
- Deploy Airflow itself to the cloud for a fully cloud-native workflow.

