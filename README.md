# cloud-benchmark

## Overview

**cloud-benchmark** is a multi-cloud benchmarking and learning project. It demonstrates how to orchestrate the deployment, execution, and cleanup of cloud resources and container workloads using modern DevOps tools. The project is designed for hands-on practice and comparison of workflows across Azure, AWS, and GCP.

---

## Technologies

- **Python:** Web scraping and data modeling
- **Azure:** Blob storage, Container Registry, Container Instances
- **Docker:** Containerization of the scraper
- **Terraform:** Infrastructure as Code for resource provisioning
- **Apache Airflow:** Workflow orchestration and benchmarking

---

## Project Workflow

1. **Web Scraper Development (`container/`):**
   - Implemented a Python script to scrape news articles (see `scraper.py`, `models.py`).
   - Structured results using Pydantic models.

2. **Azure Blob Upload:**
   - Extended the scraper to upload results directly to Azure Blob Storage (see `storage.py`).

3. **Dockerization:**
   - Containerized the scraper application with a custom Dockerfile.
   - Managed dependencies with `requirements.txt`.

4. **Terraform Infrastructure:**
   - Defined all required Azure resources (resource group, storage, container registry, container group) in the `terraform/azure/` directory.
   - Parameterized resource creation for staged benchmarking.

5. **Airflow Orchestration:**
   - Created a DAG to automate the workflow: provision resources, push Docker image, deploy container group, monitor scraping completion, cleanup resources, and generate a markdown report.
   - Benchmarked Azure deployment time and saved results in a project-level report.

---

## Setup Instructions

1. **Clone the repository**
2. **Configure Azure credentials:** (Service Principal, secrets, etc.)
3. **Build and test the scraper locally (`container/`):**
   - `python main.py` (requires Python 3.7+, see `requirements.txt`)
4. **Build Docker image:**
   - `docker build -t cloudbenchmark-scraper container/`
5. **Run Terraform:**
   - Configure `.tfvars` and deploy resources (`terraform/azure/`)
6. **Launch Airflow environment:**
   - Use `docker-compose.yaml` to start Airflow.
   - Trigger the DAG for Azure benchmarking.

---

## Directory Structure

```bash
cloud-benchmark/
├── azure_run_report.md
├── container/
│   ├── Dockerfile
│   ├── main.py
│   ├── models.py
│   ├── requirements.txt
│   ├── scraper.py
│   ├── storage.py
├── credentials/
│   ├── aws.env
│   ├── azure.env
│   ├── gcp.env
│   ├── gmail.env
├── dags/
│   └── azure_workflow_dag.py
├── docker-compose.yaml
├── LICENSE
├── README.md
├── requirements.txt
├── terraform/
│   ├── aws/
│   │   └── main.tf
│   ├── azure/
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   ├── outputs.json
│   │   ├── provider.tf
│   │   ├── terraform.tfvars
│   │   ├── variables.tf
│   │   ├── versions.tf
│   ├── gcp/
│   │   └── main.tf
```
---

## Benchmarking and Reporting

- The Airflow DAG generates a markdown report (`azure_run_report.md`) summarizing resource details and elapsed deployment time.
- Reports are stored in the project root for future comparison across providers.

---

## Progress & Next Steps

- [x] Azure workflow implemented and benchmarked
- [x] Scraper container deployed and results uploaded to Azure Blob
- [x] Infrastructure provisioned/destroyed via Terraform
- [x] Workflow orchestrated and benchmarked with Airflow

**Next goals:**
- [ ] Implement AWS workflow (Terraform, container registry, ECS/EKS, S3)
- [ ] Implement GCP workflow (Terraform, Artifact Registry, Cloud Run, GCS)
- [ ] Aggregate benchmark reports for all cloud providers
- [ ] Analyze and visualize results
- [ ] Polish documentation and add troubleshooting section

---

## License

MIT License

---

## Author

Christos  
GitHub: [Christos-workspace](https://github.com/Christos-workspace)
