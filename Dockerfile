FROM python:latest

USER root

RUN apt update -y
RUN apt install curl -y

RUN /bin/sh -c "$(curl -fsSL https://raw.githubusercontent.com/turbot/steampipe/main/scripts/install.sh)"

ARG user=steampipe
ARG group=steampipe
ARG uid=9999
ARG gid=9999

RUN groupadd -g ${gid} ${group}
RUN useradd -u ${uid} -g ${group} -s /bin/sh -m ${user}

USER ${uid}:${gid}
    
RUN steampipe plugin install steampipe aws theapsgroup/gitlab # azure gcp azuread kubernetes

RUN steampipe plugin update --all

WORKDIR /home/steampipe

RUN  git clone --depth 1 https://github.com/turbot/steampipe-mod-aws-compliance.git 
RUN  git clone --depth 1 https://github.com/turbot/steampipe-mod-azure-compliance.git 
RUN  git clone --depth 1 https://github.com/turbot/steampipe-mod-gcp-compliance.git 
RUN  git clone --depth 1 https://github.com/turbot/steampipe-mod-kubernetes-compliance.git 

COPY . .

COPY requirements.txt .

RUN pip3 install -r requirements.txt
RUN pip3 install --upgrade requests

ENV STEAMPIPE_DATABASE_START_TIMEOUT=300

# Replace with actual entrypoint later
# ENTRYPOINT ["python", "run_aws_steampipe.py"]
