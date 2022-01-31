from importlib.metadata import metadata
from time import sleep
from tokenize import String
from googleapiclient import discovery
from datetime import datetime
from google.cloud.devtools import cloudbuild_v1
from concurrent import futures
from datetime import timedelta
from google.protobuf.duration_pb2 import Duration

class gcpExportSnapshot:

    def __init__(self,project_id,credentials,export_format,bucket_name,network_project_id,network,sub_network,zone,network_zone):
        self.PROJECT_ID = project_id
        self.CREDENTIALS = credentials
        self.EXPORT_FORMAT = export_format
        self.BUCKET_NAME = bucket_name
        self.NETWORK_PROJECT_ID = network_project_id
        self.NETWORK = network
        self.SUB_NETWORK = sub_network
        self.ZONE = zone
        self.NETWORK_ZONE = network_zone

    def checkNecessaryLabels(self,snapshot_label,necessary_labels):
        tags_ok = True
        for label in necessary_labels:
            if not snapshot_label[label]:
                tags_ok = False

        return tags_ok  

    def getObjectFromBucket(self,object_name,bucket_name):
        
        service = discovery.build( 
            serviceName='storage',
            version='v1',
            credentials=self.CREDENTIALS
            )

        request = service.objects().get(project=self.PROJECT_ID)

        response = request.execute()


        return response

    def setBucketObjectLabel(self,snapshot_labels,object_name):
        # Adding the labels to the new created object
        service = discovery.build( 
            serviceName='storage',
            version='v1',
            credentials=self.CREDENTIALS
            )

        bucket_body = {
            'metadata': snapshot_labels
        }

        request = service.objects().update(userProject=self.PROJECT_ID,bucket=self.BUCKET_NAME,object=object_name,body=bucket_body)

        request.execute()

        return request

    def exportImage(self,snapshot_labels,image_name):
        
        client = cloudbuild_v1.services.cloud_build.CloudBuildClient()

        build = cloudbuild_v1.Build()

        object_name = "{}/{}/{}/{}.{}".format(
                                                snapshot_labels['engine'],
                                                snapshot_labels['infra_name'],
                                                snapshot_labels['database_name'],
                                                snapshot_labels['snapshot_name'],
                                                self.EXPORT_FORMAT
                                                )

        # https://cloud.google.com/compute/docs/images/export-image#api
        build.steps = [
                    {
                    "args":[
                        "-timeout=7000s",
                        "-source_image={}".format(image_name),
                        "-client_id=api",
                        "-format={}".format(self.EXPORT_FORMAT),
                        "-destination_uri=gs://{}/{}".format(self.BUCKET_NAME,object_name),
                        "-network=projects/{}/global/networks/{}".format(self.NETWORK_PROJECT_ID,self.NETWORK),
                        "-subnet=projects/{}/regions/{}/subnetworks/{}".format(self.NETWORK_PROJECT_ID,self.ZONE,self.SUB_NETWORK),
                        "-zone={}".format(self.NETWORK_ZONE)
                    ],
                    "name":"gcr.io/compute-image-tools/gce_vm_image_export:release",
                    "env":[
                        "BUILD_ID=$BUILD_ID"
                    ]
                    }
            ]

        # Adjusting timeout for the export (in seconds)

        td = timedelta(minutes=120)
        duration = Duration()
        duration.FromTimedelta(td)

        build.timeout= duration

        operation = client.create_build(project_id=self.PROJECT_ID, build=build)
        # Print the in-progress operation
        print("IN PROGRESS:")
        print(operation.metadata)

        result = operation.result()

        # Set bucket object label

        self.setBucketObjectLabel(snapshot_labels,object_name)

        return result.status

    def createImageFromSnapshot(self,snapshot_name,image_name):

        service = discovery.build( 
            serviceName='compute',
            version='v1',
            credentials=self.CREDENTIALS
            )

        image_body = {
                "kind": "compute#image",
                "name": image_name,
                "sourceSnapshot": "projects/{}/global/snapshots/{}".format(self.PROJECT_ID,snapshot_name),
                "storageLocations": [
                    self.ZONE
                ]
            }

        request = service.images().insert(project=self.PROJECT_ID,body=image_body)
        response = request.execute()

        ### Checking if the resource is ready
        # Variable for knowing if the resource is created or not
        created = False

        request = service.images().get(project=self.PROJECT_ID,image=image_name)

        while created is False:
            response = request.execute()
            if response['status'] == 'READY':
                created = True

            sleep(5)


        return response

    def deleteImage(self,image_name):

        service = discovery.build( 
            serviceName='compute',
            version='v1',
            credentials=self.CREDENTIALS
            )

        request = service.images().delete(project=self.PROJECT_ID,image=image_name)
        response = request.execute()

        return response

    def fixSnapshotLabels(self):

        snapshot_dict = {}

        service = discovery.build( 
            serviceName='compute',
            version='v1',
            credentials=self.CREDENTIALS
            )

        request = service.snapshots().list(
                project=self.PROJECT_ID,
                filter='(labels.backupstatus:*)'
                )

        
        while request is not None:
            response = request.execute()
            if "items" in response:
                for snapshot in response['items']:
                    snapshot_labels = snapshot["labels"]
                    if 'backupstatus' in snapshot_labels:
                        snapshot_labels.pop('backupstatus')
                        snapshot_labels.pop('backuptogcsdate') if 'backuptogcsdate' in snapshot_labels else None
                        self.setSnapshotLabel(snapshot["name"],snapshot['labelFingerprint'],snapshot_labels)

                request = service.snapshots().list_next(previous_request=request, previous_response=response)
            else:
                break

    def getSnapshots(self,necessary_labels):
        snapshot_dict = {}
        query = ""

        service = discovery.build( 
            serviceName='compute',
            version='v1',
            credentials=self.CREDENTIALS
            )

        for i in necessary_labels:
            query+='(labels.'+i+':*) '

        request = service.snapshots().list(
                project=self.PROJECT_ID,filter="""
                    {}
                """.format(query)
                )

        
        while request is not None:
            response = request.execute()
            if "items" in response:
                for snapshot in response['items']:
                    snapshot_labels = snapshot["labels"]
                    if ('backupstatus' not in snapshot_labels or (snapshot_labels['backupstatus'] not in ['senttobucket','copying'])):
                        snapshot_dict[snapshot['id']] = snapshot

                request = service.snapshots().list_next(previous_request=request, previous_response=response)
            else:
                break
        return snapshot_dict

    def setSnapshotLabel(self,resource,label_fingerprint,snapshot_labels):
        service = discovery.build( 
            serviceName='compute',
            version='v1',
            credentials=self.CREDENTIALS
            )

        # Tag com o status
        global_set_labels_request_body = {
            "labels" : snapshot_labels,
            "labelFingerprint" : label_fingerprint
        }

        request = service.snapshots().setLabels(project=self.PROJECT_ID, resource=resource, body=global_set_labels_request_body)
        response = request.execute()

        # TODO: Change code below to process the `response` dict:
        return response

    def getSnapshotLabelFingerprint(self,snapshot_name):

        service = discovery.build('compute', 'v1', credentials=self.CREDENTIALS)

        request = service.snapshots().get(project=self.PROJECT_ID, snapshot=snapshot_name)
        
        response = request.execute()

        return response['labelFingerprint']

    def copySnapshotToBucket(self,snapshot):
        
        if 'labels' not in snapshot:
            snapshot["labels"]={} 
            
        snapshot_labels = snapshot["labels"] # Aux dict to hel to iterate

        print('Snapshot to be copied: '+snapshot["name"])

        ###
        ## Change the tag "backupstatus" to "copying", so other process won't copy the same snapshot
        ###
        print('Set snapshot label to copying...')

        snapshot_labels["backupstatus"] = "copying"
        response = self.setSnapshotLabel(
            snapshot["name"],
            snapshot["labelFingerprint"],
            snapshot_labels
        )
        print(response)

        ###
        ## Creating the image using the snapshot
        ###
        print('Creating image...')

        image_name = snapshot["name"]

        response = self.createImageFromSnapshot(snapshot["name"],image_name)
        print(response)

        ###
        ## Exporting the image to an GCS bucket
        ###

        print('Exporting image to GCS')
        
        response = self.exportImage(
            snapshot_labels=snapshot_labels,
            image_name=image_name,
            )
            
        print(response)
        
        ###
        ## Deleting the image
        ###
        print('Deleting image...')

        response = self.deleteImage(image_name)
        print(response)

        ###
        ## Set the tag "backupstatus" as "senttobucket" and "backuptogcsdate" as the CURRENT_DATE
        ###
        print('Chagen label to senttobucket')
        snapshot_labels["backupstatus"] = "senttobucket"
        snapshot_labels["backuptogcsdate"] = datetime.today().strftime('%Y-%m-%d-%H_%M_%S')

        # Setting new fingerprint
        snapshot["labelFingerprint"] = self.getSnapshotLabelFingerprint(snapshot["name"])

        response = self.setSnapshotLabel(\
                snapshot["name"],\
                snapshot["labelFingerprint"],\
                snapshot_labels \
            )
        print(response)

    def initCopy(self):

        # List of necessary tags for the filter
        necessary_labels = ['database_name','infra_name', 'engine', 'cretate_at']

        response = self.getSnapshots(necessary_labels) # Brings only the snapshots that were not migrated yet

        # Parallel Pooling:
        pool = futures.ThreadPoolExecutor(max_workers=8)
        move_ok=[]

        # Set a new tag for the snapshots
        for snapshot_id in response:
            snapshot = response[snapshot_id]
            ###
            ## Checking if the labels key exists in the dictionary, if not, add it
            ###
                       
            snapshot_labels = snapshot["labels"]
                
            if 'backupstatus' not in snapshot_labels:
                snapshot_labels["backupstatus"]=""

            if 'snapshot_name' not in snapshot_labels:
                snapshot_labels["snapshot_name"]= snapshot["name"]


            if self.checkNecessaryLabels(snapshot_labels,necessary_labels):
                
                moved = pool.submit(self.copySnapshotToBucket,snapshot)
                move_ok.append(moved)
                
            else:
                print('Empty value for labels for the snapshot: '+snapshot['name'])
                        
        # (END) for   

        futures.wait(move_ok)

