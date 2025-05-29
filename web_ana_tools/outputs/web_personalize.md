# 网页个性化程度分析报告

## 分析文件: ./websites/amazon.com/2020/20201231235544_index.html

总得分: 9/30 (30.0%)

## 各类别得分

| 类别 | 得分 | 满分 |
|------|------|------|
| 用户识别与账户相关个性化 | 2 | 5 |
| 内容推荐与个性化展示 | 2 | 5 |
| 用户行为跟踪与数据收集 | 3 | 5 |
| 地理位置与本地化个性化 | 1 | 5 |
| 技术实现与API | 1 | 5 |
| 购物车与交易个性化 | 0 | 5 |

## 检测到的个性化特征

### 用户识别与账户相关个性化 - username_display

- 来源: element_text
- 值: Hello, Sign in
- 匹配模式: hello,\s+\w+

### 用户识别与账户相关个性化 - order_history

- 来源: script_inline
- 值: Your Orders
- 匹配模式: your orders

### 内容推荐与个性化展示 - search_suggestion

- 来源: script_inline
- 值: Search suggestions
- 匹配模式: search suggestions

### 内容推荐与个性化展示 - personalized_ads

- 来源: element_text
- 值: Interest-Based Ads
- 匹配模式: interest-based ads

### 用户行为跟踪与数据收集 - tracking_scripts

- 来源: script_inline
- 值: g-Accessories
- 匹配模式: G-[A-Z0-9]{10,}

### 用户行为跟踪与数据收集 - user_session_id

- 来源: script_inline
- 值: sessionId
- 匹配模式: session[_\-]?id

### 用户行为跟踪与数据收集 - preference_storage

- 来源: script_inline
- 值: localStorage.setItem
- 匹配模式: localStorage\.setItem

### 地理位置与本地化个性化 - location_detection

- 来源: script_inline
- 值: geolocation
- 匹配模式: geolocation

### 技术实现与API - ab_testing

- 来源: script_inline
- 值: vWo
- 匹配模式: vwo

