"""Picks the layers a Lambda function asked for, by name."""

from collections.abc import Mapping, Sequence

from aws_cdk import aws_lambda as lambda_


def select_layers(
    layers_by_name: Mapping[str, lambda_.ILayerVersion], wanted_names: Sequence[str]
) -> list[lambda_.ILayerVersion]:
    missing = [name for name in wanted_names if name not in layers_by_name]
    if missing:
        raise KeyError(
            f"unknown layer(s) {missing}; defined layers: {sorted(layers_by_name)}"
        )
    return [layers_by_name[name] for name in wanted_names]
