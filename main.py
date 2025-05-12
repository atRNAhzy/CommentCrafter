import pandas as pd
import time
from
#调用大模型根据关键词写评语
def get_comment(key_word,example,additional_instructions):
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI
    from langchain_core.pydantic_v1 import BaseModel, Field
    from langchain_core.output_parsers import PydanticOutputParser
    from langchain.prompts import (
        ChatPromptTemplate,
        HumanMessagePromptTemplate,
        SystemMessagePromptTemplate,
    )
    # 加载.env到环境变量
    load_dotenv()
    # 选择模型
    model = ChatOpenAI(model="deepseek-chat")

    # 定义输出对象
    class output(BaseModel):
        answer: str = Field(description="评语")

    # 根据Pydantic对象的定义，构造一个OutputParser
    parser = PydanticOutputParser(pydantic_object=output)
    instruction = """
    你是一名优秀的高中班主任，现在期末了，你需要根据关键词给学生写评语。
    """
    template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                """任务指示:```{instruction}```
                输出格式:```{output_format}```
                附加指令:```{additional_instructions}```
                例子：```{example}```"""),
            HumanMessagePromptTemplate.from_template("{key_word}"),
        ]
    )

    # 生成prompt
    prompt = template.format_messages(
        instruction=instruction,
        output_format=parser.get_format_instructions(),
        key_word=key_word,
        example=example,
        additional_instructions=additional_instructions
    )
    # 调用模型
    model_output = model.invoke(prompt)
    # 解析输出
    model_output_parser = parser.parse(model_output.content)

    return model_output_parser.answer

#控制面板信息处理
def control_panel_processing():
    # 读取Excel文件
    file_path = '控制面板.xlsx'  # 替换为你的Excel文件路径
    df = pd.read_excel(file_path)
    # 获取第一列的要求列表（从第二行开始）
    requirements = df.iloc[0:, 0].dropna().tolist()
    # 输出结果
    print("要求列表：", requirements)

#处理example,只获取前20个例子
def get_exanple():
    import os
    # 存储所有文件中的“评语”列
    example = []
    # 获取当前工作目录下的 'example' 文件夹路径
    folder_path = os.path.join(os.getcwd(), 'example')
    # 遍历文件夹中的所有 Excel 文件
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.xlsx'):  # 检查是否为 Excel 文件
            file_path = os.path.join(folder_path, file_name)
            # 读取 Excel 文件
            df = pd.read_excel(file_path)
            # 如果“评语”列存在，则添加到列表中
            if '评语' in df.columns:
                example.extend(df['评语'].dropna().tolist())  # 去除空值，并将其加入列表
    # 打印读取的评语
    for item in example:
        print(item)
    return example[:20]


#主函数
def main():
    file_name = 'students.xlsx'
    # 读取 Excel 文件
    df = pd.read_excel(file_name)
    # 遍历第三列，如果单元格为空，则填充
    ans = 0
    control_panel_processing()
    start_time = time.time()
    """for index, row in df.iterrows():
        if pd.isna(df.at[index, '评语']):
            df.at[index, '评语'] = get_comment(df.at[index, '关键词']," "," ")
            print(f"已填写{df.at[index, '姓名']}的评语")
            ans+=1"""
    end_time = time.time()

    # 保存修改后的 DataFrame 到新的 Excel 文件
    df.to_excel('students.xlsx', index=False)
    # 输出结果
    print(f"总共处理{ans}个同学的评语，用时{end_time - start_time}s")

api_key=" "
import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget
from GUI import Ui_Form  # 假设你把上面的UI代码保存为your_ui_file.py
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()  # 实例化你的 UI 类
        self.ui.setupUi(self)  # 调用 setupUi 方法，传入当前窗口实例
        self.show()  # 显示窗口

    # 在这里添加按钮功能，例如：
    def save(self):
        print("Save button clicked")
        # 读取 QLineEdit 的内容
        api_key = self.lineEdit.text()

    def check(self):
        print("Check button clicked")

    def start(self):
        print("Start button clicked")
        print(api_key)


if __name__ == "__main__":
    app = QApplication(sys.argv)  # 创建应用程序实例
    window = MainWindow()  # 创建主窗口实例
    sys.exit(app.exec_())  # 进入主事件循环
