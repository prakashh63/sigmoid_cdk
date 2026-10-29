from pathlib import Path

import aws_cdk as cdk

from sigmoid_cdk import ServerlessWebAppStack
from sigmoid_cdk.configs import load_config

app = cdk.App()
config = load_config(Path(__file__).parent / "config.yaml")
ServerlessWebAppStack(app, "PortalSuiteStack", config=config)
app.synth()
