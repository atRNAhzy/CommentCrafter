import re
import requests

def handle_http_error(status_code, error_message=None):
    error_messages = {
        400: ("格式错误", "请求体格式错误", "请根据错误信息提示修改请求体"),
        401: ("认证失败", "API key 错误，认证失败", "请检查您的 API key 是否正确或是否与模型相对应，如没有 API key，请先创建 API key"),
        402: ("余额不足", "账号余额不足", "请确认账户余额，并前往充值页面进行充值"),
        422: ("参数错误", "请求体参数错误", "请根据错误信息提示修改相关参数"),
        429: ("请求速率达到上限", "请求速率（TPM 或 RPM）达到上限", "请合理规划您的请求速率"),
        500: ("服务器故障", "服务器内部故障", "请等待后重试。若问题一直存在，请联系我们解决"),
        503: ("服务器繁忙", "服务器负载过高", "请稍后重试您的请求"),
    }

    if status_code in error_messages:
        error_type, cause, solution = error_messages[status_code]
        return f"\n错误类别：{error_type}\n原因：{cause}\n解决方法：{solution}"
    else:
        return f"未知错误，状态码: {status_code}"


def parse_error_message(error_str):
    # 使用正则表达式匹配错误代码和消息
    pattern = r"Error code: (\d+) - .*'message': '([^']*)'"
    match = re.search(pattern, error_str)

    if match:
        error_code = int(match.group(1))
        error_message = match.group(2)
        # 处理错误信息
        handle_http_error(error_code, error_message)
        # 检测到错误，返回 True
        return f"错误代码: {error_code},"+handle_http_error(error_code, error_message)
    else:
        # 没有检测到错误
        return False


def get_comment(key_word, example, additional_instructions, modelname,API_key):
    from langchain_openai import ChatOpenAI
    from langchain_core.pydantic_v1 import BaseModel, Field
    from langchain_core.output_parsers import PydanticOutputParser
    from langchain.prompts import (
        ChatPromptTemplate,
        HumanMessagePromptTemplate,
        SystemMessagePromptTemplate,
    )

    api_key = f"{API_key}"
    if modelname=="deepseek-chat":
        base_url="https://api.deepseek.com"
    elif modelname=="GPT-4o-mini":
        base_url="https://api.agicto.cn/v1"
        modelname="gpt-4o-mini"
    model = ChatOpenAI(model=modelname, api_key=api_key, base_url=base_url)

    class output(BaseModel):
        answer: str = Field(description="评语")

    parser = PydanticOutputParser(pydantic_object=output)

    instruction = """
    你是一名优秀的高中班主任，现在期末了，你需要根据关键词给学生写评语。
    """
    template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                """任务指示:```{instruction}```\n输出格式:```{output_format}```\n附加指令:```{additional_instructions}```\n例子：```{example}```"""
            ),
            HumanMessagePromptTemplate.from_template("{key_word}"),
        ]
    )

    prompt = template.format_messages(
        instruction=instruction,
        output_format=parser.get_format_instructions(),
        key_word=key_word,
        example=example,
        additional_instructions=additional_instructions
    )

    try:
        model_output = model.invoke(prompt)

        # 检查输出内容是否包含错误代码
        if "Error code" in model_output.content:
            return 0,f"检测到错误：{parse_error_message(model_output.content)}"

        # 如果没有错误，继续解析
        model_output_parser = parser.parse(model_output.content)

        return 1,model_output_parser.answer

    except requests.exceptions.RequestException as e:
        return 0,f"API request error: {str(e)}"

    except Exception as e:
        # 捕获其他潜在错误并检测是否有错误代码
        error_str = str(e)
        if "Error code" in error_str:
            return 0,parse_error_message(error_str)
        else:
            return 0,f"An unexpected error occurred: {error_str}"
