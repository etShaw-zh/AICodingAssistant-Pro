import requests
from src.module.config import readConfig

class APIError(Exception):
    """API错误的自定义异常类"""
    def __init__(self, status_code, error_type, message):
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        super().__init__(self.message)

class AiHubMixAPI:
    BASE_URL = "https://api.aihubmix.com/v1"

    # HTTP状态码及其对应的错误描述
    ERROR_MESSAGES = {
        400: "请求格式错误，不能被服务器理解。通常意味着客户端错误。",
        401: "API密钥验证未通过。你需要验证你的API密钥是否正确，其他原因",
        403: "一般是权限不足。",
        404: "请求的资源未找到。你可能正在尝试访问一个不存在的端点。",
        413: "请求体太大。你可能需要减小你的请求体容量。",
        429: "由于频繁的请求超过限制，你已经超过了你的速率限制。",
        500: "服务器内部的错误。这可能是OpenAI服务器的问题，不是你的问题。",
        503: "服务器暂时不可用。这可能是由于OpenAI正在进行维护或者服务器过载。"
    }

    def __init__(self):
        self.api_key = readConfig().get("APIkey", "api_key")
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

    def _handle_error_response(self, response):
        """处理API错误响应"""
        status_code = response.status_code
        try:
            error_data = response.json().get('error', {})
            error_type = error_data.get('type', 'unknown_error')
            error_message = error_data.get('message', '未知错误')
        except ValueError:
            error_type = 'parse_error'
            error_message = '无法解析错误响应'

        # 获取详细的错误描述
        error_description = self.ERROR_MESSAGES.get(status_code, '未知错误')
        
        # 组合完整的错误信息
        full_error_message = f"HTTP {status_code}: {error_description}\n具体错误: {error_message}"
        
        raise APIError(status_code, error_type, full_error_message)

    def _make_request(self, method, endpoint, **kwargs):
        """统一的请求处理方法"""
        try:
            url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
            response = requests.request(method, url, headers=self.headers, **kwargs)
            
            if response.status_code != 200:
                self._handle_error_response(response)
                
            return response.json()
        except requests.exceptions.RequestException as e:
            raise APIError(0, 'network_error', f"网络请求错误: {str(e)}")
        except Exception as e:
            raise APIError(0, 'unknown_error', f"未知错误: {str(e)}")

    def get_available_models(self):
        """获取当前API Key支持的所有模型列表"""
        try:
            response = self._make_request('GET', '/models')
            models = response.get('data', [])
            return [model['id'] for model in models if model.get('available', True)]
        except APIError as e:
            print(f"获取模型列表失败: {e.message}")
            return []

    def get_model_info(self, model_id):
        """获取特定模型的详细信息"""
        try:
            response = self._make_request('GET', f'/models/{model_id}')
            return response.get('data', {})
        except APIError as e:
            print(f"获取模型信息失败: {e.message}")
            return {}

    def validate_api_key(self):
        """验证API Key是否有效"""
        try:
            self._make_request('GET', '/models')
            return True
        except APIError:
            return False

    def chat_completion(self, model, messages, temperature=0.7, max_tokens=None):
        """统一的聊天完成接口"""
        try:
            data = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            if max_tokens is not None:
                data["max_tokens"] = max_tokens

            return self._make_request('POST', '/chat/completions', json=data)
        except APIError as e:
            return {"error": e.message}
