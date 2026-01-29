#!/bin/bash
# Script para configurar notificações S3 após deploy

set -e

ENVIRONMENT=${1:-dev}
BUCKET_NAME="myp-cards-csv-${ENVIRONMENT}-$(aws sts get-caller-identity --query Account --output text)"
FUNCTION_NAME="myp-cards-producer-${ENVIRONMENT}"

echo "🔧 Configurando notificações S3..."
echo "📦 Bucket: ${BUCKET_NAME}"
echo "⚡ Function: ${FUNCTION_NAME}"

# Obter ARN da função
FUNCTION_ARN=$(aws lambda get-function --function-name ${FUNCTION_NAME} --query 'Configuration.FunctionArn' --output text)
echo "✅ Function ARN: ${FUNCTION_ARN}"

# Configurar notificação S3
aws s3api put-bucket-notification-configuration \
  --bucket ${BUCKET_NAME} \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [
      {
        "Id": "csv-uploads-trigger",
        "LambdaFunctionArn": "'${FUNCTION_ARN}'",
        "Events": ["s3:ObjectCreated:*"],
        "Filter": {
          "Key": {
            "FilterRules": [
              {
                "Name": "prefix",
                "Value": "csv-uploads/"
              }
            ]
          }
        }
      },
      {
        "Id": "csv-excluir-trigger",
        "LambdaFunctionArn": "'${FUNCTION_ARN}'",
        "Events": ["s3:ObjectCreated:*"],
        "Filter": {
          "Key": {
            "FilterRules": [
              {
                "Name": "prefix",
                "Value": "csv-excluir/"
              }
            ]
          }
        }
      },
      {
        "Id": "csv-recadastrar-trigger",
        "LambdaFunctionArn": "'${FUNCTION_ARN}'",
        "Events": ["s3:ObjectCreated:*"],
        "Filter": {
          "Key": {
            "FilterRules": [
              {
                "Name": "prefix",
                "Value": "csv-recadastrar/"
              }
            ]
          }
        }
      }
    ]
  }'

echo "✅ Notificações S3 configuradas com sucesso!"
