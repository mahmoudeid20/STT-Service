#!/bin/bash

# STT Service Test Script
# Tests all endpoints of the STT service

set -e

BASE_URL="http://localhost:5002"
USER_ID="test_user_$(date +%s)"

echo "🧪 Testing STT Service"
echo "======================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local expected_code=$4
    
    echo -n "Testing $name... "
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" -H "Content-Type: application/json")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" -eq "$expected_code" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Expected $expected_code, got $http_code)"
        return 1
    fi
}

# 1. Health Check
test_endpoint "Health Check" "GET" "/health" 200

# 2. Get Supported Languages
test_endpoint "Get Languages" "GET" "/api/v1/languages" 200

# 3. Get Supported Formats
test_endpoint "Get Formats" "GET" "/api/v1/formats" 200

# 4. Test transcription without file (should fail)
echo -n "Testing Transcribe (no file)... "
response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/transcribe")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" -eq 400 ]; then
    echo -e "${GREEN}✓ PASSED${NC} (Expected error)"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

# 5. Test with audio file (if exists)
if [ -f "test_audio.wav" ]; then
    echo -n "Testing Transcribe (with file)... "
    response=$(curl -s -w "\n%{http_code}" \
        -X POST "$BASE_URL/transcribe" \
        -F "audio=@test_audio.wav" \
        -F "user_id=$USER_ID" \
        -F "language=en-US")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        transcription_id=$(echo "$body" | grep -o '"transcription_id":"[^"]*"' | cut -d'"' -f4)
        echo "  Transcription ID: $transcription_id"
        
        # 6. Get transcription by ID
        if [ ! -z "$transcription_id" ]; then
            test_endpoint "Get Transcription" "GET" "/transcriptions/$transcription_id" 200
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (Note: May fail without valid audio file)"
    fi
else
    echo "⚠ Skipping audio transcription test (test_audio.wav not found)"
fi

# 7. Create Session
echo -n "Testing Create Session... "
response=$(curl -s -w "\n%{http_code}" \
    -X POST "$BASE_URL/api/v1/sessions" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$USER_ID\", \"session_name\": \"Test Session\"}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" -eq 201 ]; then
    echo -e "${GREEN}✓ PASSED${NC}"
    session_id=$(echo "$body" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
    echo "  Session ID: $session_id"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

# 8. Get User Transcriptions
test_endpoint "Get User Transcriptions" "GET" "/transcriptions/user/$USER_ID" 200

# 9. Get Statistics
test_endpoint "Get Statistics" "GET" "/statistics" 200

# 10. Test invalid transcription ID
echo -n "Testing Invalid Transcription ID... "
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/transcriptions/invalid_id")
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" -eq 404 ]; then
    echo -e "${GREEN}✓ PASSED${NC} (Expected 404)"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

echo ""
echo "======================="
echo "✅ Test suite completed"
echo ""
echo "To create a test audio file:"
echo "ffmpeg -f lavfi -i sine=frequency=1000:duration=5 -ar 16000 test_audio.wav"
