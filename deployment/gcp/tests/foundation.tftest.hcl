# Offline provider mocks; these tests do NOT authenticate, plan against GCP or apply.
mock_provider "google" {}

run "disabled_by_default" {
  command = plan
  assert {
    condition     = length(google_cloud_run_v2_service.foundation) == 0 && length(google_artifact_registry_repository.foundation) == 0 && length(google_service_account.foundation) == 0
    error_message = "Default configuration must create no cloud resources."
  }
}

run "private_deny_only" {
  command = plan
  variables {
    foundation_enabled = true
    project_id         = "davai-test-only"
    foundation_image   = "us-central1-docker.pkg.dev/davai-test-only/davai-foundation/deny-api@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  }
  assert {
    condition     = google_cloud_run_v2_service.foundation[0].ingress == "INGRESS_TRAFFIC_INTERNAL_ONLY" && !google_cloud_run_v2_service.foundation[0].invoker_iam_disabled
    error_message = "Network ingress and IAM invoker authentication must stay private."
  }
  assert {
    condition     = google_cloud_run_v2_service.foundation[0].template[0].scaling[0].max_instance_count == 1 && google_cloud_run_v2_service.foundation[0].template[0].max_instance_request_concurrency == 4
    error_message = "Foundation cost and concurrency defaults changed."
  }
}

run "reject_mutable_or_foreign_image" {
  command = plan
  variables {
    foundation_enabled = true
    foundation_image   = "example.com/pharmaceutical-api:latest"
  }
  expect_failures = [var.foundation_image]
}
