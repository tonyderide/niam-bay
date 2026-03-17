#!/bin/bash
# Publish an article to DEV.to via their API
# Usage: ./scripts/publish-devto.sh <article-file.md> [publish]
# Requires DEV_TO_API_KEY environment variable or GitHub secret

set -euo pipefail

ARTICLE_FILE="${1:?Usage: $0 <article-file.md> [publish]}"
PUBLISH="${2:-false}"

if [ -z "${DEV_TO_API_KEY:-}" ]; then
  echo "Error: DEV_TO_API_KEY not set"
  echo "Get yours at: https://dev.to/settings/extensions"
  exit 1
fi

if [ ! -f "$ARTICLE_FILE" ]; then
  echo "Error: File not found: $ARTICLE_FILE"
  exit 1
fi

# Extract front matter and body
TITLE=$(grep '^title:' "$ARTICLE_FILE" | sed 's/^title: *"\(.*\)"/\1/')
DESCRIPTION=$(grep '^description:' "$ARTICLE_FILE" | sed 's/^description: *"\(.*\)"/\1/')
TAGS=$(grep '^tags:' "$ARTICLE_FILE" | sed 's/^tags: *//')
CANONICAL=$(grep '^canonical_url:' "$ARTICLE_FILE" | sed 's/^canonical_url: *//')

# Get body (everything after the second ---)
BODY=$(awk '/^---$/{c++; next} c>=2' "$ARTICLE_FILE")

# Build JSON payload
PAYLOAD=$(jq -n \
  --arg title "$TITLE" \
  --arg body "$BODY" \
  --arg description "$DESCRIPTION" \
  --arg tags "$TAGS" \
  --arg canonical "$CANONICAL" \
  --argjson published "$([ "$PUBLISH" = "publish" ] && echo true || echo false)" \
  '{
    article: {
      title: $title,
      body_markdown: $body,
      description: $description,
      tags: ($tags | split(", ")),
      canonical_url: $canonical,
      published: $published
    }
  }')

echo "Publishing: $TITLE"
echo "Published: $([ "$PUBLISH" = "publish" ] && echo "YES" || echo "DRAFT")"

RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "api-key: ${DEV_TO_API_KEY}" \
  -d "$PAYLOAD" \
  https://dev.to/api/articles)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY_RESPONSE=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
  URL=$(echo "$BODY_RESPONSE" | jq -r '.url')
  echo "Success! Article URL: $URL"
else
  echo "Error (HTTP $HTTP_CODE):"
  echo "$BODY_RESPONSE" | jq .
  exit 1
fi
