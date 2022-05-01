import boto3
from datetime import datetime

TASK_NAMES=[
    "task-name-1",
    "task-name-2"
]
CLUSTER_NAME="cluster-name-1"
SERVICE_NAME="backend-service-name"


def lambda_handler(event, context):
    
    pipeline = boto3.client('codepipeline')
    ecs = boto3.client('ecs', region_name="eu-west-2")

    pipelineId=event["CodePipeline.job"]["id"]

    try :
        #get the ECR ARN of the latest build
        services=ecs.list_services(
            cluster=CLUSTER_NAME,
            launchType="FARGATE"
        )

        services=services["serviceArns"]

        services=list(filter(lambda x : (SERVICE_NAME in x) ,services))

        description=ecs.describe_services(
            cluster=CLUSTER_NAME,
            services=services
        )

        definition=description["services"][0]["taskDefinition"]

        taskDefinition=ecs.describe_task_definition(
            taskDefinition=definition
        )

        imageARN=taskDefinition["taskDefinition"]["containerDefinitions"][0]["image"]

        for name in TASK_NAMES :
            taskArns=ecs.list_task_definitions(
                familyPrefix=name
            )
            taskArn=taskArns["taskDefinitionArns"][-1]

            taskDefinition=ecs.describe_task_definition(taskDefinition=taskArn)
            taskDefinition=taskDefinition["taskDefinition"]

            taskDefinition["containerDefinitions"][0]["image"]=imageARN

            ecs.register_task_definition(
                family=taskDefinition["family"],
                taskRoleArn=taskDefinition["taskRoleArn"],
                executionRoleArn=taskDefinition["executionRoleArn"],
                networkMode=taskDefinition["networkMode"],
                containerDefinitions=taskDefinition["containerDefinitions"],
                volumes=taskDefinition["volumes"],
                placementConstraints=taskDefinition["placementConstraints"],
                requiresCompatibilities=taskDefinition["requiresCompatibilities"],
                cpu=taskDefinition["cpu"],
                memory=taskDefinition["memory"],
            )

        pipeline.put_job_success_result(
            jobId=pipelineId
        )

    except Exception as e:
        print(e)
        pipeline.put_job_failure_result(
            jobId=pipelineId,
            failureDetails={
                'type': 'JobFailed',
                'message': e
            }
        )
        
    return