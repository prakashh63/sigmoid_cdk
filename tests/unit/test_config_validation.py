from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from sigmoid_cdk.configs import (
    ApiGatewayConfig,
    EventRuleTriggerConfig,
    LambdaConfig,
    S3Config,
    ScheduleTriggerConfig,
    WebAppConfig,
    load_config,
)

ROOT = Path(__file__).parents[2]


def fn(name: str = "fn", **extra: Any) -> dict[str, Any]:
    return {"function_name": name, "entry_point_dir": "src", **extra}


def valid_data() -> dict[str, Any]:
    return {
        "app_name": "demo",
        "environment": "dev",
        "owner_team": "team-a",
        "buckets": {"web": {"bucket_name": "demo-assets-bucket", "cdn_default": True}},
        "lambdas": {"backend": fn()},
    }


def two_lambdas() -> dict[str, Any]:
    data = valid_data()
    data["lambdas"] = {"users": fn("users-fn"), "reports": fn("reports-fn")}
    return data


def write_yaml(folder: Path, body: str) -> Path:
    (folder / "code").mkdir(exist_ok=True)
    path = folder / "config.yaml"
    path.write_text(body)
    return path


# ---------- defaults and shapes ----------


def test_valid_config_loads_with_defaults() -> None:
    config = WebAppConfig.model_validate(valid_data())
    function = config.lambdas["backend"]
    assert function.memory_mb == 512
    assert function.runtime == "PYTHON_3_14"
    assert function.timeout_seconds == 30
    assert function.bucket_access == {}
    assert function.triggers.schedule is None
    assert config.api_gateway.enable_proxy is True
    assert config.api_gateway.stage_name == "prod"
    assert config.encrypt_logs is True


def test_worker_config_without_buckets_is_valid() -> None:
    data = valid_data()
    data["buckets"] = {}
    data["api_gateway"] = {"enable_proxy": False}
    config = WebAppConfig.model_validate(data)
    assert config.buckets == {}
    assert config.effective_routes() == []


def test_single_lambda_without_routes_gets_root_route() -> None:
    config = WebAppConfig.model_validate(valid_data())
    routes = config.effective_routes()
    assert [(r.path, r.function) for r in routes] == [("/", "backend")]


def test_multi_resource_config_is_valid() -> None:
    data = two_lambdas()
    data["buckets"]["uploads"] = {"bucket_name": "demo-uploads-bucket"}
    data["topics"] = {"orders": {"topic_name": "orders-topic"}}
    data["lambdas"]["users"]["bucket_access"] = {"uploads": "read_write"}
    data["lambdas"]["reports"]["triggers"] = {"sns": ["orders"]}
    data["api_gateway"] = {
        "routes": [
            {"path": "/api/users", "function": "users"},
            {"path": "/api/reports", "function": "reports"},
        ]
    }
    config = WebAppConfig.model_validate(data)
    assert len(config.effective_routes()) == 2


# ---------- legacy single-resource keys ----------


def test_legacy_keys_are_upgraded() -> None:
    config = WebAppConfig.model_validate(
        {
            "app_name": "demo",
            "environment": "dev",
            "owner_team": "team-a",
            "s3": {"bucket_name": "demo-assets-bucket"},
            "lambda_backend": fn(),
            "triggers": {
                "sns": {"topic_name": "old-topic"},
                "schedule": {"expression": "rate(1 hour)"},
            },
        }
    )
    assert list(config.lambdas) == ["backend"]
    assert config.buckets["web"].cdn_default is True
    assert config.topics["default"].topic_name == "old-topic"
    assert config.lambdas["backend"].triggers.sns == ["default"]
    assert config.lambdas["backend"].triggers.schedule is not None


def test_legacy_python_objects_are_upgraded() -> None:
    config = WebAppConfig.model_validate(
        {
            "app_name": "demo",
            "environment": "prod",
            "owner_team": "team-a",
            "s3": S3Config(bucket_name="demo-assets-bucket"),
            "lambda_backend": LambdaConfig(function_name="fn", entry_point_dir="src"),
            "api_gateway": ApiGatewayConfig(stage_name="v1"),
        }
    )
    assert config.buckets["web"].cdn_default is True
    assert config.lambdas["backend"].function_name == "fn"
    assert config.api_gateway.stage_name == "v1"


def test_mixing_old_and_new_keys_rejected() -> None:
    data = valid_data()
    data["s3"] = {"bucket_name": "other-bucket"}
    with pytest.raises(ValidationError, match="Do not mix"):
        WebAppConfig.model_validate(data)


# ---------- field validation ----------


def test_memory_below_minimum_rejected() -> None:
    with pytest.raises(ValidationError):
        LambdaConfig(function_name="fn", entry_point_dir="src", memory_mb=50)


def test_memory_above_maximum_rejected() -> None:
    with pytest.raises(ValidationError):
        LambdaConfig(function_name="fn", entry_point_dir="src", memory_mb=4000)


def test_unknown_environment_rejected() -> None:
    data = valid_data()
    data["environment"] = "qa"
    with pytest.raises(ValidationError):
        WebAppConfig.model_validate(data)


def test_unknown_runtime_rejected() -> None:
    with pytest.raises(ValidationError):
        LambdaConfig(function_name="fn", entry_point_dir="src", runtime="PYTHON_9_99")


def test_unknown_field_rejected() -> None:
    data = valid_data()
    data["memory_mbb"] = 1
    with pytest.raises(ValidationError):
        WebAppConfig.model_validate(data)


def test_bad_bucket_name_rejected() -> None:
    with pytest.raises(ValidationError):
        S3Config(bucket_name="Bad_Name")


def test_bad_cdn_path_rejected() -> None:
    with pytest.raises(ValidationError):
        S3Config(bucket_name="good-name", cdn_path="assets")


def test_bad_stage_name_rejected() -> None:
    with pytest.raises(ValidationError):
        ApiGatewayConfig(stage_name="bad stage!")


def test_bad_schedule_expression_rejected() -> None:
    with pytest.raises(ValidationError):
        ScheduleTriggerConfig(expression="every day")


def test_event_rule_requires_a_source() -> None:
    with pytest.raises(ValidationError):
        EventRuleTriggerConfig(source=[])


def test_bad_resource_key_rejected() -> None:
    data = valid_data()
    data["lambdas"] = {"Bad_Key": fn()}
    with pytest.raises(ValidationError):
        WebAppConfig.model_validate(data)


def test_at_least_one_lambda_required() -> None:
    data = valid_data()
    data["lambdas"] = {}
    with pytest.raises(ValidationError):
        WebAppConfig.model_validate(data)


# ---------- cross-checks ----------


def test_route_to_unknown_lambda_rejected() -> None:
    data = valid_data()
    data["api_gateway"] = {"routes": [{"path": "/api/x", "function": "ghost"}]}
    with pytest.raises(ValidationError, match="unknown Lambda 'ghost'"):
        WebAppConfig.model_validate(data)


def test_unknown_bucket_access_rejected() -> None:
    data = valid_data()
    data["lambdas"]["backend"]["bucket_access"] = {"ghost": "read"}
    with pytest.raises(ValidationError, match="unknown bucket 'ghost'"):
        WebAppConfig.model_validate(data)


def test_bad_access_level_rejected() -> None:
    data = valid_data()
    data["lambdas"]["backend"]["bucket_access"] = {"web": "admin"}
    with pytest.raises(ValidationError):
        WebAppConfig.model_validate(data)


def test_unknown_topic_rejected() -> None:
    data = valid_data()
    data["lambdas"]["backend"]["triggers"] = {"sns": ["ghost"]}
    with pytest.raises(ValidationError, match="unknown topic 'ghost'"):
        WebAppConfig.model_validate(data)


def test_duplicate_function_name_rejected() -> None:
    data = two_lambdas()
    data["lambdas"]["reports"]["function_name"] = "users-fn"
    data["api_gateway"] = {"enable_proxy": False}
    with pytest.raises(ValidationError, match="duplicate function_name"):
        WebAppConfig.model_validate(data)


def test_duplicate_bucket_name_rejected() -> None:
    data = valid_data()
    data["buckets"]["other"] = {"bucket_name": "demo-assets-bucket"}
    with pytest.raises(ValidationError, match="duplicate bucket_name"):
        WebAppConfig.model_validate(data)


def test_duplicate_topic_name_rejected() -> None:
    data = valid_data()
    data["topics"] = {"a": {"topic_name": "same"}, "b": {"topic_name": "same"}}
    with pytest.raises(ValidationError, match="duplicate topic_name"):
        WebAppConfig.model_validate(data)


def test_two_cdn_default_buckets_rejected() -> None:
    data = valid_data()
    data["buckets"]["second"] = {"bucket_name": "second-bucket", "cdn_default": True}
    with pytest.raises(ValidationError, match="only one bucket can have cdn_default"):
        WebAppConfig.model_validate(data)


def test_cdn_path_without_default_bucket_rejected() -> None:
    data = valid_data()
    data["buckets"] = {"assets": {"bucket_name": "assets-bucket", "cdn_path": "/assets/*"}}
    with pytest.raises(ValidationError, match="needs one bucket with cdn_default"):
        WebAppConfig.model_validate(data)


def test_cdn_default_and_path_together_rejected() -> None:
    data = valid_data()
    data["buckets"]["web"]["cdn_path"] = "/assets/*"
    with pytest.raises(ValidationError, match="cannot be combined"):
        WebAppConfig.model_validate(data)


def test_cdn_path_api_is_reserved() -> None:
    data = valid_data()
    data["buckets"]["x"] = {"bucket_name": "x-bucket", "cdn_path": "/api/*"}
    with pytest.raises(ValidationError, match="reserved"):
        WebAppConfig.model_validate(data)


def test_several_lambdas_need_routes() -> None:
    with pytest.raises(ValidationError, match="routes is required"):
        WebAppConfig.model_validate(two_lambdas())


def test_routes_need_proxy_enabled() -> None:
    data = valid_data()
    data["api_gateway"] = {
        "enable_proxy": False,
        "routes": [{"path": "/api/x", "function": "backend"}],
    }
    with pytest.raises(ValidationError, match="enable_proxy is false"):
        WebAppConfig.model_validate(data)


def test_duplicate_route_path_rejected() -> None:
    data = two_lambdas()
    data["api_gateway"] = {
        "routes": [
            {"path": "/api/x", "function": "users"},
            {"path": "/api/x", "function": "reports"},
        ]
    }
    with pytest.raises(ValidationError, match="duplicate route path"):
        WebAppConfig.model_validate(data)


def test_route_outside_api_prefix_rejected_with_cdn() -> None:
    data = valid_data()
    data["api_gateway"] = {"routes": [{"path": "/users", "function": "backend"}]}
    with pytest.raises(ValidationError, match="must start with /api/"):
        WebAppConfig.model_validate(data)


def test_route_outside_api_prefix_allowed_without_cdn() -> None:
    data = valid_data()
    data["buckets"] = {}
    data["api_gateway"] = {"routes": [{"path": "/users", "function": "backend"}]}
    WebAppConfig.model_validate(data)


# ---------- loader ----------


def test_load_example_configs() -> None:
    web = load_config(ROOT / "examples" / "config.yaml")
    assert web.app_name == "customer-portal"
    assert Path(web.lambdas["backend"].entry_point_dir).is_absolute()

    worker = load_config(ROOT / "examples" / "worker" / "config.yaml")
    assert worker.buckets == {}
    assert worker.api_gateway.enable_proxy is False
    triggers = worker.lambdas["worker"].triggers
    assert triggers.sns == ["orders"]
    assert triggers.schedule is not None
    assert triggers.event_rule is not None

    multi = load_config(ROOT / "examples" / "multi" / "config.yaml")
    assert set(multi.lambdas) == {"users", "reports", "order-worker"}
    assert set(multi.buckets) == {"website", "assets", "uploads"}
    for function in multi.lambdas.values():
        assert Path(function.entry_point_dir).is_absolute()


def test_entry_point_resolved_relative_to_config(tmp_path: Path) -> None:
    path = write_yaml(
        tmp_path,
        "app_name: x\nenvironment: dev\nowner_team: t\n"
        "lambdas:\n  main:\n    function_name: f\n    entry_point_dir: code\n",
    )
    config = load_config(path)
    assert config.lambdas["main"].entry_point_dir == str((tmp_path / "code").resolve())


def test_legacy_yaml_still_loads(tmp_path: Path) -> None:
    path = write_yaml(
        tmp_path,
        "app_name: x\nenvironment: dev\nowner_team: t\n"
        "lambda_backend:\n  function_name: f\n  entry_point_dir: code\n",
    )
    assert list(load_config(path).lambdas) == ["backend"]


def test_load_invalid_yaml_rejected(tmp_path: Path) -> None:
    path = write_yaml(
        tmp_path,
        "app_name: x\nenvironment: dev\nowner_team: t\n"
        "lambdas:\n  main:\n    function_name: f\n    entry_point_dir: code\n    memory_mb: 50\n",
    )
    with pytest.raises(ValidationError):
        load_config(path)


def test_empty_yaml_gives_clear_error(tmp_path: Path) -> None:
    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    with pytest.raises(ValueError, match="empty or is not a YAML mapping"):
        load_config(empty)


def test_missing_file_gives_clear_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config(tmp_path / "nope.yaml")


def test_missing_code_folder_names_the_lambda(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        "app_name: x\nenvironment: dev\nowner_team: t\n"
        "lambdas:\n  main:\n    function_name: f\n    entry_point_dir: missing_folder\n"
    )
    with pytest.raises(FileNotFoundError, match="Lambda code folder not found for 'main'"):
        load_config(path)


def test_aws_block_is_optional_and_validated() -> None:
    data = valid_data()
    assert WebAppConfig.model_validate(data).aws is None
    data["aws"] = {"account": "123456789012", "region": "ap-south-1"}
    config = WebAppConfig.model_validate(data)
    assert config.aws is not None
    assert config.aws.region == "ap-south-1"


@pytest.mark.parametrize(
    "aws",
    [
        {"account": "1234"},
        {"account": 123456789012},  # unquoted YAML number
        {"region": "Mumbai"},
        {"region": "ap-south"},
        {"profile": "dev"},  # unknown field
    ],
)
def test_bad_aws_block_rejected(aws: dict[str, object]) -> None:
    data = valid_data()
    data["aws"] = aws
    with pytest.raises(ValidationError):
        WebAppConfig.model_validate(data)
