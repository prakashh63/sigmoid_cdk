# Naming conventions

| Thing | Rule | Example |
|---|---|---|
| Config names (function, queue, rule, API, layer) | kebab-case, 3-40 chars | `orders-api` |
| AWS resource name | `<app>-<stage>-<name>` | `orders-app-dev-orders-api` |
| Stack name | `<org>-<app>-<stage>` | `sigmoid-orders-app-dev` |
| Construct id | PascalCase of the name + type | `OrdersApiFunction` |
| Environment variable | UPPER_SNAKE | `QUEUE_URL_ORDER_EVENTS` |
| Python files | snake_case, never `utils`/`misc`/`common` | `secure_bucket.py` |
| Construct folders | `constructs/aws_<service>/` | `aws_s3/` |

`tools/check_conventions.py` enforces the file rules in CI.
