"""Aspect that puts the standard company tags on every taggable resource."""

from collections.abc import Mapping

import aws_cdk as cdk
import jsii
from constructs import IConstruct


@jsii.implements(cdk.IAspect)
class TaggingAspect:
    def __init__(self, tags: Mapping[str, str]) -> None:
        self._tags = dict(tags)

    def visit(self, node: IConstruct) -> None:
        if cdk.TagManager.is_taggable(node):
            for key, value in self._tags.items():
                node.tags.set_tag(key, value)  # type: ignore[attr-defined]
