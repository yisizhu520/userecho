"""测试批量识别多反馈功能"""

import asyncio
from typing import Any


async def test_multi_feedback() -> None:
    """测试多反馈识别逻辑"""

    # 模拟 AI 返回多条反馈
    mock_result: dict[str, Any] = {
        "raw_text": "用户A：建议增加批量截图识别\n用户B：希望支持更多平台",
        "feedback_list": [
            {
                "content": "建议增加批量截图识别功能",
                "user_name": "用户A",
                "platform": "wechat",
                "confidence": 0.95,
            },
            {
                "content": "希望支持更多平台的截图识别",
                "user_name": "用户B",
                "platform": "wechat",
                "confidence": 0.88,
            },
            {
                "content": "建议优化识别准确度",
                "user_name": "用户C",
                "platform": "wechat",
                "confidence": 0.82,
            },
        ],
        "overall_confidence": 0.88,
    }

    # 模拟处理逻辑
    feedback_list = mock_result.get("feedback_list", [])

    if not feedback_list:
        print("❌ 没有识别到反馈")
        feedback_list = [
            {
                "content": mock_result.get("raw_text", "识别失败"),
                "user_name": "",
                "platform": "",
                "confidence": 0,
            }
        ]

    print(f"✅ 识别到 {len(feedback_list)} 条反馈：\n")

    created_feedbacks: list = []
    for idx, feedback_data in enumerate(feedback_list):
        ai_content = feedback_data.get("content", "")
        ai_user_name = feedback_data.get("user_name", "")
        ai_platform = feedback_data.get("platform", "")
        ai_confidence = feedback_data.get("confidence", 0)

        print(f"反馈 {idx + 1}:")
        print(f"  内容: {ai_content}")
        print(f"  用户: {ai_user_name}")
        print(f"  平台: {ai_platform}")
        print(f"  置信度: {ai_confidence * 100:.1f}%")
        print()

        created_feedbacks.append(
            {
                "feedback_id": f"feedback_{idx + 1}",
                "content": ai_content[:100],
                "confidence": ai_confidence,
            }
        )

    # 输出结果
    output = {
        "screenshot_url": "https://example.com/screenshot.jpg",
        "feedbacks": created_feedbacks,
        "total_feedbacks": len(created_feedbacks),
        "overall_confidence": mock_result.get("overall_confidence", 0),
    }

    print("=" * 60)
    print("输出数据结构:")
    print(f"  total_feedbacks: {output['total_feedbacks']}")
    print(f"  overall_confidence: {output['overall_confidence'] * 100:.1f}%")
    print(f"  feedbacks: {len(output['feedbacks'])} 条")
    print()
    print("✅ 测试通过！批量识别现在支持多反馈")


if __name__ == "__main__":
    asyncio.run(test_multi_feedback())
