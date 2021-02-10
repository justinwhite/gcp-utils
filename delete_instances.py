import argparse
import googleapiclient.discovery
import subprocess
from os.path import basename

def list_zones(compute, project):
  result = compute.zones().list(project=project).execute()
  zones = result['items'] if 'items' in result else []
  return [basename(zone['name']) for zone in zones]

def list_instances(compute, project, zone, service_account, maxResults=50):
  nextPageToken = None
  while True:
    # TODO: Use instances.list(filter=) instead of is_target
    result = compute.instances().list(project=project, zone=zone, maxResults=maxResults, pageToken=nextPageToken).execute()
    items = result['items'] if 'items' in result else []
    yield [x['name'] for x in items if is_target(x.get('serviceAccounts'), service_account)]
    try:
      nextPageToken = result['nextPageToken']
    except KeyError:
      break

def is_target(service_accounts_on_instance, service_account_target):
  if not service_accounts_on_instance:
    return False
  emails = [x['email'] for x in service_accounts_on_instance]
  return service_account_target in emails
    
def main(project, service_account):
  compute = googleapiclient.discovery.build('compute', 'v1')
  # TODO: Use compute.instances().aggregatedList instead of iterating over zones
  for zone in list_zones(compute, project):
    for batch in list_instances(compute, project, zone, service_account):
      if batch:
        print('Deleting %d instances in zone %s' %  (len(batch), zone))
        cmd = ["gcloud", "compute", "instances", "delete"] + batch + ["--zone", zone, "--quiet"]
        # TODO: Use the api directly with request pooling. This example uses gcloud because
        #       it natively handles batch deletes.
        subprocess.run(cmd)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description=__doc__,
      formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('project_id', help='Your Google Cloud project ID.')
  parser.add_argument('service_account', help='Service Account with access to VM.')
  # TODO: add a dry run flag
  args = parser.parse_args()

  main(args.project_id, args.service_account)

