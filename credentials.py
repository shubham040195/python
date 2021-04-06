import os
import subprocess
import json
import boto3


jenkins_master = "localhost:8080"

def GetAwsSecrets(key):
    """Get the credentials from secrets manager"""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name='us-east-1'
    )

    secret_string = client.get_secret_value(SecretId=key)
    
    return secret_string


def GenerateCrumbandToken():
    """ Create Crumb and token for Jenkins api authentication """

    output = subprocess.check_output("curl http://"+jenkins_master+"/crumbIssuer/api/xml?xpath=concat\(//crumbRequestField,%22:%22,//crumb\) \
    -c cookies.txt \
    --user 'admin:admin'", shell=True,stderr= subprocess.STDOUT)


    output=str(output.decode('utf-8'))

    crumb=output.splitlines()

    output = crumb[-1:]

    listToStr = ' '.join(map(str, output))

    cmd = "curl -H "+listToStr+" 'http://"+jenkins_master+"/user/admin/descriptorByName/jenkins.security.ApiTokenProperty/generateNewToken' \
    --data 'newTokenName=kb-token' \
    --user 'admin:admin' \
    -b cookies.txt"

    data = subprocess.check_output(cmd,shell=True)


    token = json.loads(data.decode('utf-8'))

    
    data = {'token':token['data']['tokenValue'],'crumb':listToStr}

    return data

def GenerateSecrets(data,secrets_data):
    if 'Username' in secrets_data['SecretString']:

        secretData = json.loads(secrets_data['SecretString'])

        jsonData = {"": "0","credentials": {"scope": "GLOBAL","id": secrets_data["Name"],"username": secretData["Username"],"password": secretData["Password"],"description": secrets_data["Name"],"$class": "com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl"}}

        cmd= "curl -H "+data['crumb']+" -X POST 'http://admin:"+data['token']+"@"+jenkins_master+"/credentials/store/system/domain/_/createCredentials' --data-urlencode 'json="+json.dumps(jsonData)+"'"

    elif 'Username' not in secrets_data['SecretString']:

        jsonData = {"": "0","credentials": {"scope": "GLOBAL","id": secrets_data["Name"],"secret":secrets_data['SecretString'],"description": secrets_data["Name"],"$class": "org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl"}}

        cmd= "curl -H "+data['crumb']+" -X POST 'http://admin:"+data['token']+"@"+jenkins_master+"/credentials/store/system/domain/_/createCredentials' --data-urlencode 'json="+json.dumps(jsonData)+"'"

    Secrets = subprocess.check_output(str(cmd),shell=True)



if __name__== "__main__":
    try:
        dictOfSecrtes = {"Jenkins-Jira":"jira-cred","slack-jenkins-secret-text":"slack-cred","Bitbucket":"bitbucket-cred"}
        data = GenerateCrumbandToken()
        for key in dictOfSecrtes:
            secrets_data = GetAwsSecrets(key)   # Getting Secrets from Secrets manager
            GenerateSecrets(data,secrets_data)  # Adding credentials in Jenkins store
            print ("Successfully added secrets in Jenkins store:"+key+"")           
    except Exception as ex:
        print(ex)
        raise
