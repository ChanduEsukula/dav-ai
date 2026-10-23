"""Policy assertions supplement (not replace) Terraform provider validation/tests."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_templates_have_no_enable_path_for_data_or_public_invokers():
    config = json.loads((ROOT / "deployment/gcp/main.tf.json").read_text())
    assert config["variable"]["foundation_enabled"]["default"] is False
    resources = config["resource"]
    assert set(resources) == {"google_cloud_run_v2_service", "google_service_account", "google_artifact_registry_repository"}
    for group in resources.values():
        for resource in group.values():
            assert resource["count"] == "${var.foundation_enabled ? 1 : 0}"
    service = resources["google_cloud_run_v2_service"]["foundation"]
    assert service["ingress"] == "INGRESS_TRAFFIC_INTERNAL_ONLY"
    assert service["invoker_iam_disabled"] is False
    assert service["deletion_protection"] is True
    template = service["template"]
    assert template["scaling"] == {"min_instance_count": 0, "max_instance_count": 1}
    assert template["max_instance_request_concurrency"] == 4 and template["timeout"] == "10s"
    container = template["containers"][0]
    assert container["env"] == [{"name": "DAVAI_ENV", "value": "staging"}, {"name": "DAVAI_FOUNDATION_MODE", "value": "deny"}]
    assert not any(k in template for k in ("volumes", "vpc_access"))
    assert set(container["resources"]["limits"]) == {"cpu", "memory"}
    assert "sha256:" in config["variable"]["foundation_image"]["validation"]["condition"]
    assert "allUsers" not in json.dumps(config) and "allAuthenticatedUsers" not in json.dumps(config)


def test_deny_image_context_cannot_copy_application_data_or_models():
    dockerfile = (ROOT / "deployment/foundation/Dockerfile").read_text()
    assert "USER 65532:65532" in dockerfile and "--require-hashes" in dockerfile
    assert "app.main" not in dockerfile and "COPY backend/app" not in dockerfile
    assert "COPY deployment/foundation/app.py /foundation/app.py" in dockerfile
    lines = (ROOT / "deployment/foundation/Dockerfile.dockerignore").read_text().splitlines()
    allowed = {line[1:] for line in lines if line.startswith("!")}
    assert allowed == {"deployment/", "deployment/foundation/", "deployment/foundation/requirements.lock",
                       "deployment/foundation/app.py", "deployment/foundation/Dockerfile", "deployment/foundation/Dockerfile.dockerignore"}
    tree = ast.parse((ROOT / "deployment/foundation/app.py").read_text())
    modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not any(module and module.startswith("app.") for module in modules)


def test_frontend_image_is_artifact_only_and_pins_dependencies():
    dockerfile = (ROOT / "deployment/frontend/Dockerfile").read_text()
    assert "node:24-bookworm-slim@sha256:" in dockerfile
    assert "npm ci" in dockerfile and "npm run build" in dockerfile
    final = dockerfile.split("FROM scratch AS artifact")[1]
    assert "COPY --from=build /ui/dist /dist" in final
    assert all(command not in final for command in ("CMD", "ENTRYPOINT", "EXPOSE"))
    ignore = (ROOT / "deployment/frontend/Dockerfile.dockerignore").read_text()
    assert "**/.env*" in ignore and "data/" not in ignore


def test_foundation_ci_is_credential_free_and_never_deploys():
    # actionlint separately validates YAML and Actions semantics; policy checks
    # here use stdlib only, so the locked test environment needs no YAML package.
    import re
    workflow = (ROOT / ".github/workflows/gcp-foundation.yml").read_text()
    assert re.search(r"(?m)^permissions:\n  contents: read\n", workflow)
    assert workflow.count("permissions:") == 1
    assert "id-token:" not in workflow and "secrets." not in workflow and "environment:" not in workflow
    for reference in re.findall(r"uses: ([^ \n]+)", workflow):
        assert re.fullmatch(r"[A-Za-z0-9_./-]+@[a-f0-9]{40}", reference)
    assert not any(command in workflow for command in ("terraform apply", "gcloud ", "docker push", "firebase deploy"))


def test_foundation_lock_only_reuses_server_pins_and_hashes():
    import re
    existing = (ROOT / "backend/requirements-runtime.lock").read_text()
    minimal = (ROOT / "deployment/foundation/requirements.lock").read_text()
    assert set(re.findall(r"(?m)^([a-z0-9_-]+)==", minimal)) == {"click", "h11", "uvicorn"}
    for name in ("click", "h11", "uvicorn"):
        block = re.search(r"(?m)^" + name + r"==[^\n]+(?:\n[ \t]+--hash=[^\n]+)*", minimal).group()
        assert block in existing
