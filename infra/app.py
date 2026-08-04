#!/usr/bin/env python3
import os
import aws_cdk as cdk
from smileesync_infra.smileesync_stack import SmileeSyncStack

app = cdk.App()
SmileeSyncStack(
    app, "SmileeSyncStack",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
    ),
)
app.synth()
