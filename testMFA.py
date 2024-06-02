import requests

# 测试生成MFA代码
response = requests.get("http://127.0.0.1:8000/mfa/")
print(response.json())

# 测试验证MFA代码
client_mfa_code = "123456"  # 这是一个示例，请使用实际生成的MFA代码进行测试
response = requests.post(f"http://127.0.0.1:8000/verify-mfa/?client_mfa_code={client_mfa_code}")
print(response.json())
