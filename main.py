
from datetime import datetime
from oauth2client.client import GoogleCredentials
from absl import app, flags, logging
from auxmethods import auxMethods

flags.DEFINE_string(name='project_id',default=None,help='Project ID being used in GCP, Example: gglobo-dbaaslab-dev-qa',required=True)

FLAGS = flags.FLAGS

credentials = GoogleCredentials.get_application_default()

def main(argv):
    print('The value of project id is %s' % FLAGS.project_id)
    print("Initializing copying process... "+datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))

    aux_methods = auxMethods()

    response = aux_methods.getSnapshots(FLAGS.project_id,credentials)

    for snapshot_id in response:
        result_dict = response[snapshot_id]
        #print(result_dict)
        if 'labels' in result_dict:
            print(result_dict['labels'])
    

if __name__ == "__main__": 
    app.run(main)
