from tokenize import String
from googleapiclient import discovery

class auxMethods:

    
    def getSnapshots(self,project_id,credentials):
        snapshot_dict = {}

        service = discovery.build( \
            serviceName='compute',\
            version='v1',\
            credentials=credentials\
            )

        request = service.snapshots().list(project=project_id)

        while request is not None:
            response = request.execute()

            for snapshot in response['items']:
                snapshot_dict[snapshot['id']] = snapshot

            request = service.snapshots().list_next(previous_request=request, previous_response=response)

        return snapshot_dict
