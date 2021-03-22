import boto3
from boto3.dynamodb.conditions import Key


def query_actions(action, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')
        #, endpoint_url="http://localhost:8000")

    table = dynamodb.Table('moadsd-ng-reporter')
    response = table.query(
        #KeyConditionExpression=Key('action = :action').eq(action)
        KeyConditionExpression='admin_email = :admin_email',
        ExpressionAttributeValues={
            ':action': {'S': action}
        } #) #.eq('2020-06-09-17-02-01')
    )
    return response['Items']

# def scan_admins(dynamodb=None):
#     if not dynamodb:
#         dynamodb = boto3.resource('dynamodb')

#     table = dynamodb.Table('moadsd-ng-reporter')
#     scan_kwargs = {
#         'ProjectionExpression': "admin, action, datetime"
#     }

#     done = False
#     start_key = None
#     while not done:
#         if start_key:
#             scan_kwargs['ExclusiveStartKey'] = start_key
#         response = table.scan(**scan_kwargs)
#         display_movies(response.get('Items', []))
#         start_key = response.get('LastEvaluatedKey', None)
#         done = start_key is None

if __name__ == '__main__':
    query_action = 'deploy'
    # print(f"Movies from {query_year}")
    actions = query_actions(query_action)
    for action in actions:
        print(action['admin_email'], ":")