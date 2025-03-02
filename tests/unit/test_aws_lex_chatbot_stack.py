import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_lex_chatbot.aws_lex_chatbot_stack import AwsLexChatbotStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws_lex_chatbot/aws_lex_chatbot_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsLexChatbotStack(app, "aws-lex-chatbot")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
