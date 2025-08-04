#\!/bin/bash
echo "Testing API deployment..."
attempt=1
max_attempts=10

while [ $attempt -le $max_attempts ]; do
    echo -e "\n🔄 Attempt $attempt of $max_attempts"
    
    # Test the API
    response=$(curl -s -X POST https://exa-lead-enrichment-api-production.up.railway.app/enrich \
      -H "Content-Type: application/json" \
      -d '{"query": "superintendent + leadership at beverlyparkgolf.org"}')
    
    # Check if response contains error
    if echo "$response" | grep -q '"status":"error"'; then
        error=$(echo "$response" | jq -r '.error')
        echo "❌ Error: $error"
        
        if [ $attempt -lt $max_attempts ]; then
            echo "⏳ Waiting 30 seconds before retry..."
            sleep 30
        fi
    else
        echo "✅ Success\! API is working\!"
        echo "$response" | jq .
        exit 0
    fi
    
    ((attempt++))
done

echo "❌ Failed after $max_attempts attempts"
exit 1
