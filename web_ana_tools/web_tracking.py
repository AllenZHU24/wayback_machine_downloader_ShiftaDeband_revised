import os
import pandas as pd
import re
import json
from bs4 import BeautifulSoup
from collections import defaultdict
import glob
from tqdm import tqdm
import time

class TrackingEventAnalyzer:
    def __init__(self):
        # 定义常见的埋点事件类型和对应的识别模式
        self.tracking_patterns = {
            # Google Analytics
            'Google Analytics': [
                r'google-analytics\.com/analytics\.js',
                r'gtag\(.*\)',
                r'ga\(.*\)',
                r'GoogleAnalyticsObject',
                r'google-analytics\.com/ga\.js',
                r'G-[A-Z0-9]{10,}',  # GA4 测量ID
                r'UA-[0-9]+-[0-9]+',  # Universal Analytics ID
            ],
            
            # Google Tag Manager
            'Google Tag Manager': [
                r'googletagmanager\.com/gtm\.js',
                r'dataLayer\.push\(',
                r'GTM-[A-Z0-9]+',
            ],
            
            # Facebook Pixel
            'Facebook Pixel': [
                r'connect\.facebook\.net/en_US/fbevents\.js',
                r'fbq\(',
                r'_fbq',
                r'facebook-jssdk',
                r'facebook\.com/tr\?',
            ],
            
            # 百度统计
            'Baidu Analytics': [
                r'hm\.baidu\.com/hm\.js',
                r'_hmt\.push\(',
            ],
            
            # 友盟统计
            'Umeng Analytics': [
                r'cnzz\.com/z_stat\.php',
                r'cnzz\.mmstat\.com',
            ],
            
            # 神策数据
            'Sensors Analytics': [
                r'sensorsdata\.min\.js',
                r'sa\.track\(',
                r'sensors\.track\(',
            ],
            
            # GrowingIO
            'GrowingIO': [
                r'assets\.giocdn\.com/gio',
                r'gio\(',
                r'growingio\.com',
            ],
            
            # 诸葛IO
            'Zhuge.io': [
                r'zgsdk\.zhugeio\.com',
                r'zhuge\.track',
            ],
            
            # 腾讯统计
            'Tencent Analytics': [
                r'tajs\.qq\.com',
                r'pingjs\.qq\.com',
            ],
            
            # 自定义埋点
            'Custom Events': [
                r'data-track',
                r'data-analytics',
                r'data-event',
                r'onclick="track',
                r'trackEvent\(',
                r'trackPageview\(',
                r'logEvent\(',
                r'sendEvent\(',
                r'pushEvent\(',
                r'trackAction\(',
            ],
            
            # 通用事件监听
            'Event Listeners': [
                r'addEventListener\([\'"]click[\'"]',
                r'addEventListener\([\'"]submit[\'"]',
                r'addEventListener\([\'"]change[\'"]',
            ],
            
            # 其他常见分析工具
            'Other Analytics': [
                r'hotjar\.com',
                r'clarity\.ms',
                r'matomo\.js',
                r'piwik\.js',
                r'adobe\.com/analytics',
                r'omniture',
                r'mixpanel',
                r'heap\.js',
                r'fullstory\.com',
                r'segment\.com',
                r'amplitude\.com',
            ],
        }
        
        # 定义常见的埋点属性
        self.tracking_attributes = [
            'data-track', 'data-analytics', 'data-event', 'data-ga', 'data-gtm',
            'data-click', 'data-impression', 'data-layer', 'data-tracking',
            'ga-event', 'gtm-event', 'track-id', 'track-type', 'track-name',
            'track-category', 'track-action', 'track-label', 'track-value',
        ]
        
        # 初始化结果存储
        self.reset_results()
    
    def reset_results(self):
        """重置分析结果"""
        self.event_types = set()  # 埋点事件种类
        self.event_count = 0  # 埋点总数
        self.events = []  # 具体埋点事件列表
        self.event_details = defaultdict(list)  # 按类型存储的详细事件
    
    def analyze_html(self, html_content, show_progress=False):
        """分析HTML内容中的埋点事件"""
        self.reset_results()
        
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 创建分析步骤列表
        analysis_steps = [
            ("分析脚本标签", lambda: self._analyze_scripts(soup)),
            ("分析内联事件处理器", lambda: self._analyze_inline_events(soup)),
            ("分析埋点属性", lambda: self._analyze_tracking_attributes(soup)),
            ("分析Meta标签", lambda: self._analyze_meta_tags(soup)),
            ("分析图片和iframe埋点", lambda: self._analyze_tracking_pixels(soup)),
            ("分析JSON-LD结构化数据", lambda: self._analyze_json_ld(soup))
        ]
        
        # 根据是否显示进度执行分析步骤
        if show_progress:
            for step_name, step_func in tqdm(analysis_steps, desc="HTML分析进度"):
                step_func()
        else:
            for _, step_func in analysis_steps:
                step_func()
        
        # 统计结果
        self.event_types = set(self.event_details.keys())
        self.event_count = sum(len(events) for events in self.event_details.values())
        
        # 整理所有事件列表
        for event_type, events in self.event_details.items():
            for event in events:
                self.events.append({
                    'type': event_type,
                    'details': event
                })
        
        return {
            'event_types_count': len(self.event_types),
            'event_types': list(self.event_types),
            'total_events': self.event_count,
            'events': self.events
        }
    
    def _analyze_scripts(self, soup):
        """分析脚本标签中的埋点"""
        scripts = soup.find_all('script')
        
        for script in scripts:
            # 检查脚本src属性
            if script.has_attr('src'):
                src = script['src']
                for event_type, patterns in self.tracking_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, src, re.IGNORECASE):
                            self.event_details[event_type].append({
                                'source': 'script_src',
                                'value': src,
                                'pattern': pattern
                            })
            
            # 检查内联脚本内容
            if script.string:
                script_content = script.string
                for event_type, patterns in self.tracking_patterns.items():
                    for pattern in patterns:
                        matches = re.findall(pattern, script_content, re.IGNORECASE)
                        for match in matches:
                            self.event_details[event_type].append({
                                'source': 'inline_script',
                                'value': match[:100] + ('...' if len(match) > 100 else ''),
                                'pattern': pattern
                            })
                
                # 特别检查dataLayer
                if 'dataLayer' in script_content:
                    datalayer_pushes = re.findall(r'dataLayer\.push\(\s*({[^}]+})', script_content)
                    for push in datalayer_pushes:
                        self.event_details['DataLayer Push'].append({
                            'source': 'datalayer_push',
                            'value': push[:100] + ('...' if len(push) > 100 else '')
                        })
    
    def _analyze_inline_events(self, soup):
        """分析内联事件处理器"""
        # 常见的内联事件属性
        inline_events = ['onclick', 'onchange', 'onsubmit', 'onload', 'onunload', 
                         'onmouseover', 'onmouseout', 'onfocus', 'onblur']
        
        for event_attr in inline_events:
            elements = soup.find_all(attrs={event_attr: True})
            for element in elements:
                attr_value = element[event_attr]
                # 检查是否包含跟踪相关代码
                tracking_related = False
                for event_type, patterns in self.tracking_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, attr_value, re.IGNORECASE):
                            tracking_related = True
                            self.event_details[event_type].append({
                                'source': f'inline_{event_attr}',
                                'element': element.name,
                                'value': attr_value[:100] + ('...' if len(attr_value) > 100 else '')
                            })
                
                # 如果没有匹配到特定模式但看起来像跟踪代码
                if not tracking_related and any(keyword in attr_value.lower() for keyword in 
                                              ['track', 'event', 'analytics', 'log', 'send', 'push']):
                    self.event_details['Custom Events'].append({
                        'source': f'inline_{event_attr}',
                        'element': element.name,
                        'value': attr_value[:100] + ('...' if len(attr_value) > 100 else '')
                    })
    
    def _analyze_tracking_attributes(self, soup):
        """分析埋点属性"""
        for attr in self.tracking_attributes:
            elements = soup.find_all(attrs={attr: True})
            for element in elements:
                self.event_details['Attribute Tracking'].append({
                    'source': 'tracking_attribute',
                    'element': element.name,
                    'attribute': attr,
                    'value': element[attr]
                })
    
    def _analyze_meta_tags(self, soup):
        """分析Meta标签中的埋点信息"""
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            # 检查与跟踪相关的meta标签
            if meta.has_attr('name') and any(keyword in meta['name'].lower() for keyword in 
                                           ['google', 'facebook', 'fb', 'twitter', 'analytics', 
                                            'verification', 'track', 'pixel']):
                self.event_details['Meta Tag Tracking'].append({
                    'source': 'meta_tag',
                    'name': meta['name'],
                    'content': meta.get('content', '')
                })
    
    def _analyze_tracking_pixels(self, soup):
        """分析图片和iframe埋点"""
        # 检查跟踪像素
        img_pixels = soup.find_all('img', width="1", height="1")
        img_pixels.extend(soup.find_all('img', width="0", height="0"))
        
        for pixel in img_pixels:
            if pixel.has_attr('src'):
                self.event_details['Tracking Pixel'].append({
                    'source': 'img_pixel',
                    'src': pixel['src']
                })
        
        # 检查跟踪iframe
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            if iframe.has_attr('src'):
                src = iframe['src']
                for event_type, patterns in self.tracking_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, src, re.IGNORECASE):
                            self.event_details[event_type].append({
                                'source': 'iframe',
                                'src': src
                            })
    
    def _analyze_json_ld(self, soup):
        """分析JSON-LD结构化数据中的埋点"""
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            if script.string:
                try:
                    data = json.loads(script.string)
                    # 检查是否包含跟踪相关字段
                    if isinstance(data, dict) and any(key in data for key in 
                                                    ['tracking', 'analytics', 'event', 'gtm', 'ga']):
                        self.event_details['JSON-LD Tracking'].append({
                            'source': 'json_ld',
                            'data': str(data)[:100] + ('...' if len(str(data)) > 100 else '')
                        })
                except:
                    pass

def analyze_website_tracking(html_path, show_progress=False):
    """分析单个网站的埋点事件"""
    try:
        print(f"正在读取文件: {html_path}")
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as file:
            html_content = file.read()
        
        print(f"开始分析文件: {html_path}")
        analyzer = TrackingEventAnalyzer()
        results = analyzer.analyze_html(html_content, show_progress)
        
        return {
            'file_path': html_path,
            'event_types_count': results['event_types_count'],
            'event_types': results['event_types'],
            'total_events': results['total_events'],
            'events': results['events']
        }
    except Exception as e:
        print(f"Error analyzing {html_path}: {e}")
        return {
            'file_path': html_path,
            'error': str(e),
            'event_types_count': 0,
            'event_types': [],
            'total_events': 0,
            'events': []
        }

def analyze_multiple_websites(root_dir):
    """分析多个网站的埋点事件"""
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
    for i, file_info in enumerate(tqdm(files_to_analyze, desc="分析网站埋点", unit="网站")):
        # 显示当前进度
        print(f"\n[{i+1}/{total_files}] 正在分析: {file_info['website']} ({file_info['year']})")
        
        # 分析埋点事件
        tracking_results = analyze_website_tracking(file_info['file_path'], show_progress=True)
        
        # 添加结果
        results.append({
            'website': file_info['website'],
            'year': file_info['year'],
            'file_path': file_info['file_path'],
            'event_types_count': tracking_results['event_types_count'],
            'event_types': tracking_results['event_types'],
            'total_events': tracking_results['total_events'],
            'events': tracking_results['events']
        })
        
        # 显示当前文件的分析结果摘要
        print(f"埋点事件种类数: {tracking_results['event_types_count']}")
        print(f"埋点总数: {tracking_results['total_events']}")
        print(f"埋点事件类型: {', '.join(tracking_results['event_types'])}")
        
        # 短暂暂停，让用户有时间查看结果
        time.sleep(0.5)
    
    return results

def analyze_single_html(html_path):
    """分析单个HTML文件的埋点事件"""
    print("开始分析单个HTML文件...")
    
    # 使用进度条显示分析过程
    with tqdm(total=100, desc="总体进度") as pbar:
        pbar.update(10)  # 更新10%进度 - 开始分析
        
        results = analyze_website_tracking(html_path, show_progress=True)
        
        pbar.update(70)  # 更新到80%进度 - 分析完成
        
        # 打印统计结果
        print(f"\n分析文件: {html_path}")
        print(f"埋点事件种类数: {results['event_types_count']}")
        print(f"埋点总数: {results['total_events']}")
        print("\n埋点事件类型:")
        for event_type in results['event_types']:
            print(f"- {event_type}")
        
        print("\n具体埋点事件:")
        event_count = len(results['events'])
        for i, event in enumerate(results['events']):
            print(f"- [{i+1}/{event_count}] 类型: {event['type']}")
            for key, value in event['details'].items():
                if key != 'pattern':  # 不显示匹配模式
                    print(f"  {key}: {value}")
            print()
        
        # 保存结果到JSON文件
        output_path = html_path + "_tracking_analysis.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"详细分析结果已保存到: {output_path}")
        
        pbar.update(20)  # 更新到100%进度 - 全部完成
    
    return results

def export_to_excel(results, output_file='web_tracking_analysis.xlsx'):
    """将分析结果导出到Excel"""
    print("\n正在导出分析结果到Excel...")
    
    with tqdm(total=100, desc="导出进度") as pbar:
        # 准备基本数据
        pbar.update(20)
        basic_data = []
        for result in results:
            row = {
                'website': result.get('website', 'N/A'),
                'year': result.get('year', 'N/A'),
                'file_path': result.get('file_path', 'N/A'),
                'event_types_count': result['event_types_count'],
                'total_events': result['total_events'],
                'event_types': ', '.join(result['event_types'])
            }
            basic_data.append(row)
        
        # 创建基本数据DataFrame
        pbar.update(20)
        df_basic = pd.DataFrame(basic_data)
        
        # 创建详细事件数据
        pbar.update(20)
        detailed_data = []
        for result in results:
            website = result.get('website', 'N/A')
            year = result.get('year', 'N/A')
            file_path = result.get('file_path', 'N/A')
            
            for event in result['events']:
                event_type = event['type']
                details = event['details']
                
                row = {
                    'website': website,
                    'year': year,
                    'file_path': file_path,
                    'event_type': event_type,
                    'source': details.get('source', 'N/A'),
                    'element': details.get('element', 'N/A'),
                    'value': details.get('value', details.get('src', 'N/A'))
                }
                detailed_data.append(row)
        
        # 创建详细事件DataFrame
        pbar.update(20)
        df_detailed = pd.DataFrame(detailed_data) if detailed_data else pd.DataFrame()
        
        # 保存到Excel，每个表格一个sheet
        pbar.update(10)
        with pd.ExcelWriter(output_file) as writer:
            df_basic.to_excel(writer, sheet_name='Summary', index=False)
            if not df_detailed.empty:
                df_detailed.to_excel(writer, sheet_name='Detailed Events', index=False)
        
        pbar.update(10)
    
    print(f"分析结果已保存到Excel文件: {output_file}")

def count_files_in_directory(directory):
    """统计目录中的HTML文件数量"""
    count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                count += 1
    return count

# 主程序
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='分析网页中的埋点事件')
    parser.add_argument('--file', type=str, help='单个HTML文件路径')
    parser.add_argument('--dir', type=str, help='网站目录路径')
    parser.add_argument('--output', type=str, default='web_tracking_analysis.xlsx', help='输出Excel文件路径')
    
    args = parser.parse_args()
    
    # 显示启动信息
    print("=" * 60)
    print("网页埋点事件分析工具")
    print("=" * 60)
    
    start_time = time.time()
    
    if args.file:
        # 分析单个HTML文件
        print(f"准备分析单个HTML文件: {args.file}")
        results = [analyze_single_html(args.file)]
        export_to_excel(results, args.output)
    elif args.dir:
        # 分析目录中的多个网站
        print(f"准备分析目录: {args.dir}")
        
        # 统计文件数量
        file_count = count_files_in_directory(args.dir)
        print(f"目录中共有 {file_count} 个HTML文件")
        
        results = analyze_multiple_websites(args.dir)
        export_to_excel(results, args.output)
        print(f"共分析了 {len(results)} 个网站/年份组合")
    else:
        print("请提供 --file 或 --dir 参数")
    
    # 显示总耗时
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"\n分析完成! 总耗时: {elapsed_time:.2f} 秒")
    print("=" * 60)