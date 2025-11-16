#!/bin/bash
"""
AWS Lambda Deployment Script for Daily Soccer Reports
Creates and deploys the Lambda function with all dependencies
"""

echo "🚀 AWS Lambda Deployment for Daily Soccer Reports"
echo "=================================================="

# Configuration
FUNCTION_NAME="daily-soccer-reports"
REGION="us-east-1"
EMAIL_RECIPIENT="your-email@domain.com"  # <<<< CHANGE THIS
SENDER_EMAIL="soccer-reports@your-domain.com"  # <<<< CHANGE THIS

# Create deployment directory
DEPLOY_DIR="lambda_deployment"
rm -rf $DEPLOY_DIR
mkdir $DEPLOY_DIR

echo "📦 Creating deployment package..."

# Copy Python files (exclude output reports and temp files)
cp *.py $DEPLOY_DIR/
cp *.pkl $DEPLOY_DIR/ 2>/dev/null || true
cp *.json $DEPLOY_DIR/ 2>/dev/null || true

# Copy requirements
cp requirements.txt $DEPLOY_DIR/

echo "📋 Installing Python dependencies..."
cd $DEPLOY_DIR

# Install dependencies
pip install -r requirements.txt -t .

# Remove unnecessary files to reduce package size
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo "🗜️ Creating deployment zip..."
zip -r ../soccer-lambda.zip . -x "*.DS_Store" "output*" "*.log"

cd ..

echo "☁️ Deploying to AWS Lambda..."

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION >/dev/null 2>&1; then
    echo "📝 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://soccer-lambda.zip \
        --region $REGION
else
    echo "🆕 Creating new Lambda function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.9 \
        --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
        --handler lambda_function.lambda_handler \
        --zip-file fileb://soccer-lambda.zip \
        --timeout 900 \
        --memory-size 1024 \
        --region $REGION \
        --environment Variables="{EMAIL_RECIPIENT=$EMAIL_RECIPIENT,SENDER_EMAIL=$SENDER_EMAIL}"
fi

echo "⏰ Setting up EventBridge trigger for 6 AM daily..."

# Create EventBridge rule for 6 AM UTC (adjust timezone as needed)
aws events put-rule \
    --name daily-soccer-trigger \
    --schedule-expression "cron(0 6 * * ? *)" \
    --description "Daily trigger for soccer reports at 6 AM" \
    --region $REGION

# Add permission for EventBridge to invoke Lambda
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id daily-soccer-trigger \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:$REGION:YOUR_ACCOUNT_ID:rule/daily-soccer-trigger \
    --region $REGION 2>/dev/null || true

# Add Lambda as target for EventBridge rule
aws events put-targets \
    --rule daily-soccer-trigger \
    --targets "Id"="1","Arn"="arn:aws:lambda:$REGION:YOUR_ACCOUNT_ID:function:$FUNCTION_NAME" \
    --region $REGION

echo "✅ Deployment complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Verify your email in AWS SES:"
echo "   aws ses verify-email-identity --email-address $EMAIL_RECIPIENT --region $REGION"
echo "   aws ses verify-email-identity --email-address $SENDER_EMAIL --region $REGION"
echo ""
echo "2. Update IAM role with SES permissions"
echo ""
echo "3. Test the function:"
echo "   aws lambda invoke --function-name $FUNCTION_NAME --region $REGION response.json"
echo ""
echo "💰 Estimated monthly cost: \$1-5 USD"

# Cleanup
rm -rf $DEPLOY_DIR
rm soccer-lambda.zip