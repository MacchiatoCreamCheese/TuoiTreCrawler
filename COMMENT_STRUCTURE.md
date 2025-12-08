# Comment Structure Reference

## Complete Comment Schema

```json
{
  "commentId": "comment_123456",
  "author": "Nguyễn Văn A",
  "text": "Bài viết rất hay và bổ ích. Cảm ơn tác giả!",
  "date": "2024-12-08T10:30:00",
  "vote_react_list": {
    "like": 15,
    "love": 3,
    "haha": 1
  },
  "depth": 0,
  "replies": [
    {
      "commentId": "comment_789012",
      "author": "Trần Thị B",
      "text": "Tôi hoàn toàn đồng ý với bạn!",
      "date": "2024-12-08T11:00:00",
      "vote_react_list": {
        "like": 8
      },
      "depth": 1,
      "replies": [
        {
          "commentId": "comment_345678",
          "author": "Lê Văn C",
          "text": "Cảm ơn các bạn đã chia sẻ.",
          "date": "2024-12-08T11:30:00",
          "vote_react_list": {},
          "depth": 2,
          "replies": []
        }
      ]
    }
  ]
}
```

## Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `commentId` | string | ✅ | Unique identifier for the comment |
| `author` | string | ✅ | Name of comment author |
| `text` | string | ✅ | Comment text content |
| `date` | string/null | ⚠️ | ISO timestamp or date string |
| `vote_react_list` | object | ✅ | Vote reactions (can be empty {}) |
| `depth` | integer | ✅ | Nesting level (0 = top-level) |
| `replies` | array | ✅ | Nested reply comments (can be empty []) |

**Legend:**
- ✅ Always present
- ⚠️ May be null if not found

## Nesting Depth Examples

### Depth 0 - Top-level Comment
```
Comment by User A
├─ depth: 0
└─ replies: [...]
```

### Depth 1 - Reply to Top-level
```
Comment by User A
└─ Reply by User B
   ├─ depth: 1
   └─ replies: [...]
```

### Depth 2 - Reply to Reply
```
Comment by User A
└─ Reply by User B
   └─ Reply by User C
      ├─ depth: 2
      └─ replies: [...]
```

### Depth 3+ - Deeper Nesting
```
Comment by User A
└─ Reply by User B
   └─ Reply by User C
      └─ Reply by User D
         ├─ depth: 3
         └─ replies: [...]
```

## Visual Tree Structure

```
Post: "Tin tức về kinh tế Việt Nam"
│
├─ [Comment 1] Nguyễn Văn A: "Bài viết rất hay..."
│  ├─ Reactions: like:15, love:3
│  ├─ Depth: 0
│  └─ Replies:
│     ├─ [Comment 1.1] Trần Thị B: "Tôi đồng ý..."
│     │  ├─ Reactions: like:8
│     │  ├─ Depth: 1
│     │  └─ Replies:
│     │     └─ [Comment 1.1.1] Lê Văn C: "Cảm ơn..."
│     │        ├─ Reactions: {}
│     │        ├─ Depth: 2
│     │        └─ Replies: []
│     │
│     └─ [Comment 1.2] Phạm Thị D: "Rất hữu ích"
│        ├─ Reactions: like:5
│        ├─ Depth: 1
│        └─ Replies: []
│
├─ [Comment 2] Hoàng Văn E: "Thông tin cần thiết"
│  ├─ Reactions: like:20, love:5, haha:2
│  ├─ Depth: 0
│  └─ Replies: []
│
└─ [Comment 3] Đỗ Thị F: "Cảm ơn tác giả"
   ├─ Reactions: like:12
   ├─ Depth: 0
   └─ Replies:
      └─ [Comment 3.1] Vũ Văn G: "Đồng ý!"
         ├─ Reactions: like:3
         ├─ Depth: 1
         └─ Replies: []
```

## Vote Reaction Types

### Standard Reactions
```json
{
  "like": 10,    // 👍 Like/Thumbs up
  "love": 5,     // ❤️ Love/Heart
  "haha": 3,     // 😄 Laugh/Funny
  "wow": 2,      // 😮 Wow/Surprised
  "sad": 1,      // 😢 Sad
  "angry": 1     // 😠 Angry
}
```

### Empty Reactions
```json
{}  // No reactions on comment
```

## Comment Count Examples

### Example 1: Simple Structure
```
3 top-level comments
2 replies total
= 5 total comments

Structure:
├─ Comment 1
│  └─ Reply 1.1
├─ Comment 2
└─ Comment 3
   └─ Reply 3.1
```

### Example 2: Nested Structure
```
2 top-level comments
5 replies (various depths)
= 7 total comments

Structure:
├─ Comment 1
│  └─ Reply 1.1
│     └─ Reply 1.1.1
│        └─ Reply 1.1.1.1
└─ Comment 2
   └─ Reply 2.1
      └─ Reply 2.1.1
```

### Example 3: Wide Structure
```
5 top-level comments
20 direct replies
= 25 total comments

Structure:
├─ Comment 1
│  ├─ Reply 1.1
│  ├─ Reply 1.2
│  ├─ Reply 1.3
│  └─ Reply 1.4
├─ Comment 2
│  ├─ Reply 2.1
│  └─ Reply 2.2
├─ Comment 3
│  ├─ Reply 3.1
│  ├─ Reply 3.2
│  ├─ Reply 3.3
│  ├─ Reply 3.4
│  └─ Reply 3.5
├─ Comment 4
│  ├─ Reply 4.1
│  ├─ Reply 4.2
│  └─ Reply 4.3
└─ Comment 5
   ├─ Reply 5.1
   ├─ Reply 5.2
   └─ Reply 5.3
```

## 20+ Comments Validation

### Scenario 1: Meets Requirement ✅
```python
comments = [
  {
    "commentId": "1",
    "text": "Comment 1",
    "replies": [
      {"commentId": "2", "text": "Reply 1.1", "replies": []},
      {"commentId": "3", "text": "Reply 1.2", "replies": [
        {"commentId": "4", "text": "Reply 1.2.1", "replies": []}
      ]}
    ]
  },
  {
    "commentId": "5",
    "text": "Comment 2",
    "replies": [
      {"commentId": "6", "text": "Reply 2.1", "replies": []},
      # ... 15 more replies
    ]
  }
]

Total: 25 comments
validate_comment_count(comments, 20) → True ✅
```

### Scenario 2: Does Not Meet ✗
```python
comments = [
  {"commentId": "1", "text": "Comment 1", "replies": []},
  {"commentId": "2", "text": "Comment 2", "replies": [
    {"commentId": "3", "text": "Reply 2.1", "replies": []}
  ]},
  {"commentId": "4", "text": "Comment 3", "replies": []}
]

Total: 4 comments
validate_comment_count(comments, 20) → False ✗
```

### Scenario 3: No Comments ✗
```python
comments = []

Total: 0 comments
validate_comment_count(comments, 20) → False ✗
```

## Statistics Example

```python
comments = extract_comments(scraper, post_url)
stats = get_comment_statistics(comments)

# Example output:
{
  'total_comments': 45,
  'top_level_comments': 10,
  'max_depth': 3,
  'depth_distribution': {
    0: 10,  # 10 top-level
    1: 20,  # 20 direct replies
    2: 12,  # 12 replies to replies
    3: 3    # 3 deeply nested
  },
  'comments_with_reactions': 35,
  'average_replies_per_comment': 3.5
}
```

## Edge Cases

### No Comments
```json
[]
```
- Total count: 0
- Meets 20+ requirement: False
- Safe to process

### Comment Without Author
```json
{
  "commentId": "123",
  "author": "Anonymous",  // Default fallback
  "text": "Comment text",
  "date": null,
  "vote_react_list": {},
  "depth": 0,
  "replies": []
}
```

### Comment Without Reactions
```json
{
  "commentId": "123",
  "author": "User",
  "text": "Comment text",
  "date": "2024-12-08T10:00:00",
  "vote_react_list": {},  // Empty dict, not null
  "depth": 0,
  "replies": []
}
```

### Maximum Depth Reached
```json
{
  "commentId": "parent",
  "depth": 10,
  "replies": []  // Empty even if more replies exist
}
```
When `depth >= MAX_COMMENT_DEPTH`, recursion stops and `replies` is empty.

## Processing Patterns

### Pattern 1: Iterate All Comments
```python
def process_all_comments(comments):
    for comment in comments:
        process_comment(comment)
        # Recursively process replies
        if comment['replies']:
            process_all_comments(comment['replies'])
```

### Pattern 2: Flatten Comment Tree
```python
def flatten_comments(comments, result=[]):
    for comment in comments:
        result.append(comment)
        if comment['replies']:
            flatten_comments(comment['replies'], result)
    return result

# Usage
all_comments = flatten_comments(comments)
print(f"Total: {len(all_comments)}")
```

### Pattern 3: Find Comments by Criteria
```python
def find_comments_by_author(comments, author_name):
    found = []
    for comment in comments:
        if comment['author'] == author_name:
            found.append(comment)
        if comment['replies']:
            found.extend(find_comments_by_author(comment['replies'], author_name))
    return found
```

### Pattern 4: Count Reactions
```python
def total_reactions(comments):
    total = {}
    for comment in comments:
        for reaction_type, count in comment['vote_react_list'].items():
            total[reaction_type] = total.get(reaction_type, 0) + count
        if comment['replies']:
            reply_reactions = total_reactions(comment['replies'])
            for reaction_type, count in reply_reactions.items():
                total[reaction_type] = total.get(reaction_type, 0) + count
    return total
```

## Summary

**Comment Structure Features:**
- ✅ Recursive nested replies (unlimited depth)
- ✅ All required fields always present
- ✅ Graceful handling of missing data
- ✅ Vietnamese text support
- ✅ Vote reactions for each comment
- ✅ Depth tracking for visualization
- ✅ Empty structures for no data

**Use Cases:**
- Extract all comments from a post
- Validate 20+ comments requirement
- Generate comment statistics
- Build comment trees for display
- Analyze engagement (reactions)
- Export to JSON for storage
