from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_iam as iam,
    aws_lex as lex,
    aws_cloudfront_origins as origins,
    aws_dynamodb as dynamodb,
    CfnOutput,
    App,
    Environment,
    Fn,
    custom_resources as cr,
    CfnOutput,
    aws_s3_deployment as s3_deployment
)
from .lex_bot import create_lex_bot
from constructs import Construct
import os
from dotenv import load_dotenv

load_dotenv()

class AwsLexChatbotStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # DynamoDB Tables
        bookings_table = dynamodb.Table(self, "BookingsTable",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING)
        )

        rooms_table = dynamodb.Table(self, "RoomsTable",
            partition_key=dynamodb.Attribute(name="room_id", type=dynamodb.AttributeType.STRING)
        )

        staff_table = dynamodb.Table(self, "StaffTable",
            partition_key=dynamodb.Attribute(name="staff_id", type=dynamodb.AttributeType.STRING)
        )

        # IAM Role for Lex Bot
        lex_role = iam.Role(self, "LexRole",
            assumed_by=iam.ServicePrincipal("lex.amazonaws.com"),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AmazonLexFullAccess")]
        )

        # Add specific permissions for Lex role to access DynamoDB
        lex_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:Scan", "dynamodb:PutItem"],
            resources=[
                bookings_table.table_arn,
                rooms_table.table_arn,
                staff_table.table_arn
            ]
        ))


        # Unified Lambda function for all Lex intents
        unified_lambda = _lambda.Function(self, "UnifiedLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="unified_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "BOOKINGS_TABLE": bookings_table.table_name,
                "ROOMS_TABLE": rooms_table.table_name,
                "STAFF_TABLE": staff_table.table_name
            }
        )

        # Grant Lex Role permission to invoke Lambda
        unified_lambda.grant_invoke(lex_role)



        # Grant Lambda function permissions to read/write DynamoDB tables
        bookings_table.grant_read_write_data(unified_lambda)
        rooms_table.grant_read_write_data(unified_lambda)
        staff_table.grant_read_write_data(unified_lambda)





        # Define the Lex Bot with a single Lambda function for all intents
        lex_bot = create_lex_bot(self, lex_role, unified_lambda_arn=unified_lambda.function_arn)


        unified_lambda.add_permission("LexInvokeLambda",
            principal=iam.ServicePrincipal("lexv2.amazonaws.com"),  # Lex V2 service principal
            action="lambda:InvokeFunction",
            #source_arn=lex_bot.attr_arn  # Ensure this is the correct Lex Bot ARN
            source_arn = f"arn:aws:lex:{self.region}:{self.account}:bot-alias/{lex_bot.attr_id}/*"





        )


        # Attach permission to Lex Role for invoking the Lambda function
        lex_role.add_to_policy(iam.PolicyStatement(
            actions=["lambda:InvokeFunction"],
            resources=[unified_lambda.function_arn]
        ))


        # S3 Bucket for frontend
        # 1. Create the S3 bucket
        website_bucket = s3.Bucket(self, "WebsiteBucket",
            website_index_document="index.html",
            website_error_document="error.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS
        )

        # CloudFront Distribution for the frontend
        # 2. Create the CloudFront distribution pointing to the S3 bucket
        cloudfront_dist = cloudfront.Distribution(self, "ChatbotFrontendCDN",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(website_bucket)
            )
        )
        # 3. Deploy the contents of your built React app to the S3 bucket
        s3_deployment.BucketDeployment(self, "DeployFrontend",
            sources=[s3_deployment.Source.asset("frontend/react-app/dist")],
            destination_bucket=website_bucket
        )

        # Lambda function to initialize the database
        init_lambda = _lambda.Function(self, "InitDatabaseLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="init_db.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "BOOKINGS_TABLE": bookings_table.table_name,
                "ROOMS_TABLE": rooms_table.table_name,
                "STAFF_TABLE": staff_table.table_name
            }
        )

        # Grant Lambda function permissions to read/write DynamoDB tables
        bookings_table.grant_read_write_data(init_lambda)
        rooms_table.grant_read_write_data(init_lambda)
        staff_table.grant_read_write_data(init_lambda)

        init_trigger = cr.AwsCustomResource(self, "InitDatabaseTrigger",
            on_create=cr.AwsSdkCall(
                service="Lambda",
                action="invoke",
                parameters={
                    "FunctionName": init_lambda.function_name,
                    "InvocationType": "Event"
                },
                physical_resource_id=cr.PhysicalResourceId.of("InitDatabaseRun")
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["lambda:InvokeFunction"],
                    resources=[init_lambda.function_arn]
                )
            ])
        )

        # API Gateway for meeting bookings
        booking_api = apigateway.LambdaRestApi(self, "BookingAPI",
            handler=unified_lambda,
            proxy=False
        )

        # For adding bookings via chatbot
        booking_resource = booking_api.root.add_resource("book")
        booking_resource.add_method("POST")
        
        # GET list of /bookings in the frontend
        bookings_list = booking_api.root.add_resource("bookings")
        bookings_list.add_method("GET")  # uses unified_lambda by default

        # API Gateway for checking availability
        availability_api = apigateway.LambdaRestApi(self, "AvailabilityAPI",
            handler=unified_lambda,
            proxy=False
        )

        availability_resource = availability_api.root.add_resource("check-availability")
        availability_resource.add_method("GET")

        # Output API Gateway URLs
      #  CfnOutput(self, "BookingAPIGatewayURL", value=booking_api.url)
      #  CfnOutput(self, "AvailabilityAPIGatewayURL", value=availability_api.url)

        # Output Lex Bot ARN
      #  CfnOutput(self, "LexBotARN", value=lex_bot.attr_arn)

        CfnOutput(self, "WebsiteURL", value=f"https://{cloudfront_dist.domain_name}")


        CfnOutput(self, "REACT_APP_BOOKING_API", value=booking_api.url)
        CfnOutput(self, "REACT_APP_AVAILABILITY_API", value=availability_api.url)
        CfnOutput(self, "REACT_APP_LEX_BOT_ARN", value=lex_bot.attr_arn)
 

# Define the app and stack
app = App()
AwsLexChatbotStack(app, "AwsLexChatbotStack", env=Environment(account=os.getenv("AWS_ACCOUNT"), region=os.getenv("AWS_REGION")))
app.synth()
