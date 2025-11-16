# 🚀 AWS Lambda Automation Setup for Daily Soccer Reports

Automate your soccer betting reports to be generated and emailed daily at 6 AM using AWS Lambda, EventBridge, and SES.

## 🎯 What This Does

- **Runs daily at 6 AM** (UTC) - adjust timezone as needed
- **Generates all soccer reports** automatically
- **Emails reports as attachments** to your specified email
- **Costs ~$1-5/month** (much cheaper than keeping EC2 running)
- **Zero maintenance** - fully serverless

## 📋 Prerequisites

1. **AWS CLI installed and configured**
   ```bash
   aws configure
   ```

2. **AWS Account with permissions for:**
   - Lambda
   - EventBridge (CloudWatch Events)
   - SES (Simple Email Service)
   - IAM

## 🚀 Quick Setup (5 minutes)

### Step 1: Edit Configuration
Edit `deploy_lambda.sh` and update these lines:
```bash
EMAIL_RECIPIENT="your-actual-email@gmail.com"      # Your email
SENDER_EMAIL="soccer-reports@your-domain.com"      # Sender email
```

### Step 2: Run Deployment Script
```bash
./deploy_lambda.sh
```

### Step 3: Verify Email Addresses in SES
```bash
# Verify recipient email
aws ses verify-email-identity --email-address your-actual-email@gmail.com --region us-east-1

# Verify sender email
aws ses verify-email-identity --email-address soccer-reports@your-domain.com --region us-east-1

# Check verification status
aws ses list-verified-email-addresses --region us-east-1
```

### Step 4: Create IAM Role (if needed)
If you don't have a Lambda execution role, create one:

```bash
# Create trust policy
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name lambda-execution-role \
  --assume-role-policy-document file://trust-policy.json

# Attach basic Lambda permissions
aws iam attach-role-policy \
  --role-name lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Attach SES permissions
aws iam attach-role-policy \
  --role-name lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonSESFullAccess
```

### Step 5: Test the Function
```bash
aws lambda invoke \
  --function-name daily-soccer-reports \
  --region us-east-1 \
  response.json

cat response.json
```

## 📧 Email Setup Options

### Option A: Use Your Gmail (Simplest)
- Set `EMAIL_RECIPIENT` to your Gmail address
- Set `SENDER_EMAIL` to the same Gmail address
- Verify both in SES

### Option B: Use Custom Domain
- Own a domain (e.g., mydomain.com)
- Set `SENDER_EMAIL` to something like `soccer@mydomain.com`
- Verify domain in SES (more complex but more professional)

## ⏰ Schedule Configuration

Default: **6 AM UTC daily**

To change timezone/time, edit the cron expression in `deploy_lambda.sh`:
```bash
# 6 AM EST (11 AM UTC)
"cron(0 11 * * ? *)"

# 6 AM PST (2 PM UTC)
"cron(0 14 * * ? *)"

# 8 AM UTC daily
"cron(0 8 * * ? *)"
```

## 📊 What Gets Emailed

**Attached Files:**
- `daily_picks_YYYYMMDD.csv` - All 500+ betting opportunities
- `daily_report_YYYYMMDD.txt` - Human-readable summary
- `high_confidence_picks_YYYYMMDD.csv` - 85%+ confidence picks
- `top8_daily_tracker.csv` - Best daily picks with tracking
- `strategy_comparison.txt` - Performance comparison

**Email Content:**
- Analysis summary (matches analyzed, opportunities found)
- File descriptions
- Generation timestamp
- Responsible gambling reminder

## 💰 Cost Breakdown

**Monthly Costs (estimated):**
- Lambda execution: ~$0.50-2.00
- SES emails: ~$0.10-1.00
- EventBridge: ~$0.00-0.10
- **Total: $1-5/month**

Much cheaper than keeping an EC2 instance running 24/7 (~$15-30/month).

## 🔧 Troubleshooting

### Common Issues:

1. **Email not sent**
   - Check SES email verification status
   - Verify Lambda has SES permissions
   - Check CloudWatch logs

2. **Lambda timeout**
   - Increase timeout in `deploy_lambda.sh` (current: 900 seconds)
   - Check memory allocation (current: 1024 MB)

3. **No reports generated**
   - Check if API key is valid
   - Verify internet access in Lambda
   - Check CloudWatch logs for errors

### Debugging Commands:
```bash
# Check Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/daily-soccer"

# Check EventBridge rule
aws events describe-rule --name daily-soccer-trigger

# Test email sending manually
aws ses send-email \
  --source soccer-reports@your-domain.com \
  --destination ToAddresses=your-email@gmail.com \
  --message Subject={Data="Test"},Body={Text={Data="Test message"}}
```

## 🛡️ Security Best Practices

1. **Use least privilege IAM permissions**
2. **Keep API keys in environment variables** (already done)
3. **Enable CloudTrail** for audit logging
4. **Use SES in sandbox mode** initially to prevent abuse

## 📈 Monitoring

**CloudWatch Metrics to Monitor:**
- Lambda Duration
- Lambda Errors
- SES Bounce Rate
- SES Complaint Rate

**Set up CloudWatch Alarms:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "Soccer-Reports-Failures" \
  --alarm-description "Alert when soccer reports fail" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold
```

## 🎉 Ready to Go!

Once set up, you'll receive comprehensive soccer betting reports every morning at 6 AM with:
- ✅ **500+ betting opportunities** analyzed
- ✅ **High-confidence picks** highlighted
- ✅ **Historical tracking** of performance
- ✅ **Professional formatting** ready for use
- ✅ **Zero maintenance required**

Your soccer betting analysis is now fully automated! 🚀⚽