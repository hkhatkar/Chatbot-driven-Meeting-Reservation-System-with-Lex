import aws_cdk as cdk
from aws_cdk import aws_lex as lex
from aws_cdk import aws_iam as iam
from aws_cdk import CfnOutput
from constructs import Construct

def create_lex_bot(scope: Construct, lex_role: iam.Role, unified_lambda_arn: str) -> lex.CfnBot:
    lex_bot = lex.CfnBot(scope, "LexChatBot",
        name="MeetingBookingBot",
        role_arn=lex_role.role_arn,
        data_privacy={"ChildDirected": False},
        idle_session_ttl_in_seconds=300,
        bot_locales=[lex.CfnBot.BotLocaleProperty(
            locale_id="en_US",
            nlu_confidence_threshold=0.4,
            intents=[
                lex.CfnBot.IntentProperty(
                    name="BookMeeting",
                    fulfillment_code_hook=lex.CfnBot.FulfillmentCodeHookSettingProperty(
                        enabled=True
                    ),

                    sample_utterances=[
                        lex.CfnBot.SampleUtteranceProperty(utterance="I want to book a meeting"),
                        lex.CfnBot.SampleUtteranceProperty(utterance="Schedule a meeting for me"),
                        lex.CfnBot.SampleUtteranceProperty(utterance="Book a room for a meeting"),
                    ],
                    slot_priorities=[  # Add slot priorities here
                        lex.CfnBot.SlotPriorityProperty(
                            priority=1,
                            slot_name="MeetingDate"
                        ),
                        lex.CfnBot.SlotPriorityProperty(
                            priority=2,
                            slot_name="MeetingTime"
                        ),
                        lex.CfnBot.SlotPriorityProperty(
                            priority=3,
                            slot_name="Duration"
                        ),
                        lex.CfnBot.SlotPriorityProperty(
                            priority=4,
                            slot_name="Room"
                        ),
                        lex.CfnBot.SlotPriorityProperty(
                            priority=5,
                            slot_name="Attendees"
                        ),
                    ],
                    slots=[
                        lex.CfnBot.SlotProperty(
                            name="MeetingDate",
                            slot_type_name="AMAZON.Date",
                            value_elicitation_setting=lex.CfnBot.SlotValueElicitationSettingProperty(
                                slot_constraint="Required",
                                prompt_specification=lex.CfnBot.PromptSpecificationProperty(
                                    message_groups_list=[
                                        lex.CfnBot.MessageGroupProperty(
                                            message=lex.CfnBot.MessageProperty(
                                                plain_text_message=lex.CfnBot.PlainTextMessageProperty(
                                                    value="What date would you like to book the meeting for?"
                                                )
                                            )
                                        )
                                    ],
                                    max_retries=2
                                )
                            )
                        ),
                        lex.CfnBot.SlotProperty(
                            name="MeetingTime",
                            slot_type_name="AMAZON.Time",
                            value_elicitation_setting=lex.CfnBot.SlotValueElicitationSettingProperty(
                                slot_constraint="Required",
                                prompt_specification=lex.CfnBot.PromptSpecificationProperty(
                                    message_groups_list=[
                                        lex.CfnBot.MessageGroupProperty(
                                            message=lex.CfnBot.MessageProperty(
                                                plain_text_message=lex.CfnBot.PlainTextMessageProperty(
                                                    value="What time should the meeting start?"
                                                )
                                            )
                                        )
                                    ],
                                    max_retries=2
                                )
                            )
                        ),
                        lex.CfnBot.SlotProperty(
                            name="Duration",
                            slot_type_name="AMAZON.Number",
                            value_elicitation_setting=lex.CfnBot.SlotValueElicitationSettingProperty(
                                slot_constraint="Required",
                                prompt_specification=lex.CfnBot.PromptSpecificationProperty(
                                    message_groups_list=[
                                        lex.CfnBot.MessageGroupProperty(
                                            message=lex.CfnBot.MessageProperty(
                                                plain_text_message=lex.CfnBot.PlainTextMessageProperty(
                                                    value="How long will the meeting last (in minutes)?"
                                                )
                                            )
                                        )
                                    ],
                                    max_retries=2
                                )
                            )
                        ),
                        lex.CfnBot.SlotProperty(
                            name="Room",
                            slot_type_name="AMAZON.AlphaNumeric",
                            value_elicitation_setting=lex.CfnBot.SlotValueElicitationSettingProperty(
                                slot_constraint="Required",
                                prompt_specification=lex.CfnBot.PromptSpecificationProperty(
                                    message_groups_list=[
                                        lex.CfnBot.MessageGroupProperty(
                                            message=lex.CfnBot.MessageProperty(
                                                plain_text_message=lex.CfnBot.PlainTextMessageProperty(
                                                    value="Which room should I book for the meeting?"
                                                )
                                            )
                                        )
                                    ],
                                    max_retries=2
                                )
                            )
                        ),
                        lex.CfnBot.SlotProperty(
                            name="Attendees",
                            slot_type_name="AMAZON.FirstName", 
                            value_elicitation_setting=lex.CfnBot.SlotValueElicitationSettingProperty(
                                slot_constraint="Required",
                                prompt_specification=lex.CfnBot.PromptSpecificationProperty(
                                    message_groups_list=[
                                        lex.CfnBot.MessageGroupProperty(
                                            message=lex.CfnBot.MessageProperty(
                                                plain_text_message=lex.CfnBot.PlainTextMessageProperty(
                                                    value="Who will be attending the meeting? You can list multiple names separated by commas."
                                                )
                                            )
                                        )
                                    ],
                                    max_retries=2
                                )
                            )
                        ),
                    ]
                ),
                lex.CfnBot.IntentProperty(
                    name="CheckAvailability",
                    fulfillment_code_hook=lex.CfnBot.FulfillmentCodeHookSettingProperty(
                        enabled=True
                    ),
                    sample_utterances=[
                        lex.CfnBot.SampleUtteranceProperty(utterance="Is the meeting room available?"),
                        lex.CfnBot.SampleUtteranceProperty(utterance="Can I book a meeting at 2 PM?"),
                        lex.CfnBot.SampleUtteranceProperty(utterance="Check availability for a meeting tomorrow"),
                    ],
                    slot_priorities=[  # Add slot priorities here
                        lex.CfnBot.SlotPriorityProperty(priority=1, slot_name="Room"),
                        lex.CfnBot.SlotPriorityProperty(priority=2, slot_name="CheckDate"),
                        lex.CfnBot.SlotPriorityProperty(priority=3, slot_name="CheckTime"),
                    ],
                    slots=[
                        lex.CfnBot.SlotProperty(
                            name="CheckDate",
                            slot_type_name="AMAZON.Date",
                            value_elicitation_setting=lex.CfnBot.SlotValueElicitationSettingProperty(
                                slot_constraint="Required",
                                prompt_specification=lex.CfnBot.PromptSpecificationProperty(
                                    message_groups_list=[
                                        lex.CfnBot.MessageGroupProperty(
                                            message=lex.CfnBot.MessageProperty(
                                                plain_text_message=lex.CfnBot.PlainTextMessageProperty(
                                                    value="Which date do you want to check availability for?"
                                                )
                                            )
                                        )
                                    ],
                                    max_retries=2
                                )
                            )
                        ),
                        lex.CfnBot.SlotProperty(
                            name="CheckTime",
                            slot_type_name="AMAZON.Time",
                            value_elicitation_setting=lex.CfnBot.SlotValueElicitationSettingProperty(
                                slot_constraint="Required",
                                prompt_specification=lex.CfnBot.PromptSpecificationProperty(
                                    message_groups_list=[
                                        lex.CfnBot.MessageGroupProperty(
                                            message=lex.CfnBot.MessageProperty(
                                                plain_text_message=lex.CfnBot.PlainTextMessageProperty(
                                                    value="What time should I check for availability?"
                                                )
                                            )
                                        )
                                    ],
                                    max_retries=2
                                )
                            )
                        ),
                        lex.CfnBot.SlotProperty(
                            name="Room",
                            slot_type_name="AMAZON.AlphaNumeric",
                            value_elicitation_setting=lex.CfnBot.SlotValueElicitationSettingProperty(
                                slot_constraint="Required",
                                prompt_specification=lex.CfnBot.PromptSpecificationProperty(
                                    message_groups_list=[
                                        lex.CfnBot.MessageGroupProperty(
                                            message=lex.CfnBot.MessageProperty(
                                                plain_text_message=lex.CfnBot.PlainTextMessageProperty(
                                                    value="Which room would you like to check?"
                                                )
                                            )
                                        )
                                    ],
                                    max_retries=2
                                )
                            )
                        )
                    ]
                ),
                lex.CfnBot.IntentProperty(
                    name="FallbackIntent",
                    parent_intent_signature="AMAZON.FallbackIntent",
                    fulfillment_code_hook=lex.CfnBot.FulfillmentCodeHookSettingProperty(
                        enabled=True
                    )
                )
            ],
        )],
        test_bot_alias_settings = lex.CfnBot.TestBotAliasSettingsProperty(
            bot_alias_locale_settings=[
                lex.CfnBot.BotAliasLocaleSettingsItemProperty(
                    locale_id="en_US",
                    bot_alias_locale_setting=lex.CfnBot.BotAliasLocaleSettingsProperty(
                        enabled=True,
                        code_hook_specification=lex.CfnBot.CodeHookSpecificationProperty(
                            lambda_code_hook=lex.CfnBot.LambdaCodeHookProperty(
                                code_hook_interface_version="1.0",
                                lambda_arn=unified_lambda_arn
                            )
                        )
                    )
                )
            ]
        )

    )


    bot_version = lex.CfnBotVersion(
        scope,
        "LexChatBotVersion",
        bot_id=lex_bot.ref,
        bot_version_locale_specification=[
            lex.CfnBotVersion.BotVersionLocaleSpecificationProperty(
                locale_id="en_US",
                bot_version_locale_details=lex.CfnBotVersion.BotVersionLocaleDetailsProperty(
                    source_bot_version="DRAFT"  # You clone from DRAFT
                )
            )
        ]
    )

        # Create an explicit alias for Lex V2
    lex_alias = lex.CfnBotAlias(
        scope,
        "LexChatBotAlias",
        bot_alias_name="Prod",            # or a custom alias name
        bot_id=lex_bot.ref,            # reference the bot ID
        bot_version=bot_version.attr_bot_version,                # use draft or a specific version
        bot_alias_locale_settings=[
            lex.CfnBotAlias.BotAliasLocaleSettingsItemProperty(
                locale_id="en_US",
                bot_alias_locale_setting=lex.CfnBotAlias.BotAliasLocaleSettingsProperty(
                    enabled=True,
                    code_hook_specification=lex.CfnBotAlias.CodeHookSpecificationProperty(
                        lambda_code_hook=lex.CfnBotAlias.LambdaCodeHookProperty(
                            code_hook_interface_version="1.0",
                            lambda_arn=unified_lambda_arn
                        )
                    )
                )
            )
        ]
    )
        # Export outputs for frontend configuration
    CfnOutput(scope, "REACT_APP_LEX_BOT_ID",       value=lex_bot.ref)
    CfnOutput(scope, "REACT_APP_LEX_BOT_ALIAS_ID", value=lex_alias.ref)
    return lex_bot
