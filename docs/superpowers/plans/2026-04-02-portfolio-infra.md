# Portfolio Site — Infrastructure & CI/CD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provision all AWS resources and configure GitHub Actions CI/CD pipelines so that pushing to `dev` or `prod` automatically deploys backend and frontend independently.

**Architecture:** Two Lambda functions (portfolio-dev, portfolio-prod) with Function URLs; two S3+CloudFront distributions; one shared DynamoDB table with 3 GSIs; SES sender identity; path-based GitHub Actions workflows triggered by `backend/**` or `frontend/**` changes.

**Tech Stack:** AWS CLI v2, GitHub Actions, Python 3.12, DynamoDB (on-demand), S3, CloudFront (OAC), Lambda Function URL, SES

---

## File Structure

**Created in this plan:**
- `version.txt` — version string, start at `0.1.0`
- `backend/handler.py` — hello-world Lambda placeholder (replaced in backend plan)
- `backend/requirements.txt` — Python deps placeholder (populated in backend plan)
- `frontend/index.html` — placeholder HTML (replaced in frontend plan)
- `frontend/assets/.gitkeep` — keeps assets directory in git
- `infra/iam-policy.json` — IAM permissions policy document (committed for reference)
- `.github/workflows/deploy-backend.yml` — backend CI/CD workflow
- `.github/workflows/deploy-frontend.yml` — frontend CI/CD workflow

**Not in this plan:** Route code, model code, real frontend HTML — those are Plans 2 and 3.

---

### Task 1: Repository structure + branches

**Files:**
- Create: `version.txt`
- Create: `backend/handler.py`
- Create: `backend/requirements.txt`
- Create: `frontend/index.html`
- Create: `frontend/assets/.gitkeep`

- [ ] **Step 1: Create version.txt**

```
0.1.0
```

- [ ] **Step 2: Create hello-world Lambda handler**

```python
# backend/handler.py
import json


def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps({"data": {"message": "Portfolio API"}, "error": None}),
    }
```

- [ ] **Step 3: Create requirements.txt placeholder**

```
boto3>=1.34.0
PyJWT>=2.8.0
requests>=2.31.0
```

- [ ] **Step 4: Create frontend placeholder**

```html
<!-- frontend/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Ron Harifiyati</title>
</head>
<body>
  <h1>Portfolio — coming soon</h1>
</body>
</html>
```

- [ ] **Step 5: Create assets directory marker**

```bash
touch frontend/assets/.gitkeep
```

- [ ] **Step 6: Commit initial structure**

```bash
git add version.txt backend/ frontend/
git commit -m "chore: initial repo structure with hello-world Lambda and placeholder frontend"
```

- [ ] **Step 7: Create and push dev branch**

```bash
git checkout -b dev
git push origin dev
git checkout main
git push origin main
```

Expected: GitHub shows branches `main` and `dev`.

---

### Task 2: Create DynamoDB table with GSIs and TTL

**Prerequisites:** AWS CLI configured. Verify:
```bash
aws sts get-caller-identity
```
Expected: JSON with your account ID and user ARN.

- [ ] **Step 1: Create the portfolio table**

```bash
aws dynamodb create-table \
  --table-name portfolio \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
    AttributeName=GSI1PK,AttributeType=S \
    AttributeName=GSI1SK,AttributeType=S \
    AttributeName=GSI2PK,AttributeType=S \
    AttributeName=GSI2SK,AttributeType=S \
    AttributeName=GSI3PK,AttributeType=S \
    AttributeName=GSI3SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --global-secondary-indexes '[
    {
      "IndexName": "GSI1",
      "KeySchema": [
        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
        {"AttributeName": "GSI1SK", "KeyType": "RANGE"}
      ],
      "Projection": {"ProjectionType": "ALL"}
    },
    {
      "IndexName": "GSI2",
      "KeySchema": [
        {"AttributeName": "GSI2PK", "KeyType": "HASH"},
        {"AttributeName": "GSI2SK", "KeyType": "RANGE"}
      ],
      "Projection": {"ProjectionType": "ALL"}
    },
    {
      "IndexName": "GSI3",
      "KeySchema": [
        {"AttributeName": "GSI3PK", "KeyType": "HASH"},
        {"AttributeName": "GSI3SK", "KeyType": "RANGE"}
      ],
      "Projection": {"ProjectionType": "ALL"}
    }
  ]' \
  --region us-east-1
```

Expected: JSON with `TableDescription.TableStatus: "CREATING"`

- [ ] **Step 2: Wait for table to become active**

```bash
aws dynamodb wait table-exists --table-name portfolio --region us-east-1
echo "Table is ACTIVE"
```

- [ ] **Step 3: Enable TTL on the `ttl` attribute**

```bash
aws dynamodb update-time-to-live \
  --table-name portfolio \
  --time-to-live-specification "Enabled=true,AttributeName=ttl" \
  --region us-east-1
```

Expected: `{"TimeToLiveSpecification": {"Enabled": true, "AttributeName": "ttl"}}`

- [ ] **Step 4: Verify table, GSIs, and TTL**

```bash
aws dynamodb describe-table --table-name portfolio --region us-east-1 \
  --query 'Table.{Status:TableStatus,GSIs:GlobalSecondaryIndexes[*].IndexName}'
```

Expected: `Status: "ACTIVE"`, GSIs: `["GSI1", "GSI2", "GSI3"]`

---

### Task 3: Create IAM role for Lambda

- [ ] **Step 1: Create the trust policy document**

```bash
cat > /tmp/trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
```

- [ ] **Step 2: Create the IAM role**

```bash
aws iam create-role \
  --role-name portfolio-lambda-role \
  --assume-role-policy-document file:///tmp/trust-policy.json
```

Expected: JSON with `Role.RoleName: "portfolio-lambda-role"`. **Save the `Role.Arn` value.**

- [ ] **Step 3: Create the permissions policy document**

```bash
mkdir -p infra
cat > infra/iam-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoDB",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:*:table/portfolio",
        "arn:aws:dynamodb:us-east-1:*:table/portfolio/index/*"
      ]
    },
    {
      "Sid": "SES",
      "Effect": "Allow",
      "Action": ["ses:SendEmail"],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatch",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
EOF
```

- [ ] **Step 4: Create the policy and attach to role**

```bash
POLICY_ARN=$(aws iam create-policy \
  --policy-name portfolio-lambda-policy \
  --policy-document file://infra/iam-policy.json \
  --query 'Policy.Arn' \
  --output text)

aws iam attach-role-policy \
  --role-name portfolio-lambda-role \
  --policy-arn $POLICY_ARN

echo "Attached: $POLICY_ARN"
```

- [ ] **Step 5: Verify**

```bash
aws iam list-attached-role-policies --role-name portfolio-lambda-role
```

Expected: `portfolio-lambda-policy` listed under `AttachedPolicies`.

- [ ] **Step 6: Commit IAM policy doc**

```bash
git add infra/iam-policy.json
git commit -m "chore: add IAM permissions policy document"
```

---

### Task 4: Create Lambda functions (dev + prod)

- [ ] **Step 1: Package the hello-world handler**

```bash
cd backend && zip -j /tmp/hello.zip handler.py && cd ..
```

- [ ] **Step 2: Get the role ARN**

```bash
ROLE_ARN=$(aws iam get-role \
  --role-name portfolio-lambda-role \
  --query 'Role.Arn' \
  --output text)
echo $ROLE_ARN
```

- [ ] **Step 3: Create portfolio-dev**

```bash
aws lambda create-function \
  --function-name portfolio-dev \
  --runtime python3.12 \
  --role $ROLE_ARN \
  --handler handler.handler \
  --zip-file fileb:///tmp/hello.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{ENVIRONMENT=dev,DYNAMODB_TABLE_NAME=portfolio}" \
  --region us-east-1
```

Expected: JSON with `State: "Pending"` then becomes `"Active"`.

- [ ] **Step 4: Create portfolio-prod**

```bash
aws lambda create-function \
  --function-name portfolio-prod \
  --runtime python3.12 \
  --role $ROLE_ARN \
  --handler handler.handler \
  --zip-file fileb:///tmp/hello.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{ENVIRONMENT=prod,DYNAMODB_TABLE_NAME=portfolio}" \
  --region us-east-1
```

- [ ] **Step 5: Wait for both to be active**

```bash
aws lambda wait function-active --function-name portfolio-dev --region us-east-1
aws lambda wait function-active --function-name portfolio-prod --region us-east-1
echo "Both functions active"
```

- [ ] **Step 6: Enable Function URLs**

```bash
DEV_URL=$(aws lambda create-function-url-config \
  --function-name portfolio-dev \
  --auth-type NONE \
  --cors '{"AllowOrigins":["*"],"AllowHeaders":["Content-Type","Authorization"],"AllowMethods":["GET","POST","PUT","DELETE","OPTIONS"]}' \
  --query 'FunctionUrl' --output text --region us-east-1)

PROD_URL=$(aws lambda create-function-url-config \
  --function-name portfolio-prod \
  --auth-type NONE \
  --cors '{"AllowOrigins":["*"],"AllowHeaders":["Content-Type","Authorization"],"AllowMethods":["GET","POST","PUT","DELETE","OPTIONS"]}' \
  --query 'FunctionUrl' --output text --region us-east-1)

echo "Dev URL:  $DEV_URL"
echo "Prod URL: $PROD_URL"
```

**Save both URLs** — the frontend API client needs them.

- [ ] **Step 7: Allow public invocation via Function URL**

```bash
for FN in portfolio-dev portfolio-prod; do
  aws lambda add-permission \
    --function-name $FN \
    --statement-id AllowPublicAccess \
    --action lambda:InvokeFunctionUrl \
    --principal "*" \
    --function-url-auth-type NONE \
    --region us-east-1
done
```

- [ ] **Step 8: Smoke test**

```bash
curl $DEV_URL
```

Expected: `{"data": {"message": "Portfolio API"}, "error": null}`

---

### Task 5: Create S3 buckets (dev + prod)

- [ ] **Step 1: Create buckets**

```bash
aws s3api create-bucket --bucket portfolio-frontend-dev --region us-east-1
aws s3api create-bucket --bucket portfolio-frontend-prod --region us-east-1
```

- [ ] **Step 2: Block all public access (CloudFront-only access)**

```bash
for BUCKET in portfolio-frontend-dev portfolio-frontend-prod; do
  aws s3api put-public-access-block \
    --bucket $BUCKET \
    --public-access-block-configuration \
      BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
done
```

- [ ] **Step 3: Upload placeholder index.html**

```bash
aws s3 cp frontend/index.html s3://portfolio-frontend-dev/
aws s3 cp frontend/index.html s3://portfolio-frontend-prod/
```

---

### Task 6: Create CloudFront distributions (dev + prod)

- [ ] **Step 1: Get your AWS account ID**

```bash
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo $AWS_ACCOUNT_ID
```

- [ ] **Step 2: Create Origin Access Control (OAC)**

```bash
OAC_ID=$(aws cloudfront create-origin-access-control \
  --origin-access-control-config '{
    "Name": "portfolio-s3-oac",
    "Description": "OAC for portfolio S3 buckets",
    "SigningProtocol": "sigv4",
    "SigningBehavior": "always",
    "OriginAccessControlOriginType": "s3"
  }' \
  --query 'OriginAccessControl.Id' --output text)
echo "OAC ID: $OAC_ID"
```

- [ ] **Step 3: Create CloudFront distribution for dev**

```bash
DEV_CF_JSON=$(aws cloudfront create-distribution \
  --distribution-config "{
    \"CallerReference\": \"portfolio-dev-$(date +%s)\",
    \"Comment\": \"Portfolio Dev\",
    \"DefaultRootObject\": \"index.html\",
    \"Origins\": {
      \"Quantity\": 1,
      \"Items\": [{
        \"Id\": \"S3-portfolio-frontend-dev\",
        \"DomainName\": \"portfolio-frontend-dev.s3.us-east-1.amazonaws.com\",
        \"S3OriginConfig\": {\"OriginAccessIdentity\": \"\"},
        \"OriginAccessControlId\": \"$OAC_ID\"
      }]
    },
    \"DefaultCacheBehavior\": {
      \"TargetOriginId\": \"S3-portfolio-frontend-dev\",
      \"ViewerProtocolPolicy\": \"redirect-to-https\",
      \"CachePolicyId\": \"658327ea-f89d-4fab-a63d-7e88639e58f6\",
      \"AllowedMethods\": {\"Quantity\": 2, \"Items\": [\"GET\", \"HEAD\"]},
      \"Compress\": true
    },
    \"CustomErrorResponses\": {
      \"Quantity\": 2,
      \"Items\": [
        {\"ErrorCode\": 403, \"ResponseCode\": \"200\", \"ResponsePagePath\": \"/index.html\", \"ErrorCachingMinTTL\": 0},
        {\"ErrorCode\": 404, \"ResponseCode\": \"200\", \"ResponsePagePath\": \"/index.html\", \"ErrorCachingMinTTL\": 0}
      ]
    },
    \"Enabled\": true,
    \"HttpVersion\": \"http2\"
  }")

DEV_CF_ID=$(echo $DEV_CF_JSON | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['Distribution']['Id'])")
DEV_CF_DOMAIN=$(echo $DEV_CF_JSON | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['Distribution']['DomainName'])")
echo "Dev CF ID:     $DEV_CF_ID"
echo "Dev CF Domain: $DEV_CF_DOMAIN"
```

- [ ] **Step 4: Create CloudFront distribution for prod**

```bash
PROD_CF_JSON=$(aws cloudfront create-distribution \
  --distribution-config "{
    \"CallerReference\": \"portfolio-prod-$(date +%s)\",
    \"Comment\": \"Portfolio Prod\",
    \"DefaultRootObject\": \"index.html\",
    \"Origins\": {
      \"Quantity\": 1,
      \"Items\": [{
        \"Id\": \"S3-portfolio-frontend-prod\",
        \"DomainName\": \"portfolio-frontend-prod.s3.us-east-1.amazonaws.com\",
        \"S3OriginConfig\": {\"OriginAccessIdentity\": \"\"},
        \"OriginAccessControlId\": \"$OAC_ID\"
      }]
    },
    \"DefaultCacheBehavior\": {
      \"TargetOriginId\": \"S3-portfolio-frontend-prod\",
      \"ViewerProtocolPolicy\": \"redirect-to-https\",
      \"CachePolicyId\": \"658327ea-f89d-4fab-a63d-7e88639e58f6\",
      \"AllowedMethods\": {\"Quantity\": 2, \"Items\": [\"GET\", \"HEAD\"]},
      \"Compress\": true
    },
    \"CustomErrorResponses\": {
      \"Quantity\": 2,
      \"Items\": [
        {\"ErrorCode\": 403, \"ResponseCode\": \"200\", \"ResponsePagePath\": \"/index.html\", \"ErrorCachingMinTTL\": 0},
        {\"ErrorCode\": 404, \"ResponseCode\": \"200\", \"ResponsePagePath\": \"/index.html\", \"ErrorCachingMinTTL\": 0}
      ]
    },
    \"Enabled\": true,
    \"HttpVersion\": \"http2\"
  }")

PROD_CF_ID=$(echo $PROD_CF_JSON | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['Distribution']['Id'])")
PROD_CF_DOMAIN=$(echo $PROD_CF_JSON | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['Distribution']['DomainName'])")
echo "Prod CF ID:     $PROD_CF_ID"
echo "Prod CF Domain: $PROD_CF_DOMAIN"
```

- [ ] **Step 5: Apply S3 bucket policies (allow CloudFront OAC reads)**

```bash
# Dev bucket
cat > /tmp/dev-bucket-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "cloudfront.amazonaws.com"},
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::portfolio-frontend-dev/*",
    "Condition": {
      "StringEquals": {
        "AWS:SourceArn": "arn:aws:cloudfront::${AWS_ACCOUNT_ID}:distribution/${DEV_CF_ID}"
      }
    }
  }]
}
EOF
aws s3api put-bucket-policy --bucket portfolio-frontend-dev --policy file:///tmp/dev-bucket-policy.json

# Prod bucket
cat > /tmp/prod-bucket-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "cloudfront.amazonaws.com"},
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::portfolio-frontend-prod/*",
    "Condition": {
      "StringEquals": {
        "AWS:SourceArn": "arn:aws:cloudfront::${AWS_ACCOUNT_ID}:distribution/${PROD_CF_ID}"
      }
    }
  }]
}
EOF
aws s3api put-bucket-policy --bucket portfolio-frontend-prod --policy file:///tmp/prod-bucket-policy.json
```

- [ ] **Step 6: Wait for distributions to deploy (~5 min) and test**

```bash
aws cloudfront wait distribution-deployed --id $DEV_CF_ID
curl https://$DEV_CF_DOMAIN
```

Expected: HTML content of `frontend/index.html`.

---

### Task 7: Verify SES sender email identity

- [ ] **Step 1: Request email verification**

```bash
aws ses verify-email-identity \
  --email-address YOUR_EMAIL@example.com \
  --region us-east-1
```

Expected: Empty 200 response. AWS sends a verification email to `YOUR_EMAIL@example.com`.

- [ ] **Step 2: Click the verification link in the email AWS sent.**

- [ ] **Step 3: Confirm verification succeeded**

```bash
aws ses get-identity-verification-attributes \
  --identities YOUR_EMAIL@example.com \
  --region us-east-1
```

Expected: `"VerificationStatus": "Success"`

**Note on SES sandbox mode:** By default SES can only send to verified addresses. For production use, request production access: AWS Console → SES → Account dashboard → Request production access. For development and testing, sandbox mode is sufficient.

---

### Task 8: Configure GitHub Secrets

Go to: **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

- [ ] **Step 1: Create a dedicated IAM user for GitHub Actions**

```bash
aws iam create-user --user-name github-actions-portfolio

# Attach only the permissions CI/CD needs
aws iam attach-user-policy \
  --user-name github-actions-portfolio \
  --policy-arn arn:aws:iam::aws:policy/AWSLambda_FullAccess

aws iam attach-user-policy \
  --user-name github-actions-portfolio \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-user-policy \
  --user-name github-actions-portfolio \
  --policy-arn arn:aws:iam::aws:policy/CloudFrontFullAccess

# Create access keys — save these immediately
KEYS=$(aws iam create-access-key --user-name github-actions-portfolio)
echo "Key ID:     $(echo $KEYS | python3 -c \"import json,sys; print(json.load(sys.stdin)['AccessKey']['AccessKeyId'])\")"
echo "Secret Key: $(echo $KEYS | python3 -c \"import json,sys; print(json.load(sys.stdin)['AccessKey']['SecretAccessKey'])\")"
```

- [ ] **Step 2: Add all secrets to GitHub**

| Secret Name | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | from Step 1 |
| `AWS_SECRET_ACCESS_KEY` | from Step 1 |
| `AWS_REGION` | `us-east-1` |
| `DEV_LAMBDA_FUNCTION_NAME` | `portfolio-dev` |
| `PROD_LAMBDA_FUNCTION_NAME` | `portfolio-prod` |
| `DEV_S3_BUCKET` | `portfolio-frontend-dev` |
| `PROD_S3_BUCKET` | `portfolio-frontend-prod` |
| `DEV_CLOUDFRONT_ID` | `$DEV_CF_ID` from Task 6 |
| `PROD_CLOUDFRONT_ID` | `$PROD_CF_ID` from Task 6 |
| `JWT_SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `SES_SENDER_EMAIL` | your verified email from Task 7 |
| `GITHUB_OAUTH_CLIENT_ID` | from GitHub OAuth App (see below) |
| `GITHUB_OAUTH_CLIENT_SECRET` | from GitHub OAuth App |
| `GOOGLE_OAUTH_CLIENT_ID` | from Google Cloud Console |
| `GOOGLE_OAUTH_CLIENT_SECRET` | from Google Cloud Console |
| `DISCORD_WEBHOOK` | optional — Discord channel webhook URL |

**Create GitHub OAuth App:**
1. github.com/settings/developers → OAuth Apps → New OAuth App
2. Homepage URL: `https://$PROD_CF_DOMAIN`
3. Authorization callback URL: `$PROD_URL/auth/oauth/github/callback`
4. Copy Client ID and generate Client Secret

**Create Google OAuth Credentials:**
1. console.cloud.google.com → APIs & Services → Credentials → Create → OAuth 2.0 Client ID
2. Application type: Web application
3. Authorized redirect URIs: `$PROD_URL/auth/oauth/google/callback`
4. Copy Client ID and Client Secret

---

### Task 9: Write deploy-backend.yml

**Files:**
- Create: `.github/workflows/deploy-backend.yml`

- [ ] **Step 1: Create the workflow**

```yaml
# .github/workflows/deploy-backend.yml
name: Deploy Backend

on:
  push:
    branches: [dev, prod]
    paths:
      - 'backend/**'
      - 'version.txt'

jobs:
  test-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-mock "moto[dynamodb,ses]" flake8

      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --tb=short

      - name: Lint
        run: |
          cd backend
          flake8 . --max-line-length=120 --exclude=tests/,package/

      - name: Set deploy environment
        run: |
          if [[ "${{ github.ref_name }}" == "prod" ]]; then
            echo "LAMBDA_NAME=${{ secrets.PROD_LAMBDA_FUNCTION_NAME }}" >> $GITHUB_ENV
            echo "DEPLOY_ENV=prod" >> $GITHUB_ENV
          else
            echo "LAMBDA_NAME=${{ secrets.DEV_LAMBDA_FUNCTION_NAME }}" >> $GITHUB_ENV
            echo "DEPLOY_ENV=dev" >> $GITHUB_ENV
          fi
          echo "VERSION=$(cat version.txt)" >> $GITHUB_ENV

      - name: Package Lambda
        run: |
          cd backend
          pip install -r requirements.txt -t package/ --quiet
          cp handler.py router.py auth.py db.py utils.py package/
          cp -r routes/ models/ package/
          cd package && zip -r ../lambda.zip . -x "*.pyc" -x "*__pycache__*"

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Deploy Lambda code
        run: |
          aws lambda update-function-code \
            --function-name $LAMBDA_NAME \
            --zip-file fileb://backend/lambda.zip \
            --region ${{ secrets.AWS_REGION }}
          aws lambda wait function-updated \
            --function-name $LAMBDA_NAME \
            --region ${{ secrets.AWS_REGION }}

      - name: Stamp Lambda environment variables
        run: |
          aws lambda update-function-configuration \
            --function-name $LAMBDA_NAME \
            --environment "Variables={GIT_SHA=${{ github.sha }},DEPLOY_TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ),ENVIRONMENT=$DEPLOY_ENV,VERSION=$VERSION,JWT_SECRET_KEY=${{ secrets.JWT_SECRET_KEY }},SES_SENDER_EMAIL=${{ secrets.SES_SENDER_EMAIL }},GITHUB_OAUTH_CLIENT_ID=${{ secrets.GITHUB_OAUTH_CLIENT_ID }},GITHUB_OAUTH_CLIENT_SECRET=${{ secrets.GITHUB_OAUTH_CLIENT_SECRET }},GOOGLE_OAUTH_CLIENT_ID=${{ secrets.GOOGLE_OAUTH_CLIENT_ID }},GOOGLE_OAUTH_CLIENT_SECRET=${{ secrets.GOOGLE_OAUTH_CLIENT_SECRET }},DYNAMODB_TABLE_NAME=portfolio}" \
            --region ${{ secrets.AWS_REGION }}

      - name: Notify Discord
        if: always()
        run: |
          curl -s -X POST "${{ secrets.DISCORD_WEBHOOK }}" \
            -H "Content-Type: application/json" \
            -d "{\"content\": \"**Backend** deploy to **$DEPLOY_ENV**: ${{ job.status }} | SHA: \`${{ github.sha }}\`\"}" || true
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/deploy-backend.yml
git commit -m "ci: add backend deploy workflow"
```

---

### Task 10: Write deploy-frontend.yml

**Files:**
- Create: `.github/workflows/deploy-frontend.yml`

- [ ] **Step 1: Create the workflow**

```yaml
# .github/workflows/deploy-frontend.yml
name: Deploy Frontend

on:
  push:
    branches: [dev, prod]
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Validate HTML
        run: |
          pip install html5validator
          html5validator --root frontend/ || true

      - name: Set deploy environment
        run: |
          if [[ "${{ github.ref_name }}" == "prod" ]]; then
            echo "S3_BUCKET=${{ secrets.PROD_S3_BUCKET }}" >> $GITHUB_ENV
            echo "CF_DISTRIBUTION=${{ secrets.PROD_CLOUDFRONT_ID }}" >> $GITHUB_ENV
            echo "DEPLOY_ENV=prod" >> $GITHUB_ENV
          else
            echo "S3_BUCKET=${{ secrets.DEV_S3_BUCKET }}" >> $GITHUB_ENV
            echo "CF_DISTRIBUTION=${{ secrets.DEV_CLOUDFRONT_ID }}" >> $GITHUB_ENV
            echo "DEPLOY_ENV=dev" >> $GITHUB_ENV
          fi

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Sync assets to S3 (long cache)
        run: |
          aws s3 sync frontend/ s3://$S3_BUCKET \
            --delete \
            --cache-control "max-age=86400" \
            --exclude "*.html"

      - name: Sync HTML to S3 (no cache)
        run: |
          aws s3 sync frontend/ s3://$S3_BUCKET \
            --delete \
            --exclude "*" --include "*.html" \
            --cache-control "no-cache"

      - name: Invalidate CloudFront cache
        run: |
          INVALIDATION_ID=$(aws cloudfront create-invalidation \
            --distribution-id $CF_DISTRIBUTION \
            --paths "/*" \
            --query 'Invalidation.Id' --output text)
          echo "Invalidation: $INVALIDATION_ID"

      - name: Notify Discord
        if: always()
        run: |
          curl -s -X POST "${{ secrets.DISCORD_WEBHOOK }}" \
            -H "Content-Type: application/json" \
            -d "{\"content\": \"**Frontend** deploy to **$DEPLOY_ENV**: ${{ job.status }} | SHA: \`${{ github.sha }}\`\"}" || true
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/deploy-frontend.yml
git commit -m "ci: add frontend deploy workflow"
```

---

### Task 11: Smoke test end-to-end CI/CD

- [ ] **Step 1: Push all commits to dev branch**

```bash
git checkout dev
git merge main
git push origin dev
```

- [ ] **Step 2: Watch GitHub Actions**

Go to GitHub repo → **Actions** tab. Expect two workflows triggered:
- `Deploy Backend` (triggered by `backend/**` path change)
- `Deploy Frontend` (triggered by `frontend/**` path change)

Both should show green checkmarks within ~3 minutes.

- [ ] **Step 3: Verify backend is live**

```bash
DEV_URL=$(aws lambda get-function-url-config \
  --function-name portfolio-dev \
  --query 'FunctionUrl' --output text --region us-east-1)

curl $DEV_URL
```

Expected: `{"data": {"message": "Portfolio API"}, "error": null}`

- [ ] **Step 4: Verify Lambda env vars were stamped**

```bash
aws lambda get-function-configuration \
  --function-name portfolio-dev \
  --query 'Environment.Variables.{SHA:GIT_SHA,Timestamp:DEPLOY_TIMESTAMP,Env:ENVIRONMENT}' \
  --region us-east-1
```

Expected: `SHA` matches the latest commit hash, `Env: "dev"`.

- [ ] **Step 5: Verify frontend is live**

```bash
DEV_CF_DOMAIN=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Comment=='Portfolio Dev'].DomainName" \
  --output text)

curl https://$DEV_CF_DOMAIN
```

Expected: HTML from `frontend/index.html`.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "chore: infrastructure complete, CI/CD smoke tested"
git push origin dev
```

---

## Checklist before starting Backend Plan

- [ ] DynamoDB `portfolio` table is ACTIVE with GSI1, GSI2, GSI3 and TTL enabled on `ttl` attribute
- [ ] `portfolio-lambda-role` IAM role has DynamoDB, SES, and CloudWatch permissions
- [ ] `portfolio-dev` and `portfolio-prod` Lambda functions are ACTIVE with Function URLs enabled
- [ ] S3 buckets `portfolio-frontend-dev` and `portfolio-frontend-prod` exist with public access blocked
- [ ] CloudFront distributions for dev and prod are DEPLOYED and serving `index.html`
- [ ] SES sender email is verified
- [ ] All GitHub Secrets are set (AWS credentials, Lambda names, S3 buckets, CF IDs, JWT secret, OAuth credentials)
- [ ] Pushing to `dev` triggers both workflows and deploys successfully
- [ ] Lambda env vars (GIT_SHA, DEPLOY_TIMESTAMP, ENVIRONMENT) are visible after deploy
- [ ] Note down: Dev Lambda Function URL, Prod Lambda Function URL, Dev CF domain, Prod CF domain
