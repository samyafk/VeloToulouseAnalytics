# VeloToulouseAnalytics
## Setup

Prerequisites: WSL/Linux, Python 3.10+, Java 17 + clone repository

```bash
sudo apt install -y python3-venv openjdk-17-jdk-headless make
sudo apt install gh
git clone https://github.com/samyafk/VeloToulouseAnalytics.git
```
Install required libraries and activate virtual env

```bash
cd VeloToulouseAnalytics
make setup
source .venv/bin/activate
```
Modify the .env file to match your project path

```bash
# Modify this according to your project path
PROJECT_ROOT=...your_project_path
```

## Optional (ignore this if you want to use the example dataset above)
The API for VeloToulouse only provides snapshots at a given time. In order to build a historical dataset, I used a free VM that I ran on Orcale Cloud. It downloads and stores a snapshot each 15 min.

This is how to setup Oracle Cloud permissions on your machine be able to list and get objects.
1. Generate a key pair

```bash
mkdir -p ~/.oci
openssl genrsa -out ~/.oci/oci_api_key.pem 2048
chmod 600 ~/.oci/oci_api_key.pem
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
```

2. In the Console, go to Profile → My profile → API keys → Add API key → Paste a public key, paste the contents of oci_api_key_public.pem, and click Add. Copy the fingerprint it shows.

3. Create ~/.oci/config and paste the following 
```bash
[DEFAULT]
user=ocid1.user.oc1..xxxxxxxx
fingerprint=aa:bb:cc:dd:...
tenancy=ocid1.tenancy.oc1..xxxxxxxx
region=eu-paris-1
key_file=~/.oci/oci_api_key.pem
```