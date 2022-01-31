
from datetime import datetime
from oauth2client.client import GoogleCredentials
from absl import app, flags
from auxmethods import gcpExportSnapshot
import google.auth

"""
    Usage:
        python main.py --project_id gglobo-dbaaslab-dev-qa `
                       --bucket_name disksnapshot `
                       --network_project_id gglobo-network-hdg-spk-devqa `
                       --network vpc-hdg-devqa `
                       --export_format vmdk `
                       --sub_network us-east1-gglobo-dbaaslab-dev-qa `
                       --oauth2_json gglobo-dbaaslab-dev-qa-818ac58925c9.json
""" 

flags.DEFINE_string(name='project_id',default=None,help='Project ID being used in GCP, Example: gglobo-dbaaslab-dev-qa',required=True)
flags.DEFINE_string(name='bucket_name',default=None,help='Destination bucket name. Ex: disksnapshot',required=True)
flags.DEFINE_string(name='export_format',default=None,help='vmdk, vhdx, vpc, vdi, and qcow2',required=True)
flags.DEFINE_string(name='network_project_id',default=None,help='Network project id',required=True)
flags.DEFINE_string(name='network',default=None,help='Network destination',required=True)
flags.DEFINE_string(name='sub_network',default=None,help='Sub-Network destination',required=True)
flags.DEFINE_string(name='zone',default='us-east1',help='Zone Default to us-east1')
flags.DEFINE_string(name='network_zone',default='us-east1-b',help='Zone Default to us-east1-b')
flags.DEFINE_string(name='oauth2_json',default=None,help='Authentication JSON file path. Ex: gglobo-dbaaslab-dev-qa-818ac58925c9.json',required=True)

FLAGS = flags.FLAGS

def main(argv):

    print('The value of project id is %s' % FLAGS.project_id)
    print("Initializing copying process... "+datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))


    # Defining credentials
    credentials, project_id = google.auth.load_credentials_from_file(FLAGS.oauth2_json)
    credentials = GoogleCredentials.from_stream(FLAGS.oauth2_json)

    aux_methods = gcpExportSnapshot(
        project_id=FLAGS.project_id,
        credentials=credentials,
        export_format=FLAGS.export_format,
        bucket_name=FLAGS.bucket_name,
        network_project_id=FLAGS.network_project_id,
        network=FLAGS.network,
        sub_network=FLAGS.sub_network,
        zone=FLAGS.zone,
        network_zone=FLAGS.network_zone
    )


    aux_methods.initCopy()

    #aux_methods.fixSnapshotLabels()   

if __name__ == "__main__": 
    app.run(main)
