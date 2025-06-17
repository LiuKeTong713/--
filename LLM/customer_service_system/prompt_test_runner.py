import json
import os
from main import CustomerServiceSystem
from typing import Dict, List
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PromptTestRunner:
    def __init__(self):
        self.system = CustomerServiceSystem()
        self.test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
        self.test_cases_file = os.path.join(self.test_data_dir, "prompt_test_cases.json")
        
    def load_test_cases(self) -> List[Dict]:
        """加载测试用例"""
        try:
            with open(self.test_cases_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('test_cases', [])
        except Exception as e:
            logger.error(f"加载测试用例失败: {str(e)}")
            return []

    def verify_features(self, actual: Dict, expected: Dict) -> Dict:
        """验证特征提取结果"""
        results = {}
        for key in expected:
            if key not in actual:
                results[key] = {
                    "expected": expected[key],
                    "actual": "未提取",
                    "correct": False
                }
            else:
                results[key] = {
                    "expected": expected[key],
                    "actual": actual[key],
                    "correct": actual[key] == expected[key]
                }
        return results

    def verify_loan_result(self, actual: Dict, expected: Dict) -> Dict:
        """验证贷款分析结果"""
        results = {
            "是否贷款": {
                "expected": expected.get("是否贷款"),
                "actual": actual.get("是否贷款"),
                "correct": actual.get("是否贷款") == expected.get("是否贷款")
            },
            "放款机构": {
                "expected": expected.get("放款机构"),
                "actual": actual.get("放款机构"),
                "correct": actual.get("放款机构") == expected.get("放款机构")
            }
        }
        
        if "拒绝原因" in expected:
            results["拒绝原因"] = {
                "expected": expected.get("拒绝原因"),
                "actual": actual.get("拒绝原因"),
                "correct": actual.get("拒绝原因") == expected.get("拒绝原因")
            }
            
        return results

    def run_test_case(self, test_case: Dict) -> Dict:
        """运行单个测试用例"""
        text = test_case['text']
        
        # 运行分析
        result = self.system.analyze_customer_features(text)
        
        # 验证特征提取结果
        features_verification = self.verify_features(result, test_case['expected_features'])
        
        # 验证贷款分析结果
        loan_verification = self.verify_loan_result(result, test_case['expected_loan_result'])
        
        # 计算特征提取的准确率
        feature_correct_count = sum(1 for v in features_verification.values() if v['correct'])
        feature_total_count = len(features_verification)
        feature_accuracy = feature_correct_count / feature_total_count if feature_total_count > 0 else 0
        
        # 计算贷款分析的准确率
        loan_correct_count = sum(1 for v in loan_verification.values() if v['correct'])
        loan_total_count = len(loan_verification)
        loan_accuracy = loan_correct_count / loan_total_count if loan_total_count > 0 else 0
        
        return {
            'case_id': test_case['id'],
            'description': test_case['description'],
            'text': text,
            'features_verification': features_verification,
            'loan_verification': loan_verification,
            'feature_accuracy': feature_accuracy,
            'loan_accuracy': loan_accuracy,
            'success': feature_accuracy == 1.0 and loan_accuracy == 1.0
        }

    def run_all_tests(self):
        """运行所有测试用例"""
        test_cases = self.load_test_cases()
        results = []
        
        for test_case in test_cases:
            logger.info(f"\n运行测试用例: {test_case['id']} - {test_case['description']}")
            logger.info(f"输入文本: {test_case['text']}")
            
            result = self.run_test_case(test_case)
            results.append(result)
            
            # 打印特征提取结果
            logger.info("\n特征提取结果:")
            for feature, verification in result['features_verification'].items():
                status = "✓" if verification['correct'] else "✗"
                logger.info(f"{status} {feature}:")
                logger.info(f"  预期: {verification['expected']}")
                logger.info(f"  实际: {verification['actual']}")
            
            # 打印贷款分析结果
            logger.info("\n贷款分析结果:")
            for key, verification in result['loan_verification'].items():
                status = "✓" if verification['correct'] else "✗"
                logger.info(f"{status} {key}:")
                logger.info(f"  预期: {verification['expected']}")
                logger.info(f"  实际: {verification['actual']}")
            
            # 打印准确率
            logger.info(f"\n特征提取准确率: {result['feature_accuracy']*100:.2f}%")
            logger.info(f"贷款分析准确率: {result['loan_accuracy']*100:.2f}%")
            logger.info("-" * 50)
        
        # 统计结果
        total = len(results)
        passed = sum(1 for r in results if r['success'])
        avg_feature_accuracy = sum(r['feature_accuracy'] for r in results) / total
        avg_loan_accuracy = sum(r['loan_accuracy'] for r in results) / total
        
        logger.info(f"\n测试总结:")
        logger.info(f"总用例数: {total}")
        logger.info(f"完全通过数: {passed}")
        logger.info(f"完全通过率: {(passed/total)*100:.2f}%")
        logger.info(f"平均特征提取准确率: {avg_feature_accuracy*100:.2f}%")
        logger.info(f"平均贷款分析准确率: {avg_loan_accuracy*100:.2f}%")

def main():
    runner = PromptTestRunner()
    runner.run_all_tests()

if __name__ == "__main__":
    main() 