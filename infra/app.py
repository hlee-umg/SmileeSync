#!/usr/bin/env python3
import aws_cdk as cdk
from smileesync_infra.smileesync_stack import SmileeSyncStack

app = cdk.App()
SmileeSyncStack(app, "SmileeSyncStack",
                env=cdk.Environment(region="us-east-1"))
app.synth()
