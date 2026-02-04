# AWS Deployment (EC2) - GEE-Flood

This is a manual checklist for deploying the Dockerized API on EC2.

## TODO: Launch EC2 instance

- Choose Ubuntu or Amazon Linux.
- Open ports 22 (SSH) and 8000 (API) in the security group.  
  Why it matters: you control network access and can explain least-privilege access.

## TODO: Install Docker on EC2

```bash
sudo apt update
sudo apt install -y docker.io
sudo usermod -aG docker $USER
```

Why it matters: container runtime is required for reproducible deployments.

## TODO: Copy project and build image

```bash
git clone <your_repo_url>
cd gee-flood
docker build -t geeflood-api .
```

Why it matters: building from source demonstrates ownership of the deploy pipeline.

## TODO: Set environment variables

Create a `.env` file on the EC2 instance with the same keys as `.env.example`.

Why it matters: keeping secrets out of code is a core security practice.

## TODO: Run the container

```bash
docker run -d --name geeflood-api --env-file .env -p 8000:8000 geeflood-api
```

Why it matters: runtime configuration is a key MLOps skill.

## Optional: Use AWS RDS for Postgres

- Create an RDS Postgres instance.
- Update `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` in `.env`.

Why it matters: shows you can scale data storage beyond a single VM.
