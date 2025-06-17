import os
import json
from openai import OpenAI
from typing import List, Dict, Optional
import base64
from PIL import Image
import io
import logging

# 获取项目根目录（修改为正确的路径计算方式）
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CustomerServiceSystem:
    def __init__(self):
        # 使用OpenAI客户端连接阿里云API
        self.client = OpenAI(
            api_key="sk-69548e3e1b7a4c4ba4bcabd7af93b029",  # 您的API密钥
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 客服分类映射
        self.service_mapping = {
            "车辆认证": "林镇基",
            "crm": "李敬",
            "人脸/身份认证": "庄文哲",
            "前端": ["肖雪", "林敏"],
            "三方": "龙小强",
            "签约": "兰军",
            "扣款问题": "付志磊",
            "催收": "振琦",
            "用信、放款": "刘建明",
            "其他": "陈青松"
        }

    def encode_image_to_url(self, image_path: str) -> str:
        """将本地图片转换为可访问的URL格式（这里简化处理，实际应用中需要上传到云存储）"""
        # 实际应用中，您需要将图片上传到云存储并返回URL
        # 这里先返回本地路径，后续可以修改为实际的URL
        return f"file://{os.path.abspath(image_path)}"

    def classify_inquiry(self, text: str, image_path: Optional[str] = None) -> Dict:
        """分类用户咨询"""
        
        # 分类prompt
        classification_prompt = """
        你是一个专业的客服咨询分类助手。请仔细分析用户提供的文本和图片内容，将咨询内容准确分类到以下类别之一：

        1. 车辆认证 - 涉及车辆相关的认证问题、车辆信息验证、行驶证等
        2. crm - 客户关系管理相关问题、客户信息管理、客户数据等
        3. 人脸/身份认证 - 人脸识别、身份证验证、实名认证等身份相关问题
        4. 前端 - 网页显示问题、APP界面问题、操作流程问题等前端相关
        5. 三方 - 第三方服务集成、外部接口、合作伙伴相关问题
        6. 签约 - 合同签署、电子签名、协议相关问题
        7. 扣款问题 - 费用扣除、账单问题、支付相关问题
        8. 催收 - 逾期还款、催收流程、债务处理相关
        9. 用信、放款 - 信贷申请、放款流程、额度相关问题
        10. 其他 - 不属于以上任何类别的问题

        分析要求：
        - 仔细理解文本描述的具体问题
        - 如果有图片，结合图片内容进行综合判断
        - 优先根据问题的核心内容进行分类
        - 如果问题涉及多个方面，选择最主要的类别

        请只返回对应的类别名称，不要添加其他内容。
        """

        # 构建消息
        messages = [
            {
                "role": "system",
                "content": classification_prompt
            },
            {
                "role": "user",
                "content": []
            }
        ]

        # 添加图片（如果有）
        if image_path and os.path.exists(image_path):
            # 注意：实际使用中需要将图片上传到可公开访问的URL
            # 这里需要根据实际情况修改为真实的图片URL
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20241022/emyrja/dog_and_girl.jpeg"  # 示例URL，需要替换为实际的图片URL
                }
            })

        # 添加文本
        messages[1]["content"].append({
            "type": "text", 
            "text": f"用户咨询内容：{text}"
        })

        try:
            completion = self.client.chat.completions.create(
                model="qwen-omni-turbo",
                messages=messages,
                modalities=["text"],  # 只需要文本输出
                stream=True,
                stream_options={"include_usage": True}
            )

            # 收集流式输出
            category = ""
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    category += chunk.choices[0].delta.content
                elif hasattr(chunk, 'usage') and chunk.usage:
                    logger.info(f"API使用量: {chunk.usage}")

            category = category.strip()
            
            # 获取对应的客服
            service_person = self.service_mapping.get(category, "陈青松")
            if isinstance(service_person, list):
                service_person = service_person[0]  # 如果是列表，取第一个客服

            return {
                "category": category,
                "service_person": service_person,
                "original_text": text,
                "has_image": bool(image_path)
            }

        except Exception as e:
            logger.error(f"分类失败: {str(e)}")
            return {
                "error": str(e),
                "category": "其他",
                "service_person": "陈青松",
                "original_text": text,
                "has_image": bool(image_path)
            }

    def analyze_customer_features(self, text: str, image_paths: Optional[List[str]] = None) -> Dict:
        """分析客户特征并判断贷款资格"""
        prompt = """请严格遵循以下步骤分析输入的客户文本：

### 第一步：特征提取
从文本中精准提取以下9项特征（若无明确信息则标记为"未知"）：
1. **年龄** → 输出数字（如：35）
2. **国籍** → 默认中国（仅当明确提及其他国家时修改）
3. **月收入** → 转换为人民币数字（如：15000）
4. **职业** → 简化关键行业（如：IT工程师/个体商户）
5. **是否有车** → 是/否
6. **是否有公积金** → 是/否
7. **是否有寿险** → 是/否
8. **借款金额** → 转换为数字（单位：元）
9. **借款期限** → 转换为月数（如：12）

### 第二步：根据客户特征判断客户是否可以发放贷款，如果拒绝给出原因，不拒绝不用写原因

最后只需返回严格按照下面格式输出的组合结果： {'是否贷款':***,'拒绝原因':****,'放款机构':'小花钱包'};不需要返回其他内容"""

        # 准备输入内容
        content = text
        if image_paths:
            image_descriptions = self.process_images(image_paths)
            content += "\n" + image_descriptions

        try:
            completion = self.client.chat.completions.create(
                model="qwen-turbo",  # 使用qwen-turbo进行特征分析
                messages=[
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                stream=False  # 非流式输出便于解析JSON
            )
            
            result = completion.choices[0].message.content.strip()
            
            # 解析返回的JSON字符串
            try:
                result_dict = json.loads(result)
                return result_dict
            except json.JSONDecodeError:
                return {
                    "error": "返回结果格式错误",
                    "raw_result": result
                }
        except Exception as e:
            return {
                "error": str(e)
            }

    def process_images(self, image_paths: List[str]) -> str:
        """处理多张图片并返回描述"""
        image_descriptions = []
        for image_path in image_paths:
            # 这里可以添加图片分析的具体逻辑
            image_descriptions.append(f"图片内容描述: {image_path}")
        return "\n".join(image_descriptions)

    def test_classification(self, text: str, image_path: Optional[str] = None):
        """测试分类功能"""
        logger.info(f"测试分类功能")
        logger.info(f"输入文本: {text}")
        if image_path:
            logger.info(f"输入图片: {image_path}")
        
        result = self.classify_inquiry(text, image_path)
        
        logger.info(f"分类结果: {result['category']}")
        logger.info(f"分配客服: {result['service_person']}")
        logger.info("-" * 50)
        
        return result

def main():
    # 创建系统实例
    system = CustomerServiceSystem()
    
    # 测试分类功能
    test_cases = [
        {"text": "我的车辆认证一直通不过，请帮我看看", "image": None},
        {"text": "人脸识别失败了，身份证也上传了", "image": None},
        {"text": "网页打不开，APP也登录不了", "image": None},
        {"text": "为什么扣了我这么多钱？", "image": None},
        {"text": "我想申请贷款，需要什么条件？", "image": None}
    ]
    
    for i, test_case in enumerate(test_cases):
        logger.info(f"\n测试用例 {i+1}:")
        result = system.test_classification(test_case["text"], test_case["image"])

if __name__ == "__main__":
    main()