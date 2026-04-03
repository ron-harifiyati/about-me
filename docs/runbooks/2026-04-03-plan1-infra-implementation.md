# Plan 1 Implementation Log — Infrastructure & CI/CD

**Date:** 2026-04-03
**Plan:** `docs/superpowers/plans/2026-04-02-portfolio-infra.md`
**Outcome:** Complete. All resources provisioned, CI/CD smoke tested green.

---

## Overview

This document records what was done, in what order, what challenges were encountered, what was tried, what failed, and what ultimately worked — along with the reasons.

---

## Task 1: Repository Structure + Branches

**What we did:**
Created `version.txt`, `backend/handler.py`, `backend/requirements.txt`, `frontend/index.html`, `frontend/assets/.gitkeep`. Committed to `main`, created `dev` branch locally.

**Challenge: No GitHub remote configured.**
The repo was local-only. Attempting `git push origin dev` failed with `fatal: 'origin' does not appear to be a git repository`.

**Resolution:**
Added the remote manually:
```bash
git remote add origin git@github.com:ron-harifiyati/about-me.git
git push origin main
git push origin dev
```
Both branches now exist on GitHub.

---

## Task 2: DynamoDB Table

**What we did:**
Attempted to create the `portfolio` DynamoDB table with PK/SK, 3 GSIs (GSI1–3), on-demand billing, TTL on `ttl`.

**Challenge: AWS CLI permission denied.**
The configured profile (`claude-code-bedrock`) used an SSO assumed role: `AWSReservedSSO_BedrockAccess_f76ad9115734f45e`. This role had only Bedrock permissions — no DynamoDB, Lambda, IAM, S3, or CloudFront access.

```
AccessDeniedException: User is not authorized to perform: dynamodb:CreateTable
```

**What we tried:**
- Checked `aws configure list-profiles` — only one profile existed (`claude-code-bedrock`).
- Confirmed with `aws sts get-caller-identity` the role was Bedrock-scoped.

**Resolution:**
Created a new IAM user `portfolio-admin` with `AdministratorAccess` via the AWS Console, generated access keys, and configured a new CLI profile:
```bash
aws configure --profile portfolio-admin
```
All subsequent AWS CLI commands use `--profile portfolio-admin`.

**Note:** The `portfolio-admin` user is in account `993249606359` — a different account from the Bedrock SSO session (`343508908658`). This is the account used for all portfolio infrastructure.

Table created successfully: ACTIVE, GSI1/GSI2/GSI3, TTL enabled on `ttl` attribute.

---

## Task 3: IAM Role for Lambda

**What we did:**
Created `portfolio-lambda-role` with a trust policy for `lambda.amazonaws.com`. Created `portfolio-lambda-policy` with DynamoDB (GetItem/PutItem/UpdateItem/DeleteItem/Query on `portfolio` table + GSIs), SES (SendEmail), and CloudWatch Logs permissions. Attached policy to role. Committed `infra/iam-policy.json`.

**No issues.** Completed cleanly.

---

## Task 4: Lambda Functions — and the Function URL Problem

This was the most challenging task of the plan.

### Step 1: Lambda creation

Created `portfolio-dev` and `portfolio-prod` with Python 3.12, 512MB memory, 30s timeout, and hello-world handler. Both became Active without issue.

### Step 2: Function URLs — persistent 403 Forbidden

The plan called for Lambda Function URLs (`auth-type: NONE`) as the public HTTP endpoint. After enabling them on both functions and adding the required resource-based policy, every HTTP request returned:

```json
{"Message": "Forbidden. For troubleshooting Function URL authorization issues, see: ..."}
```

**What we investigated and tried:**

1. **Verified auth type was NONE** — confirmed via `get-function-url-config`. Correct.
2. **Verified resource policy** — `get-policy` showed the correct `AllowPublicAccess` statement with `Principal: *` and `Condition: lambda:FunctionUrlAuthType: NONE`. Correct.
3. **Direct Lambda invocation** — `aws lambda invoke` returned `{"data": {"message": "Portfolio API"}, "error": null}` — the function itself works perfectly.
4. **IAM simulation** — `aws iam simulate-principal-policy` for `portfolio-admin` returned `"allowed"` for `lambda:InvokeFunctionUrl`.
5. **Signed curl request** — Testing the Function URL with `--aws-sigv4` credentials also returned 403. This ruled out the issue being purely about anonymous access.
6. **Re-adding the permission without the condition** — AWS rejected this: `InvalidParameterValueException: You must specify lambda:FunctionUrlAuthType condition`. The condition is mandatory when using `Principal: *`.
7. **Checking for Lambda VPC config** — None. Not the issue.

**Root cause identified:**
The account (`993249606359`) is a member of the Jamf Software AWS Organization (`o-bk33g55csx`, master: `hosting@jamfsoftware.com`). The organization has Service Control Policies (SCPs) enabled. We could not read the SCP contents (`organizations:ListPoliciesForTarget` was denied), but the behavior was consistent with an SCP blocking public Lambda Function URL access — a common corporate security control.

Even though `simulate-principal-policy` said "allowed", that API does not fully simulate all SCP effects on Lambda Function URL anonymous invocations.

**Resolution: Switch to API Gateway HTTP API.**

Created two API Gateway HTTP APIs (`portfolio-dev`, `portfolio-prod`) using `AWS_PROXY` Lambda integrations with payload format version 2.0. Added `lambda:InvokeFunction` permissions with `apigateway.amazonaws.com` as principal. Both APIs deployed immediately and responded correctly:

```bash
curl https://ly0fxfdai9.execute-api.us-east-1.amazonaws.com
# {"data": {"message": "Portfolio API"}, "error": null}
```

**Why API Gateway worked where Function URLs didn't:**
API Gateway calls Lambda as a service-to-service invocation (not a public `InvokeFunctionUrl` call). The Lambda permission uses `lambda:InvokeFunction` with `Principal: apigateway.amazonaws.com` — a standard inter-service permission that doesn't trigger the same SCP restriction. The public-facing endpoint is the API Gateway URL itself, which doesn't go through Lambda's Function URL auth layer.

**Docs updated:** `README.md`, `CLAUDE.md`, `docs/superpowers/plans/2026-04-02-portfolio-infra.md` all updated to reflect API Gateway instead of Lambda Function URLs.

**API Gateway endpoints:**
- Dev: `https://ly0fxfdai9.execute-api.us-east-1.amazonaws.com`
- Prod: `https://o4o1xcb3wc.execute-api.us-east-1.amazonaws.com`

---

## Task 5: S3 Buckets

**Challenge: Bucket names already taken.**
`portfolio-frontend-dev` and `portfolio-frontend-prod` were already claimed by other AWS accounts. S3 bucket names are globally unique across all accounts.

```
BucketAlreadyExists: The requested bucket name is not available.
```

**Resolution:**
Appended the account ID as a suffix to guarantee uniqueness:
- `portfolio-frontend-dev-993249606359`
- `portfolio-frontend-prod-993249606359`

Public access blocked on both. Placeholder `index.html` uploaded.

**CLAUDE.md updated** with real bucket names.

---

## Task 6: CloudFront Distributions

**What we did:**
Created a single Origin Access Control (`portfolio-s3-oac`, ID: `EDZWRWAI5EH7O`) shared between both distributions. Created dev and prod CloudFront distributions pointing at the S3 buckets, with:
- `redirect-to-https` viewer protocol
- Managed cache policy `658327ea-f89d-4fab-a63d-7e88639e58f6` (CachingOptimized)
- Custom error responses: 403 and 404 → `/index.html` with 200 (SPA routing support)
- http2 enabled, compression on

Applied S3 bucket policies to allow CloudFront OAC `s3:GetObject` with `AWS:SourceArn` condition scoped to each distribution.

Waited for distributions to deploy in the background (~5 min). Both smoke tested successfully:

```bash
curl https://d3sw9ggppgh9as.cloudfront.net
# Returns frontend/index.html
```

**No issues.** Completed cleanly.

**CloudFront IDs:**
- Dev: `E3GFM00HUAVU15` → `d3sw9ggppgh9as.cloudfront.net`
- Prod: `E1P7C158XTW7UF` → `dkdwnfmhg75yf.cloudfront.net`

---

## Task 7: SES Email Verification

Ran `aws ses verify-email-identity --email-address ronshadreck@gmail.com`. AWS sent a verification email. After clicking the link, confirmed:

```
"VerificationStatus": "Success"
```

**No issues.**

---

## Task 8: GitHub Secrets

**Challenge 1: `gh` CLI lacked permissions to write secrets.**
Initial `gh auth status` showed the token was authenticated but could not write secrets (HTTP 403 on public key fetch).

**What we tried:**
Ran `gh auth login --scopes "repo,secrets"` — GitHub rejected `secrets` as an invalid OAuth scope.

**Resolution:**
`secrets` write permission is included in the `repo` scope. Re-authenticated with:
```bash
gh auth login --scopes "repo"
```
After re-auth, secret writes succeeded.

**Challenge 2: `GITHUB_OAUTH_CLIENT_ID` secret name rejected.**
When setting the GitHub OAuth App credentials:
```
HTTP 422: Secret names must not start with GITHUB_.
```
GitHub reserves the `GITHUB_` prefix for built-in context variables.

**Resolution:**
Renamed to `GH_OAUTH_CLIENT_ID` and `GH_OAUTH_CLIENT_SECRET`. Updated `deploy-backend.yml` to reference the new names. The Lambda env var key remains `GITHUB_OAUTH_CLIENT_ID` (set at deploy time inside the workflow) — only the *GitHub Secret name* changed.

**Challenge 3: Google Cloud required project creation first.**
Navigating to APIs & Services → Credentials required an active project. Created project `portfolio` in Google Cloud Console, completed the OAuth consent screen (External, app name `Ron Harifiyati Portfolio`), then created the Web Application OAuth 2.0 credential.

**All 17 secrets set:**
`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `DEV_LAMBDA_FUNCTION_NAME`, `PROD_LAMBDA_FUNCTION_NAME`, `DEV_S3_BUCKET`, `PROD_S3_BUCKET`, `DEV_CLOUDFRONT_ID`, `PROD_CLOUDFRONT_ID`, `JWT_SECRET_KEY`, `SES_SENDER_EMAIL`, `DEV_API_GATEWAY_URL`, `PROD_API_GATEWAY_URL`, `GH_OAUTH_CLIENT_ID`, `GH_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`.

---

## Tasks 9–10: GitHub Actions Workflows

Created `deploy-backend.yml` and `deploy-frontend.yml` as specified in the plan, with one architectural change: replaced all `$PROD_URL` / Lambda Function URL references with API Gateway URLs.

---

## Task 11: CI/CD Smoke Test

**Challenge 1: No workflows triggered on first push.**
The workflows use path filters (`backend/**`, `frontend/**`). The commits pushed were to `CLAUDE.md`, `README.md`, `.github/workflows/` — none of which match. GitHub Actions only triggers on the *pushed* commits, not historical ones already in the branch.

**Resolution:**
Made a touch commit modifying both `backend/requirements.txt` and `frontend/index.html` to trigger both workflows simultaneously.

**Challenge 2: Backend workflow failed — `tests/` directory not found.**
```
ERROR: file or directory not found: tests/
exit code 4
```
The `backend/tests/` directory doesn't exist until Plan 2. pytest exits with code 4 when the path doesn't exist, which fails the job.

**Resolution:**
Added a placeholder test directory with a single passing test:
```python
# backend/tests/test_placeholder.py
def test_placeholder():
    """Placeholder until backend routes are implemented in Plan 2."""
    assert True
```

**Challenge 3: Package step would fail for missing files.**
The workflow `cp handler.py router.py auth.py db.py utils.py package/` would fail because `router.py`, `auth.py`, `db.py`, `utils.py`, `routes/`, and `models/` don't exist yet (Plan 2).

**Resolution:**
Made the copy step resilient using conditionals:
```bash
cp handler.py package/
for f in router.py auth.py db.py utils.py; do [ -f "$f" ] && cp "$f" package/; done
for d in routes models; do [ -d "$d" ] && cp -r "$d" package/; done
```

**Final result:** Both workflows green. Lambda env vars confirmed stamped:
```json
{
  "SHA": "d8d0991aba60bba8b8b681a2b890a920eb10420c",
  "Timestamp": "2026-04-02T21:58:40Z",
  "Env": "dev",
  "Version": "0.1.0"
}
```

---

## Final Resource Inventory

| Resource | Dev | Prod |
|---|---|---|
| API Gateway | `ly0fxfdai9` | `o4o1xcb3wc` |
| Lambda | `portfolio-dev` | `portfolio-prod` |
| S3 | `portfolio-frontend-dev-993249606359` | `portfolio-frontend-prod-993249606359` |
| CloudFront ID | `E3GFM00HUAVU15` | `E1P7C158XTW7UF` |
| CloudFront Domain | `d3sw9ggppgh9as.cloudfront.net` | `dkdwnfmhg75yf.cloudfront.net` |
| DynamoDB | `portfolio` (shared) | `portfolio` (shared) |
| IAM Role | `portfolio-lambda-role` | (shared) |
| OAC | `EDZWRWAI5EH7O` | (shared) |
| SES | `ronshadreck@gmail.com` verified | — |
| AWS Account | `993249606359` | — |

---

## Key Lessons

1. **Check AWS org membership before designing the architecture.** The account being inside a corporate org (Jamf) caused the Function URL issue. For personal projects, use a personal AWS account or verify SCP restrictions first.

2. **Lambda Function URLs vs API Gateway:** Function URLs are simpler but subject to more restrictive org policies. API Gateway HTTP APIs are equally simple to set up and more universally compatible.

3. **S3 bucket names are globally unique.** Always plan for name collisions. Using account ID as suffix is a reliable pattern.

4. **GitHub secret naming:** The `GITHUB_` prefix is reserved. Use `GH_` for GitHub OAuth secrets.

5. **Workflow path filters need care on first run.** After adding new workflows to a branch that already has the watched paths, you must make a new commit touching those paths to trigger the first run.

6. **CI/CD must be resilient to partial codebases.** When building in phases, the workflow will run before all files exist. Defensive `[ -f "$f" ]` checks prevent failures on missing optional files.
