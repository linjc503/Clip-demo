"""测试聊天功能脚本"""
import requests
import json

def test_chat():
    base_url = "http://localhost:8000"

    # 测试聊天功能
    print("=" * 60)
    print("测试聊天功能")
    print("=" * 60)

    try:
        # 发送测试消息
        test_message = "你好"
        print(f"\n发送消息: {test_message}")

        response = requests.post(
            f"{base_url}/chat",
            json={"message": test_message},
            timeout=30
        )

        print(f"\n状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")

        # 尝试解析 JSON
        try:
            result = response.json()
            print(f"\n响应 JSON: {json.dumps(result, indent=2, ensure_ascii=False)}")

            # 检查返回格式
            if "reply" in result:
                reply = result["reply"]
                print(f"\n✓ 回复字段存在")
                print(f"回复类型: {type(reply)}")
                print(f"回复内容: {reply}")

                if isinstance(reply, str) and len(reply) > 0:
                    print(f"\n✓ 回复格式正确: 字符串类型且非空")
                else:
                    print(f"\n✗ 回复格式错误: 不是字符串或为空")
            else:
                print(f"\n✗ 响应中缺少 'reply' 字段")
                print(f"可用字段: {list(result.keys())}")

        except json.JSONDecodeError:
            print(f"\n✗ 无法解析 JSON 响应")
            print(f"原始响应文本: {response.text[:500]}")

    except requests.exceptions.ConnectionError:
        print(f"\n✗ 无法连接到服务器 http://{base_url}")
        print("请确保服务器正在运行 (python app.py)")
    except requests.exceptions.Timeout:
        print(f"\n✗ 请求超时")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chat()
