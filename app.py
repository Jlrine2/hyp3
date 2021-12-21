#!/usr/bin/env python3

import aws_cdk as cdk

from apps.hyp3_stack import HyP3Stack, HyP3Config


app = cdk.App()

HyP3Stack(app, "hyp3")
HyP3Stack(app, "hyp3-test")
HyP3Stack(app, "hyp3-edc-uat")
HyP3Stack(app, "hyp3-autorift")
HyP3Stack(app, "hyp3-autorift-eu")
HyP3Stack(app, "hyp3-isce")
HyP3Stack(app, "hyp3-tibet")


app.synth()
