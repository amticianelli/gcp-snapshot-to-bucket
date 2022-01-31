# gcp-snapshot-to-bucket
Module developed for exporting GCP disk`s snapshots for the Cloud Storage. 

# Architecture
![alt text](./img/snaptobucket.png)

# Installation

Necessary tools:

    - Python 3.9.5

## Attention

    - The snapshots will only be exported if the following labels are present in the snapshots` labels metadata: 'database_name','infra_name', 'engine', 'created_at'
    - Don't change the parallelism of Futures to more than 8 threads, because it may genereate 503 errors
    - The process will take some time to process, it needs to create an image from the snapshot, and then export to a external image
    - If some error occurs and the

## Modules installation

    - pip install -r requirements.txt

## Program run
    - Run the program with the following command: 
    
``` shell
# Windows    
python main.py  --project_id <GCP PROJECT ID> `
                --bucket_name <BUCKET NAME> `
                --network_project_id <NETWORK PROJECT ID> `
                --network <NETWORK NAME> `
                --export_format <EXPORT FORMAT> `
                --sub_network <SUB NETWORK NAME> `
                --oauth2_json <AUTHENTICATION FILE>

# Linux
python main.py  --project_id <GCP PROJECT ID> \
                --bucket_name <BUCKET NAME> \
                --network_project_id <NETWORK PROJECT ID> \
                --network <NETWORK NAME> \
                --export_format <EXPORT FORMAT> \
                --sub_network <SUB NETWORK NAME> \
                --oauth2_json <AUTHENTICATION FILE>

```

``` shell  
# Example  
python main.py  --project_id gglobo-dbaaslab-dev-qa `
                --bucket_name disksnapshot `
                --network_project_id gglobo-network-hdg-spk-devqa `
                --network vpc-hdg-devqa `
                --export_format vmdk `
                --sub_network us-east1-gglobo-dbaaslab-dev-qa `
                --oauth2_json gglobo-dbaaslab-dev-qa-818ac58925c9.json
```

    - The program will run in parallel, and export all the snapshots through created images using Cloud Build
    - The output pattern will be the following, based on the labels mentioned before: gs://<BUCKET_NAME>/<ENGINE>/<INFRA_NAME>/<DATABASE_NAME>/<SNAPSHOT_NAME>.<FORMAT>
``` shell
# Outputs
gsutil ls gs://disksnapshot
# Result
gs://disksnapshot/cassandra/
gs://disksnapshot/mongodb/
gs://disksnapshot/mongoshard/
```

## Restoring the snapshot

    - The following command will import the file exported back to GCP's image management:

``` shell

gcloud compute images import image-import-test \
    --source-file gs://disksnapshot/cassandra/testepocansicass/testepocansi-cass/gcs-testepocansicass-02-data-4528204939880166151-1641006008.vmdk \
    --project gglobo-dbaaslab-dev-qa \
    --zone us-east1-b \
    --network projects/gglobo-network-hdg-spk-devqa/global/networks/vpc-hdg-devqa \
    --subnet projects/gglobo-network-hdg-spk-devqa/regions/us-east1/subnetworks/us-east1-gglobo-dbaaslab-dev-qa \
    --no-address \
    --data-disk

```