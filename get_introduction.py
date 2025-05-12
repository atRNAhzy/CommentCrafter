from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
)
def get_introduction():
    api_key = "替换成API-key"
    base_url = "https://api.deepseek.com"
    llm = ChatOpenAI(model="deepseek-chat", api_key=api_key, base_url=base_url)

    # 定义输出对象
    class Output(BaseModel):
        answer: str = Field(description="标语")
    # 根据Pydantic对象的定义，构造一个OutputParser
    parser = PydanticOutputParser(pydantic_object=Output)
    # Prompt 模版
    instruction = """
    你是一个幽默的作家和程序员。你写了一个程序，帮助老师用AI一次性给所有学生写期末评语，减轻老师的任务负担，让本来要写两天的评语可以在半个小时内解决。
    请写一个非常幽默的介绍放在开始界面。
    不要有“欢迎使用评语生成器”类似的表述，程序中已经有这样的标题了
    输出为python的单行字符串，内容要有四行（使用换行符\\n）,每行不超过50字,可以使用颜文字，emoji和表情包
    """
    template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                """任务指示:```{instruction}```
                输出格式:```{output_format}```"""
            )
        ]
    )
    # 生成 prompt
    prompt = template.format_messages(
        instruction=instruction,
        output_format=parser.get_format_instructions(),
    )
    # 调用模型
    model_output = llm.invoke(prompt)
    # 解析输出
    model_output_parser = parser.parse(model_output.content)
    return model_output_parser.dict()["answer"]
