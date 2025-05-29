import os
import pandas as pd
import re
import json
from bs4 import BeautifulSoup
from collections import defaultdict
import glob
from tqdm import tqdm
import time
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

class PersonalizationAnalyzer:
    def __init__(self):
        # 定义六大类个性化特征的检测模式
        self.personalization_patterns = {
            # 1. 用户识别与账户相关个性化
            'user_identification': {
                'username_display': [
                    r'welcome,\s+\w+',
                    r'你好,\s+\w+',
                    r'hi,\s+\w+',
                    r'hello,\s+\w+',
                    r'user-name',
                    r'username',
                    r'user_name',
                    r'account-name',
                    r'account_name',
                    r'data-username',
                    r'data-user-name',
                    r'class="[^"]*user-name[^"]*"',
                    r'id="[^"]*user-name[^"]*"',
                    r'class="[^"]*username[^"]*"',
                    r'id="[^"]*username[^"]*"'
                ],
                'personalized_greeting': [
                    r'welcome back',
                    r'欢迎回来',
                    r'welcome home',
                    r'good (morning|afternoon|evening),\s+\w+',
                    r'(早上|下午|晚上)好,\s+\w+',
                    r'personalized-greeting',
                    r'user-greeting',
                    r'class="[^"]*greeting[^"]*"',
                    r'id="[^"]*greeting[^"]*"'
                ],
                'order_history': [
                    r'order history',
                    r'my orders',
                    r'your orders',
                    r'订单历史',
                    r'我的订单',
                    r'历史订单',
                    r'recent orders',
                    r'最近订单',
                    r'order-history',
                    r'order_history',
                    r'class="[^"]*order-history[^"]*"',
                    r'id="[^"]*order-history[^"]*"'
                ],
                'membership_points': [
                    r'membership level',
                    r'会员等级',
                    r'vip level',
                    r'loyalty points',
                    r'reward points',
                    r'积分',
                    r'会员积分',
                    r'your points',
                    r'您的积分',
                    r'points balance',
                    r'积分余额',
                    r'class="[^"]*member-(level|points)[^"]*"',
                    r'id="[^"]*member-(level|points)[^"]*"'
                ],
                'profile_completion': [
                    r'complete your profile',
                    r'完善个人资料',
                    r'profile completion',
                    r'资料完整度',
                    r'profile progress',
                    r'个人资料进度',
                    r'missing profile information',
                    r'缺少的个人信息',
                    r'class="[^"]*profile-completion[^"]*"',
                    r'id="[^"]*profile-completion[^"]*"'
                ]
            },
            
            # 2. 内容推荐与个性化展示
            'content_recommendation': {
                'product_recommendation': [
                    r'recommended for you',
                    r'为您推荐',
                    r'personalized recommendations',
                    r'个性化推荐',
                    r'you might also like',
                    r'您可能还喜欢',
                    r'based on your',
                    r'根据您的',
                    r'tailored for you',
                    r'为您定制',
                    r'class="[^"]*personalized-recommendations[^"]*"',
                    r'id="[^"]*personalized-recommendations[^"]*"'
                ],
                'recommendation_section': [
                    r'recommended section',
                    r'推荐区域',
                    r'for you section',
                    r'为您推荐区域',
                    r'personalized section',
                    r'个性化区域',
                    r'class="[^"]*recommendations-section[^"]*"',
                    r'id="[^"]*recommendations-section[^"]*"',
                    r'data-section-type="recommendations"',
                    r'data-section="personalized"'
                ],
                'recently_viewed': [
                    r'recently viewed',
                    r'最近浏览',
                    r'you recently viewed',
                    r'您最近浏览过',
                    r'history viewed',
                    r'浏览历史',
                    r'viewed products',
                    r'浏览过的商品',
                    r'class="[^"]*recently-viewed[^"]*"',
                    r'id="[^"]*recently-viewed[^"]*"'
                ],
                'search_suggestion': [
                    r'search suggestions',
                    r'搜索建议',
                    r'personalized search',
                    r'个性化搜索',
                    r'recent searches',
                    r'最近搜索',
                    r'search history',
                    r'搜索历史',
                    r'class="[^"]*search-suggestions[^"]*"',
                    r'id="[^"]*search-suggestions[^"]*"'
                ],
                'personalized_ads': [
                    r'personalized ads',
                    r'个性化广告',
                    r'targeted ads',
                    r'定向广告',
                    r'ads based on',
                    r'根据.+的广告',
                    r'interest-based ads',
                    r'兴趣广告',
                    r'class="[^"]*personalized-ads[^"]*"',
                    r'id="[^"]*personalized-ads[^"]*"',
                    r'data-ad-client',
                    r'data-ad-personalized'
                ]
            },
            
            # 3. 用户行为跟踪与数据收集
            'user_tracking': {
                'tracking_scripts': [
                    r'google-analytics\.com/analytics\.js',
                    r'gtag\(.*\)',
                    r'ga\(.*\)',
                    r'GoogleAnalyticsObject',
                    r'google-analytics\.com/ga\.js',
                    r'G-[A-Z0-9]{10,}',  # GA4 测量ID
                    r'UA-[0-9]+-[0-9]+',  # Universal Analytics ID
                    r'googletagmanager\.com/gtm\.js',
                    r'dataLayer\.push\(',
                    r'GTM-[A-Z0-9]+',
                    r'connect\.facebook\.net/en_US/fbevents\.js',
                    r'fbq\(',
                    r'_fbq',
                    r'facebook-jssdk',
                    r'facebook\.com/tr\?',
                    r'hotjar\.com',
                    r'clarity\.ms',
                    r'matomo\.js',
                    r'piwik\.js',
                    r'mixpanel',
                    r'heap\.js',
                    r'fullstory\.com',
                    r'segment\.com',
                    r'amplitude\.com'
                ],
                'user_session_id': [
                    r'session[_\-]?id',
                    r'会话[_\-]?id',
                    r'user[_\-]?id',
                    r'用户[_\-]?id',
                    r'visitor[_\-]?id',
                    r'访客[_\-]?id',
                    r'client[_\-]?id',
                    r'客户[_\-]?id',
                    r'data-user-id',
                    r'data-session-id',
                    r'data-visitor-id'
                ],
                'cookie_consent': [
                    r'cookie consent',
                    r'cookie政策',
                    r'cookie同意',
                    r'accept cookies',
                    r'接受cookie',
                    r'cookie preferences',
                    r'cookie设置',
                    r'gdpr consent',
                    r'gdpr同意',
                    r'privacy settings',
                    r'隐私设置',
                    r'class="[^"]*cookie-consent[^"]*"',
                    r'id="[^"]*cookie-consent[^"]*"',
                    r'data-consent'
                ],
                'preference_storage': [
                    r'store preferences',
                    r'存储偏好',
                    r'save preferences',
                    r'保存偏好',
                    r'user preferences',
                    r'用户偏好',
                    r'preference settings',
                    r'偏好设置',
                    r'localStorage\.setItem',
                    r'sessionStorage\.setItem',
                    r'document\.cookie',
                    r'setCookie',
                    r'set_cookie',
                    r'class="[^"]*user-preferences[^"]*"',
                    r'id="[^"]*user-preferences[^"]*"'
                ],
                'heatmap_tracking': [
                    r'heatmap',
                    r'热图',
                    r'click tracking',
                    r'点击跟踪',
                    r'mouse tracking',
                    r'鼠标跟踪',
                    r'user behavior',
                    r'用户行为',
                    r'scroll depth',
                    r'滚动深度',
                    r'hotjar',
                    r'crazyegg',
                    r'clicktale',
                    r'mouseflow'
                ]
            },
            
            # 4. 地理位置与本地化个性化
            'geo_localization': {
                'location_detection': [
                    r'geolocation',
                    r'地理位置',
                    r'detect location',
                    r'检测位置',
                    r'current location',
                    r'当前位置',
                    r'navigator\.geolocation',
                    r'ip geolocation',
                    r'ip地理位置',
                    r'location services',
                    r'位置服务',
                    r'class="[^"]*geolocation[^"]*"',
                    r'id="[^"]*geolocation[^"]*"',
                    r'data-location'
                ],
                'localized_content': [
                    r'localized content',
                    r'本地化内容',
                    r'region specific',
                    r'区域特定',
                    r'content for your region',
                    r'您所在区域的内容',
                    r'local offers',
                    r'本地优惠',
                    r'in your area',
                    r'在您的区域',
                    r'class="[^"]*localized-content[^"]*"',
                    r'id="[^"]*localized-content[^"]*"',
                    r'data-region'
                ],
                'currency_language': [
                    r'auto currency',
                    r'自动货币',
                    r'currency selector',
                    r'货币选择器',
                    r'language selector',
                    r'语言选择器',
                    r'auto detect language',
                    r'自动检测语言',
                    r'change currency',
                    r'更改货币',
                    r'change language',
                    r'更改语言',
                    r'class="[^"]*currency-selector[^"]*"',
                    r'id="[^"]*currency-selector[^"]*"',
                    r'class="[^"]*language-selector[^"]*"',
                    r'id="[^"]*language-selector[^"]*"',
                    r'data-currency',
                    r'data-language'
                ],
                'regional_promotion': [
                    r'regional promotions',
                    r'区域促销',
                    r'local promotions',
                    r'本地促销',
                    r'special offers in',
                    r'特别优惠在',
                    r'deals in your area',
                    r'您所在区域的优惠',
                    r'region specific offers',
                    r'区域特定优惠',
                    r'class="[^"]*regional-promotion[^"]*"',
                    r'id="[^"]*regional-promotion[^"]*"',
                    r'data-promotion-region'
                ],
                'shipping_options': [
                    r'shipping options',
                    r'配送选项',
                    r'delivery options',
                    r'送货选项',
                    r'shipping to your location',
                    r'配送到您的位置',
                    r'available in your area',
                    r'您所在区域可用',
                    r'shipping calculator',
                    r'配送计算器',
                    r'class="[^"]*shipping-options[^"]*"',
                    r'id="[^"]*shipping-options[^"]*"',
                    r'data-shipping-region'
                ]
            },
            
            # 5. 技术实现与API
            'technical_implementation': {
                'personalization_api': [
                    r'personalization api',
                    r'个性化api',
                    r'recommendation api',
                    r'推荐api',
                    r'api\.personalize',
                    r'api/recommendations',
                    r'api/personalized',
                    r'fetch\([\'"].*?/personalize',
                    r'fetch\([\'"].*?/recommend',
                    r'axios\.get\([\'"].*?/personalize',
                    r'axios\.get\([\'"].*?/recommend',
                    r'\.ajax\({[^}]*url:\s*[\'"].*?/personalize',
                    r'\.ajax\({[^}]*url:\s*[\'"].*?/recommend'
                ],
                'dynamic_content': [
                    r'dynamic content',
                    r'动态内容',
                    r'content loader',
                    r'内容加载器',
                    r'lazy load personalized',
                    r'懒加载个性化',
                    r'async content',
                    r'异步内容',
                    r'dynamic rendering',
                    r'动态渲染',
                    r'class="[^"]*dynamic-content[^"]*"',
                    r'id="[^"]*dynamic-content[^"]*"',
                    r'data-dynamic-content',
                    r'data-async-content'
                ],
                'ab_testing': [
                    r'a/b test',
                    r'a/b测试',
                    r'split test',
                    r'分割测试',
                    r'variant test',
                    r'变体测试',
                    r'experiment id',
                    r'实验id',
                    r'optimizely',
                    r'google optimize',
                    r'vwo',
                    r'class="[^"]*ab-test[^"]*"',
                    r'id="[^"]*ab-test[^"]*"',
                    r'data-experiment',
                    r'data-variant'
                ],
                'user_segmentation': [
                    r'user segment',
                    r'用户细分',
                    r'customer segment',
                    r'客户细分',
                    r'audience segment',
                    r'受众细分',
                    r'segment id',
                    r'细分id',
                    r'user group',
                    r'用户组',
                    r'class="[^"]*user-segment[^"]*"',
                    r'id="[^"]*user-segment[^"]*"',
                    r'data-segment',
                    r'data-user-group'
                ],
                'realtime_engine': [
                    r'realtime personalization',
                    r'实时个性化',
                    r'personalization engine',
                    r'个性化引擎',
                    r'recommendation engine',
                    r'推荐引擎',
                    r'real-time recommendations',
                    r'实时推荐',
                    r'personalization service',
                    r'个性化服务',
                    r'class="[^"]*realtime-personalization[^"]*"',
                    r'id="[^"]*realtime-personalization[^"]*"',
                    r'data-realtime-personalization'
                ]
            },
            
            # 6. 购物车与交易个性化
            'cart_transaction': {
                'cart_persistence': [
                    r'saved cart',
                    r'保存的购物车',
                    r'persistent cart',
                    r'持久购物车',
                    r'cart session',
                    r'购物车会话',
                    r'remember cart',
                    r'记住购物车',
                    r'restore cart',
                    r'恢复购物车',
                    r'class="[^"]*saved-cart[^"]*"',
                    r'id="[^"]*saved-cart[^"]*"',
                    r'data-cart-persistence'
                ],
                'cart_recommendation': [
                    r'cart recommendations',
                    r'购物车推荐',
                    r'recommended with',
                    r'推荐搭配',
                    r'frequently bought together',
                    r'经常一起购买',
                    r'complete your purchase',
                    r'完成您的购买',
                    r'add to your cart',
                    r'添加到您的购物车',
                    r'class="[^"]*cart-recommendations[^"]*"',
                    r'id="[^"]*cart-recommendations[^"]*"',
                    r'data-cart-recommendation'
                ],
                'personalized_discount': [
                    r'personal discount',
                    r'个人折扣',
                    r'special offer for you',
                    r'专属优惠',
                    r'your coupon',
                    r'您的优惠券',
                    r'exclusive discount',
                    r'专属折扣',
                    r'personalized offer',
                    r'个性化优惠',
                    r'class="[^"]*personal-discount[^"]*"',
                    r'id="[^"]*personal-discount[^"]*"',
                    r'data-personal-discount',
                    r'data-user-coupon'
                ],
                'remarketing': [
                    r'abandoned cart',
                    r'购物车遗弃',
                    r'cart reminder',
                    r'购物车提醒',
                    r'complete your order',
                    r'完成您的订单',
                    r'return to cart',
                    r'返回购物车',
                    r'items waiting',
                    r'商品等待中',
                    r'class="[^"]*cart-reminder[^"]*"',
                    r'id="[^"]*cart-reminder[^"]*"',
                    r'data-cart-reminder'
                ],
                'one_click_purchase': [
                    r'one click purchase',
                    r'一键购买',
                    r'buy now',
                    r'立即购买',
                    r'express checkout',
                    r'快速结账',
                    r'quick buy',
                    r'快速购买',
                    r'instant purchase',
                    r'即时购买',
                    r'class="[^"]*one-click-purchase[^"]*"',
                    r'id="[^"]*one-click-purchase[^"]*"',
                    r'data-one-click-purchase',
                    r'data-express-checkout'
                ]
            }
        }
        
        # 定义个性化相关的HTML属性
        self.personalization_attributes = [
            'data-personalized', 'data-user', 'data-user-id', 'data-user-name',
            'data-user-preferences', 'data-recommendations', 'data-recommended',
            'data-recently-viewed', 'data-history', 'data-personalization',
            'data-segment', 'data-ab-test', 'data-experiment', 'data-variant',
            'data-location', 'data-region', 'data-geo', 'data-currency',
            'data-language', 'data-cart', 'data-cart-id', 'data-discount',
            'data-offer', 'data-coupon', 'data-one-click'
        ]
        
        # 预编译正则表达式
        self._compile_regex_patterns()
        
        # 初始化结果存储
        self.reset_results()
    
    def _compile_regex_patterns(self):
        """预编译所有正则表达式模式以提高性能"""
        self.compiled_patterns = {}
        
        for category, subcategories in self.personalization_patterns.items():
            self.compiled_patterns[category] = {}
            for subcategory, patterns in subcategories.items():
                self.compiled_patterns[category][subcategory] = [
                    re.compile(pattern, re.IGNORECASE) for pattern in patterns
                ]
    
    def reset_results(self):
        """重置分析结果"""
        self.feature_categories = set()  # 个性化特征类别
        self.feature_count = 0  # 个性化特征总数
        self.features = []  # 具体个性化特征列表
        self.feature_details = defaultdict(lambda: defaultdict(list))  # 按类型和子类型存储的详细特征
        self.category_scores = {}  # 各类别得分
        self.total_score = 0  # 总分
        self.max_score = 0  # 满分
    
    def analyze_html(self, html_content, show_progress=False):
        """分析HTML内容中的个性化特征"""
        self.reset_results()
        
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 一次性收集所有文本和属性数据
        text_data = []
        attribute_data = []
        
        # 收集所有文本节点
        for element in soup.find_all(string=True):
            if element.strip():  # 忽略空白文本
                text_data.append({
                    'text': element,
                    'parent': element.parent.name if element.parent else "unknown"
                })
        
        # 收集所有元素属性
        for element in soup.find_all():
            for attr_name, attr_value in element.attrs.items():
                if isinstance(attr_value, str):
                    attribute_data.append({
                        'element': element.name,
                        'attr_name': attr_name,
                        'attr_value': attr_value
                    })
        
        # 收集所有脚本内容
        script_data = []
        for script in soup.find_all('script'):
            # 检查脚本src属性
            if script.has_attr('src'):
                script_data.append({
                    'type': 'src',
                    'content': script['src']
                })
            
            # 检查内联脚本内容
            if script.string:
                script_data.append({
                    'type': 'inline',
                    'content': script.string
                })
        
        # 创建分析步骤列表
        analysis_steps = [
            ("分析脚本标签中的个性化特征", lambda: self._analyze_scripts(script_data)),
            ("分析所有文本和属性中的个性化特征", lambda: self._analyze_all_features(text_data, attribute_data))
        ]
        
        # 根据是否显示进度执行分析步骤
        if show_progress:
            for step_name, step_func in tqdm(analysis_steps, desc="个性化分析进度"):
                step_func()
        else:
            for _, step_func in analysis_steps:
                step_func()
        
        # 统计结果
        self.calculate_results()
        
        return self.get_results()
    
    def _analyze_scripts(self, script_data):
        """分析脚本标签中的个性化特征"""
        for script in script_data:
            content = script['content']
            source_type = f"script_{script['type']}"
            
            for category, subcategories in self.compiled_patterns.items():
                for subcategory, patterns in subcategories.items():
                    for pattern in patterns:
                        if script['type'] == 'src':
                            # 对于src属性，使用search
                            match = pattern.search(content)
                            if match:
                                self.feature_details[category][subcategory].append({
                                    'source': source_type,
                                    'value': content,
                                    'pattern': pattern.pattern
                                })
                        else:
                            # 对于内联脚本，使用findall
                            matches = pattern.findall(content)
                            for match in matches:
                                match_text = match if isinstance(match, str) else match[0]
                                self.feature_details[category][subcategory].append({
                                    'source': source_type,
                                    'value': match_text[:100] + ('...' if len(match_text) > 100 else ''),
                                    'pattern': pattern.pattern
                                })
    
    def _analyze_all_features(self, text_data, attribute_data):
        """一次性分析所有文本和属性中的个性化特征"""
        # 分析文本数据
        for item in text_data:
            text = item['text']
            parent = item['parent']
            
            for category, subcategories in self.compiled_patterns.items():
                for subcategory, patterns in subcategories.items():
                    for pattern in patterns:
                        if pattern.search(text):
                            self.feature_details[category][subcategory].append({
                                'source': 'element_text',
                                'element': parent,
                                'value': text[:100] + ('...' if len(text) > 100 else ''),
                                'pattern': pattern.pattern
                            })
                            # 找到一个匹配就足够了，不需要继续检查此文本的此子类别
                            break
        
        # 分析属性数据
        for item in attribute_data:
            element = item['element']
            attr_name = item['attr_name']
            attr_value = item['attr_value']
            
            for category, subcategories in self.compiled_patterns.items():
                for subcategory, patterns in subcategories.items():
                    for pattern in patterns:
                        if pattern.search(attr_value):
                            self.feature_details[category][subcategory].append({
                                'source': 'element_attribute',
                                'element': element,
                                'attribute': attr_name,
                                'value': attr_value[:100] + ('...' if len(attr_value) > 100 else ''),
                                'pattern': pattern.pattern
                            })
                            # 找到一个匹配就足够了，不需要继续检查此属性的此子类别
                            break
    
    def calculate_results(self):
        """计算最终结果"""
        # 初始化类别得分字典
        self.category_scores = {}
        
        # 计算每个类别的得分
        for category, subcategories in self.personalization_patterns.items():
            category_score = 0
            for subcategory, _ in subcategories.items():
                # 如果该子类别有检测到特征，得1分
                if self.feature_details[category][subcategory]:
                    category_score += 1
                    # 添加到特征列表
                    self.features.append({
                        'category': category,
                        'subcategory': subcategory,
                        'evidence': self.feature_details[category][subcategory][0]  # 只取第一个证据
                    })
            
            # 记录类别得分
            self.category_scores[category] = category_score
            # 添加类别到集合
            if category_score > 0:
                self.feature_categories.add(category)
        
        # 计算总分
        self.total_score = sum(self.category_scores.values())
        
        # 计算最大可能得分
        self.max_score = sum(len(subcategories) for subcategories in self.personalization_patterns.values())
        
        # 计算特征总数
        self.feature_count = len(self.features)
    
    def get_results(self):
        """获取分析结果"""
        return {
            'total_score': self.total_score,
            'max_score': self.max_score,
            'category_scores': self.category_scores,
            'feature_categories': list(self.feature_categories),
            'feature_count': self.feature_count,
            'features': self.features
        }

def analyze_website_personalization(html_path, show_progress=False):
    """分析单个网站的个性化程度"""
    try:
        print(f"正在读取文件: {html_path}")
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as file:
            html_content = file.read()
        
        print(f"开始分析文件: {html_path}")
        analyzer = PersonalizationAnalyzer()
        results = analyzer.analyze_html(html_content, show_progress)
        
        return {
            'file_path': html_path,
            'total_score': results['total_score'],
            'max_score': results['max_score'],
            'category_scores': results['category_scores'],
            'feature_categories': results['feature_categories'],
            'feature_count': results['feature_count'],
            'features': results['features']
        }
    except Exception as e:
        print(f"Error analyzing {html_path}: {e}")
        return {
            'file_path': html_path,
            'error': str(e),
            'total_score': 0,
            'max_score': 30,
            'category_scores': {},
            'feature_categories': [],
            'feature_count': 0,
            'features': []
        }

def analyze_multiple_websites(root_dir):
    """分析多个网站的个性化程度"""
    results = []
    
    # 首先收集所有需要分析的文件路径
    files_to_analyze = []
    
    print("正在收集网站文件...")
    websites = os.listdir(root_dir)
    for website in tqdm(websites, desc="扫描网站目录"):
        website_path = os.path.join(root_dir, website)
        if not os.path.isdir(website_path):
            continue
        
        for year in range(2009, 2025):  # 扩展年份范围到2025
            year_dir = os.path.join(website_path, str(year))
            if not os.path.exists(year_dir):
                continue
            
            # 匹配形如 *_index.html 的文件
            matched_files = glob.glob(os.path.join(year_dir, '*_index.html'))
            if matched_files:
                year_path = matched_files[0]  # 如果有多个，只取第一个
                files_to_analyze.append({
                    'website': website,
                    'year': year,
                    'file_path': year_path
                })
    
    # 显示总文件数
    total_files = len(files_to_analyze)
    print(f"共找到 {total_files} 个网站/年份组合需要分析")
    
    # 分析每个文件
    for i, file_info in enumerate(tqdm(files_to_analyze, desc="分析网站个性化", unit="网站")):
        # 显示当前进度
        print(f"\n[{i+1}/{total_files}] 正在分析: {file_info['website']} ({file_info['year']})")
        
        # 分析个性化程度
        personalization_results = analyze_website_personalization(file_info['file_path'], show_progress=True)
        
        # 添加结果
        results.append({
            'website': file_info['website'],
            'year': file_info['year'],
            'file_path': file_info['file_path'],
            'total_score': personalization_results['total_score'],
            'max_score': personalization_results['max_score'],
            'category_scores': personalization_results['category_scores'],
            'feature_categories': personalization_results['feature_categories'],
            'feature_count': personalization_results['feature_count'],
            'features': personalization_results['features']
        })
        
        # 显示当前文件的分析结果摘要
        print(f"个性化程度得分: {personalization_results['total_score']}/{personalization_results['max_score']}")
        print(f"个性化特征数: {personalization_results['feature_count']}")
        print(f"个性化特征类别: {', '.join(personalization_results['feature_categories'])}")
        
        # 短暂暂停，让用户有时间查看结果
        time.sleep(0.5)
    
    return results

def analyze_single_html(html_path):
    """分析单个HTML文件的个性化程度"""
    print("开始分析单个HTML文件的个性化程度...")
    
    # 使用进度条显示分析过程
    with tqdm(total=100, desc="总体进度") as pbar:
        pbar.update(10)  # 更新10%进度 - 开始分析
        
        results = analyze_website_personalization(html_path, show_progress=True)
        
        pbar.update(70)  # 更新到80%进度 - 分析完成
        
        # 打印统计结果
        print(f"\n分析文件: {html_path}")
        print(f"个性化程度得分: {results['total_score']}/{results['max_score']}")
        print(f"个性化特征数: {results['feature_count']}")
        
        print("\n各类别得分:")
        for category, score in results['category_scores'].items():
            category_name = {
                'user_identification': '用户识别与账户相关个性化',
                'content_recommendation': '内容推荐与个性化展示',
                'user_tracking': '用户行为跟踪与数据收集',
                'geo_localization': '地理位置与本地化个性化',
                'technical_implementation': '技术实现与API',
                'cart_transaction': '购物车与交易个性化'
            }.get(category, category)
            max_score = len(list(PersonalizationAnalyzer().personalization_patterns[category].keys()))
            print(f"- {category_name}: {score}/{max_score}")
        
        print("\n检测到的个性化特征:")
        for i, feature in enumerate(results['features']):
            category_name = {
                'user_identification': '用户识别与账户相关个性化',
                'content_recommendation': '内容推荐与个性化展示',
                'user_tracking': '用户行为跟踪与数据收集',
                'geo_localization': '地理位置与本地化个性化',
                'technical_implementation': '技术实现与API',
                'cart_transaction': '购物车与交易个性化'
            }.get(feature['category'], feature['category'])
            
            subcategory_name = feature['subcategory']
            evidence = feature['evidence']
            
            print(f"- [{i+1}/{results['feature_count']}] 类别: {category_name}, 子类别: {subcategory_name}")
            print(f"  证据: {evidence['source']} - {evidence.get('value', '')}")
        
        pbar.update(20)  # 更新到100%进度 - 完成
        
        return results

def generate_report(results, output_path):
    """生成分析报告"""
    if isinstance(results, list):
        # 多网站分析结果
        df = pd.DataFrame([{
            'website': r['website'],
            'year': r['year'],
            'total_score': r['total_score'],
            'max_score': r['max_score'],
            'score_percentage': round(r['total_score'] / r['max_score'] * 100, 2),
            'feature_count': r['feature_count'],
            'user_identification_score': r['category_scores'].get('user_identification', 0),
            'content_recommendation_score': r['category_scores'].get('content_recommendation', 0),
            'user_tracking_score': r['category_scores'].get('user_tracking', 0),
            'geo_localization_score': r['category_scores'].get('geo_localization', 0),
            'technical_implementation_score': r['category_scores'].get('technical_implementation', 0),
            'cart_transaction_score': r['category_scores'].get('cart_transaction', 0)
        } for r in results])
        
        # 保存为Excel文件
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Summary', index=False)
    else:
        # 单网站分析结果
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 网页个性化程度分析报告\n\n")
            f.write(f"## 分析文件: {results['file_path']}\n\n")
            f.write(f"总得分: {results['total_score']}/{results['max_score']} ({round(results['total_score'] / results['max_score'] * 100, 2)}%)\n\n")
            
            f.write("## 各类别得分\n\n")
            f.write("| 类别 | 得分 | 满分 |\n")
            f.write("|------|------|------|\n")
            
            category_names = {
                'user_identification': '用户识别与账户相关个性化',
                'content_recommendation': '内容推荐与个性化展示',
                'user_tracking': '用户行为跟踪与数据收集',
                'geo_localization': '地理位置与本地化个性化',
                'technical_implementation': '技术实现与API',
                'cart_transaction': '购物车与交易个性化'
            }
            
            for category, score in results['category_scores'].items():
                category_name = category_names.get(category, category)
                max_score = len(list(PersonalizationAnalyzer().personalization_patterns[category].keys()))
                f.write(f"| {category_name} | {score} | {max_score} |\n")
            
            f.write("\n## 检测到的个性化特征\n\n")
            
            if results['features']:
                for feature in results['features']:
                    category_name = category_names.get(feature['category'], feature['category'])
                    subcategory_name = feature['subcategory']
                    evidence = feature['evidence']
                    
                    f.write(f"### {category_name} - {subcategory_name}\n\n")
                    f.write(f"- 来源: {evidence['source']}\n")
                    f.write(f"- 值: {evidence.get('value', '')}\n")
                    if 'pattern' in evidence:
                        f.write(f"- 匹配模式: {evidence['pattern']}\n")
                    f.write("\n")
            else:
                f.write("未检测到个性化特征\n")
        
        print(f"分析报告已保存至: {output_path}")

def validate_output_path(output_path):
    if os.path.isdir(output_path):
        raise ValueError(
            f"无效的输出路径: '{output_path}' 是一个目录。请指定一个文件路径，例如 './outputs/report.xlsx'"
        )
    parent_dir = os.path.dirname(output_path) or "."
    if not os.path.exists(parent_dir):
        raise ValueError(
            f"输出路径中的目录 '{parent_dir}' 不存在，请先创建该目录或检查路径是否正确。"
        )

def main():
    """主程序入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='网页个性化程度分析工具')
    parser.add_argument('--file', type=str, help='单个HTML文件路径')
    parser.add_argument('--dir', type=str, help='包含多个网站的目录路径')
    parser.add_argument('--output', type=str, help='输出结果的文件路径')
    
    args = parser.parse_args()

    # 提前验证输出路径
    if args.output:
        try:
            validate_output_path(args.output)
        except ValueError as e:
            print(f"[错误] {e}")
            return
    
    if args.file:
        # 分析单个文件
        results = analyze_single_html(args.file)
        
        # 输出结果
        if args.output:
            generate_report(results, args.output)
        
    elif args.dir:
        # 分析多个网站
        results = analyze_multiple_websites(args.dir)
        
        # 输出结果
        if args.output:
            generate_report(results, args.output)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()