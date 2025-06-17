import os
import base64
from openai import OpenAI

class CustomerServiceSystem:
    def __init__(self):
        self.client = OpenAI(
            # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
            api_key="sk-69548e3e1b7a4c4ba4bcabd7af93b029",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        # 获取当前脚本文件所在的目录
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 客服分配映射
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

    def encode_image_to_base64(self, image_path: str) -> str:
        """将本地图片转换为base64编码"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def classify_text_only(self, text: str):
        model = "text-only-model"
        return self._classify_inquiry(model, text=text)

    def classify_image_only(self, image_path: str):
        model = "image-only-model"
        return self._classify_inquiry(model, image_path=image_path)

    def classify_image_and_text(self, image_path: str, text: str):
        model = "qwen-vl-plus"
        return self._classify_inquiry(model, image_path=image_path, text=text)

    def _classify_inquiry(self, model: str, image_path: str = None, text: str = None):
        prompt = """你是一个专业的客服咨询分类助手。请仔细分析用户提供的文本内容，将咨询内容准确分类到以下类别之一：\n\n1. 车辆认证\n   - 描述：涉及车辆相关的认证、验证问题，包括：车辆信息验证、行驶证审核、车辆资料上传、保单与车主信息匹配、车险相关认证等所有与车辆证明文件相关的问题\n   - 关键词：车辆、认证、验证、行驶证、车辆信息、保单、车主、车险、车辆资料、匹配、审核。\n\n2. crm\n   - 描述：客户关系管理相关问题、客户信息管理、客户数据查询、账户管理等\n   - 关键词：客户关系、客户信息、客户数据、账户管理、CRM、客户管理、数据查询。\n\n3. 人脸/身份认证\n   - 描述：人脸识别、身份证验证、实名认证、人证比对等身份相关问题\n   - 关键词：人脸识别、身份证、实名认证、人证比对、身份验证、身份认证。\n\n4. 前端\n   - 描述：网页显示问题、APP界面问题、操作流程问题、页面加载异常等前端相关\n   - 关键词：网页显示、APP界面、操作流程、页面加载、界面问题、页面不对、加载失败、跳转、点击、按钮、布局、显示异常。\n   - 注意：如果问题涉及"页面不对"或"界面问题"，优先考虑为前端问题。\n\n5. 三方\n   - 描述：第三方服务集成、外部接口问题、合作伙伴服务、第三方支付等\n   - 关键词：第三方、外部接口、合作伙伴、第三方支付、服务集成。\n\n6. 签约\n   - 描述：合同签署、电子签名、协议相关问题、签约流程等\n   - 关键词：合同、签署、电子签名、协议、签约流程。\n\n7. 扣款问题\n   - 描述：费用扣除、账单问题、支付异常、扣费争议等相关问题\n   - 关键词：费用、扣款、账单、支付异常、扣费争议。\n\n8. 催收\n   - 描述：逾期还款、催收流程、债务处理、还款提醒等相关\n   - 关键词：逾期、催收、债务、还款提醒、还款。\n\n9. 用信、放款\n   - 描述：信贷申请、放款流程、借款额度申请等纯粹的借贷业务问题\n   - 关键词：信贷、放款、借款、额度申请、借贷业务。\n\n10. 其他\n   - 描述：不属于以上任何类别的问题\n\n分析要求：\n- 识别文本和图片中的关键字，并分析关键字出现的次数频率，适当根据关键字来对问题分类\n- 当用户提到"保单名字和车主一致"、"车辆认证"、"行驶证"等车辆相关认证时，应分类为车辆认证\n- "提额"如果是因为车辆认证问题导致的，应归类为车辆认证而非用信放款\n- 仔细理解问题的根本原因，而不是表面的症状\n- 如果有图片，结合图片内容进行综合判断\n- 优先根据问题的核心内容进行分类\n- 如果问题涉及多个方面，选择最主要的类别\n\n请只返回对应的类别名称（如：车辆认证），不要添加其他内容。"""

        # 构建消息
        messages = [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": []
            }
        ]

        # 如果有图片，添加图片内容
        if image_path:
            # 构建基于脚本文件位置的绝对路径
            full_image_path = os.path.join(self.script_dir, "image", os.path.basename(image_path))
            
            if os.path.exists(full_image_path):
                try:
                    base64_image = self.encode_image_to_base64(full_image_path)
                    # 获取图片格式
                    image_format = full_image_path.split('.')[-1].lower()
                    if image_format == 'jpg':
                        image_format = 'jpeg'
                    
                    messages[1]["content"].append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{image_format};base64,{base64_image}"
                        }
                    })
                    print(f"成功加载图片: {full_image_path}")
                except Exception as e:
                    print(f"图片处理失败 {full_image_path}: {e}")
            else:
                print(f"未找到图片文件: {full_image_path}")

        # 添加文本内容（如果有文本）
        if text and text.strip():
            messages[1]["content"].append({
                "type": "text",
                "text": text
            })
        else:
            # 如果没有文本，添加一个默认提示
            messages[1]["content"].append({
                "type": "text",
                "text": "请分析图片内容进行分类"
            })

        try:
            completion = self.client.chat.completions.create(
                model=model,  # 使用选择的模型
                messages=messages,
                stream=False
            )

            # 获取分类结果
            category = completion.choices[0].message.content.strip()
            
            # 获取对应的客服
            service_person = self.service_mapping.get(category, "陈青松")
            if isinstance(service_person, list):
                service_person = service_person[0]  # 如果是列表，取第一个客服

            result = {
                "category": category,
                "service_person": service_person,
                "original_text": text,
                "has_image": bool(image_path and os.path.exists(full_image_path))
            }
            
            print(f"分类结果: {result['category']}")
            print(f"分配客服: {result['service_person']}")
            
            return result
            
        except Exception as e:
            print(f"API调用失败: {e}")
            # 如果API调用失败，只有在有明确文本内容时才基于文本分类，否则归为其他
            if text and text.strip():
                text_lower = text.lower()
                if "页面不对" in text or "界面问题" in text or "加载失败" in text:
                    category = "前端"
                elif "车辆" in text or "认证" in text or "保单" in text or "行驶证" in text:
                    category = "车辆认证"
                elif "人脸" in text or "身份" in text:
                    category = "人脸/身份认证"
                elif "扣款" in text or "费用" in text:
                    category = "扣款问题"
                elif "贷款" in text or "放款" in text or "用信" in text:
                    category = "用信、放款"
                elif "crm" in text_lower:
                    category = "crm"
                elif "前端" in text or "页面" in text or "网页" in text or "app" in text_lower:
                    category = "前端"
                elif "签约" in text or "合同" in text:
                    category = "签约"
                elif "催收" in text or "逾期" in text:
                    category = "催收"
                elif "三方" in text or "第三方" in text:
                    category = "三方"
                else:
                    category = "其他"
            else:
                # 如果只有图片没有文字，或API调用失败且无法处理图片，归为其他
                category = "其他"
                
            service_person = self.service_mapping.get(category, "陈青松")
            if isinstance(service_person, list):
                service_person = service_person[0]
                
            return {
                "category": category,
                "service_person": service_person,
                "original_text": text if text else "仅图片内容",
                "has_image": bool(image_path and os.path.exists(full_image_path))
            }

    def classify_inquiry(self, image_path: str = None, text: str = None):
        if image_path and text:
            return self.classify_image_and_text(image_path, text)
        elif image_path:
            return self.classify_image_only(image_path)
        elif text:
            return self.classify_text_only(text)
        else:
            raise ValueError("必须提供图片或文字中的至少一个")

# 示例调用
if __name__ == "__main__":
    system = CustomerServiceSystem()
    
    # 测试用例 - 用户输入的图片和文字
    test_cases = [
        {
            "image_path": "image/lzj1.jpeg",
            "text": "客户ID:20220613023178243749 用户姓名:许颖颖 提额一直提示保单名字和车主一致的",
            "model": "image_and_text"  # 可选值："text_only", "image_only", "image_and_text"
        },
        {
            "image_path": "image/lzj2.png",
            "text": "客户ID:20200118023161007143 客户咨询车辆认证提额 麻烦核实看下是否有提额成功",
            "model": "image_and_text"
        },
        {
            "image_path": "image/lzj3.png",
            "text": "客户ID:20220831023179631450 用户反馈提交是一直提示确认保单信息一致，信息都是对的",
            "model": "image_and_text"
        },
        {
            "image_path": "image/lj1.png",
            "text": "crm 黑灰产识别一直生产不了信息",
            "model": "image_and_text"
        },
        {
            "image_path": "image/zwz1.png",
            "text": "上传身份证信息显示如图",
            "model": "image_and_text"
        },
        {
            "image_path": "image/zwz2.png",
            "text": "客户ID:20230530023184621150 这个客户月初就咨询的问题到现在还是没处理呢，辛苦查看一下什么原因，APP小程序公众号都是头像验证码失败",
            "model": "image_and_text"
        },
        {
            "image_path": None,
            "text": "客户ID:20190521023152787534 用户反馈有3000借款额度，但无法申请，一提交借款申请就返回到首页",
            "model": "text_only"
        },
        {
            "image_path": "image/xx2.png",
            "text": "客户ID:20161214000005056204，客户表示身份证要过期，到APP提交更新的时候一直提示要对齐边框，但是页面不对",
            "model": "image_and_text"
        },
        {
            "image_path": "image/lxq1.png",
            "text": "客户13810728063 表示富龙小贷没有6.4待还账单也没有逾期需还款账单，但收到我司扣费失败短信，要求核实",
            "model": "image_only"
        },
    ]
    
    print("=== 客服咨询分类系统测试 ===\n")
    
    for i, case in enumerate(test_cases, 1):
        print(f"测试用例 {i}:")
        print(f"用户文字: {case['text']}")
        if case['image_path']:
            print(f"用户图片: {case['image_path']}")
        else:
            print("用户图片: 无")
        
        # 根据指定的模型调用相应的方法
        model_type = case.get("model", "image_and_text")
        if model_type == "text_only":
            result = system.classify_text_only(case['text'])
        elif model_type == "image_only":
            result = system.classify_image_only(case['image_path'])
        else:
            result = system.classify_image_and_text(case['image_path'], case['text'])
        
        print(f"→ 转接给: {result['service_person']}\n")
        print("-" * 50)