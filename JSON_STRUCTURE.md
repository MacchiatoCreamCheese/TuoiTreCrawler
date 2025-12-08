# JSON Structure Reference

## Standard Post JSON Structure

```json
{
  "postId": "123456",
  "title": "Tin tức về kinh tế Việt Nam năm 2024",
  "content": {
    "text": "Plain text content...",
    "html": "<p>HTML content...</p>"
  },
  "author": "Nguyễn Văn A",
  "date": "2024-12-08T10:30:00",
  "category": "kinh-doanh",
  "audio_url": "https://example.com/audio/123456.mp3",
  "vote_reactions": {
    "like": 150,
    "love": 45,
    "haha": 10
  },
  "comments": [
    {
      "commentId": "comment_1",
      "author": "Trần Thị B",
      "text": "Bài viết rất hay!",
      "date": "2024-12-08T11:00:00",
      "vote_react_list": {
        "like": 25
      },
      "depth": 0,
      "replies": [
        {
          "commentId": "comment_1_1",
          "author": "Lê Văn C",
          "text": "Tôi đồng ý!",
          "date": "2024-12-08T11:30:00",
          "vote_react_list": {
            "like": 10
          },
          "depth": 1,
          "replies": []
        }
      ]
    }
  ],
  "metadata": {
    "crawled_at": "2024-12-08T14:00:00",
    "crawler_version": "1.0.0",
    "data_format_version": "1.0"
  }
}
```

## Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `postId` | string | ✅ | Unique post identifier |
| `title` | string | ✅ | Post title (Vietnamese text) |
| `content` | string or object | ✅ | Post content (text and/or HTML) |
| `author` | string | ⚠️ | Author name (optional) |
| `date` | string | ⚠️ | Publication date (ISO 8601) |
| `category` | string | ⚠️ | Post category |
| `audio_url` | string | ⚠️ | URL to audio file (if available) |
| `vote_reactions` | object | ⚠️ | Vote reactions dictionary |
| `comments` | array | ⚠️ | List of comments with nested replies |
| `metadata` | object | ⚠️ | Crawl metadata (auto-added) |

**Legend:**
- ✅ Required field (validation fails if missing)
- ⚠️ Optional field (can be null or missing)

## Content Field Variations

### Option 1: String
```json
{
  "content": "Plain text content here..."
}
```

### Option 2: Object with text and HTML
```json
{
  "content": {
    "text": "Plain text version",
    "html": "<p>HTML version</p>"
  }
}
```

## Usage Examples

### Save Single Post
```python
from crawler.json_exporter import save_post_json

post_data = {
    'postId': '123456',
    'title': 'Bài viết mẫu',
    'content': 'Nội dung bài viết...',
    'author': 'Tác giả',
    'date': '2024-12-08',
    'category': 'thoi-su',
    'audio_url': None,
    'vote_reactions': {},
    'comments': []
}

file_path = save_post_json(post_data)
# Saves to: data/123456.json
```

### Save Multiple Posts
```python
from crawler.json_exporter import save_multiple_posts

posts = [post1, post2, post3]
saved_files = save_multiple_posts(posts)
# Saves to: data/post1.json, data/post2.json, data/post3.json
```

### Save Combined JSON
```python
from crawler.json_exporter import save_combined_json

posts = [post1, post2, post3]
file_path = save_combined_json(posts, output_file='data/all_posts.json')
# Saves all posts in one file with metadata
```

## Vietnamese Text Encoding

All JSON files are saved with:
- **Encoding**: UTF-8
- **ensure_ascii**: False (preserves Vietnamese characters)
- **Validation**: Checks for encoding issues before saving

### Example Vietnamese Characters Preserved:
```json
{
  "title": "Tiếng Việt: àáảãạ ăắằẳẵặ âấầẩẫậ đ èéẻẽẹ êếềểễệ",
  "author": "Nguyễn Văn Đức",
  "content": "Các ký tự: ìíỉĩị òóỏõọ ôốồổỗộ ơớờởỡợ ùúủũụ ưứừửữự ỳýỷỹỵ"
}
```

## Validation

### Automatic Validation
```python
# Validation is enabled by default
save_post_json(post_data, validate=True)
```

### Manual Validation
```python
from crawler.json_exporter import validate_post_data

is_valid, errors = validate_post_data(post_data)

if is_valid:
    print("✓ Data is valid")
else:
    print(f"✗ Validation errors: {errors}")
```

### Validation Checks

1. ✅ Required fields present (postId, title, content)
2. ✅ Field types correct (string, dict, list, etc.)
3. ✅ Nested comment structure valid
4. ✅ No encoding issues
5. ✅ All comments have required fields

## Directory Structure

```
data/
├── 123456.json          # Individual post files
├── 789012.json
├── 345678.json
└── all_posts.json       # Combined file (optional)
```

Directories are created automatically if they don't exist.
