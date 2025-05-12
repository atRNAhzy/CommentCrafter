from PyQt5 import QtCore, QtGui, QtWidgets
from get_comment import get_comment
import os
import glob
import pandas as pd
import time
import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
import json

# 检查是否有且仅有一个excel文件
def checkFile(self):
    folder_path = 'input'
    excel_files = glob.glob(os.path.join(folder_path, '*.xls')) + glob.glob(os.path.join(folder_path, '*.xlsx'))
    if len(excel_files) == 1:
        df = pd.read_excel(excel_files[0])
        columns = df.columns.tolist()
        column_name1 = '关键词'
        column_name2 = '评语'
        if (column_name1 and column_name2) in columns:
            return 1
        else:
            self.ui.console.append("excel中缺少“关键词”列或者“评语”列")
            return 0
    else:
        self.ui.console.append("文件夹中没有或有多个 Excel 文件,或文件处于打开状态。")
        return 0
# 读取文件并填写评语
def get_keyword_and_fill_comment(self,example, requirement, API_key):
    folder_path = 'input'
    files = os.listdir(folder_path)
    excel_files = [file for file in files if file.endswith('.xlsx') or file.endswith('.xls')]
    file_name = os.path.join(folder_path, excel_files[0])
    df = pd.read_excel(file_name)
    ans = 0
    start_time = time.time()
    for index, row in df.iterrows():
        if pd.isna(df.at[index, '评语']):
            check,answer=get_comment(df.at[index, '关键词'], example, requirement, API_key)
            if check:
                df.at[index, '评语'] = answer
                self.ui.console.append(f"已填写{df.at[index, '姓名']}的评语")
                ans += 1
            else:
                self.ui.console.append(answer)
                return None
    end_time = time.time()
    with pd.ExcelWriter(file_name, mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, index=False)
    self.ui.console.append(f"总共处理{ans}个同学的评语，用时{end_time - start_time}s")

#窗口组件
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.requirements = ""
        self.examples = ""
        self.api_key = ""
        self.check_value = 0
        self.load_data()  # 初始化时加载txt文件中的内容

    # 保存功能

    def save(self):
        self.requirements = self.ui.requirement_input.toPlainText()
        self.examples = self.ui.example_input.toPlainText()
        self.api_key = self.ui.API_input.text()
        # 构建要保存的数据字典
        data = {
            "requirements": self.requirements,
            "examples": self.examples,
            "api_key": self.api_key
        }
        # 保存为 JSON 文件
        file_path = 'data/data.json'
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)  # ensure_ascii=False 确保中文字符正确保存
        self.ui.console.append("输入已保存")

    # 清除功能
    def clear(self):
        self.ui.requirement_input.clear()
        self.ui.example_input.clear()
        self.ui.API_input.clear()
        file_path = 'data/data.txt'
        with open(file_path, 'w', encoding='utf-8') as file:
            pass  # 不需要写入任何内容，文件已被清空
        self.ui.console.append("输入已清除")

    # 初始化时读取txt文件
    def load_data(self):
        file_path = 'data/data.json'

        if os.path.exists(file_path):
            # 打开 JSON 文件并读取数据
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # 将数据加载到相应的输入框中
            self.ui.requirement_input.setText(data.get("requirements", ""))
            self.ui.example_input.setText(data.get("examples", ""))
            self.ui.API_input.setText(data.get("api_key", ""))

            self.ui.console.append("已从文件加载数据")
        else:
            self.ui.console.append("文件不存在，无法加载数据")

    # 检查功能
    def check(self):
        if checkFile(self):
            if self.api_key != '':
                self.check_value = 1
            else:
                self.ui.console.append("缺少API-key")
        if self.check_value:
            self.ui.console.append("参数和操作文件完整，请点击开始按钮")
        else:
            self.ui.console.append("请按提示修改后重新点击检查按钮")

    # 开始按钮功能
    def start(self):
        if self.check_value:
            self.ui.console.append("开始运行程序")
            get_keyword_and_fill_comment(self,self.examples, self.requirements, self.api_key)
            self.check_value=0
        else:
            self.ui.console.append("请先点击检查按钮，保证所有参数完整")
class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(828, 1100)
        font = QtGui.QFont()
        font.setPointSize(16)  # 设置字体大小为16
        Form.setFont(font)

        # 标题标签
        self.welcome = QtWidgets.QLabel(Form)
        self.welcome.setGeometry(QtCore.QRect(10, 10, 800, 41))  # 改为顶部显示
        self.welcome.setObjectName("label")

        #要求
        self.requirement_text = QtWidgets.QLabel(Form)
        self.requirement_text.setGeometry(QtCore.QRect(10, 130, 800, 41))  # 下移避免重叠
        self.requirement_text.setObjectName("label_2")
        self.requirement_input = QtWidgets.QTextEdit(Form)
        self.requirement_input.setGeometry(QtCore.QRect(10, 180, 800, 160))  # 下移到适当位置
        self.requirement_input.setObjectName("textEdit")

        #例子
        self.example_text = QtWidgets.QLabel(Form)
        self.example_text.setGeometry(QtCore.QRect(10, 350, 800, 41))  # 下移以避免重叠
        self.example_text.setObjectName("label_3")
        self.example_prompt = QtWidgets.QLabel(Form)
        self.example_prompt.setGeometry(QtCore.QRect(10, 390, 800, 41))  # 下移到适当位置
        self.example_prompt.setObjectName("label_4")
        font_label_4 = QtGui.QFont()
        font_label_4.setPointSize(12)  # 设置文字大小为18
        self.example_prompt.setFont(font_label_4)
        self.example_input = QtWidgets.QTextEdit(Form)
        self.example_input.setGeometry(QtCore.QRect(10, 430, 800, 160))  # 下移到适当位置
        self.example_input.setObjectName("textEdit_2")

        #API
        self.API_text = QtWidgets.QLabel(Form)
        self.API_text.setGeometry(QtCore.QRect(10, 600, 800, 41))  # 下移到适当位置
        self.API_text.setObjectName("label_5")
        self.API_input = QtWidgets.QLineEdit(Form)
        self.API_input.setGeometry(QtCore.QRect(10, 650, 800, 41))  # 下移到适当位置
        self.API_input.setObjectName("lineEdit")

        # 文件提示
        self.file_text = QtWidgets.QLabel(Form)
        self.file_text.setGeometry(QtCore.QRect(10, 710, 800, 41))  # 下移到适当位置
        self.file_text.setObjectName("label_6")

        # 按钮部分
        #保存
        self.save_botton = QtWidgets.QPushButton(Form)
        self.save_botton.setGeometry(QtCore.QRect(480, 780, 75, 41))  # 第三个按钮
        self.save_botton.setObjectName("pushButton_3")
        #清除
        self.clear_botton = QtWidgets.QPushButton(Form)
        self.clear_botton.setGeometry(QtCore.QRect(560, 780, 75, 41))  # 清除按钮
        self.clear_botton.setObjectName("pushButton_4")
        #检查
        self.check_botton = QtWidgets.QPushButton(Form)
        self.check_botton.setGeometry(QtCore.QRect(640, 780, 75, 41))  # 第一个按钮
        self.check_botton.setObjectName("pushButton")
        #开始
        self.start_botton = QtWidgets.QPushButton(Form)
        self.start_botton.setGeometry(QtCore.QRect(720, 780, 75, 41))  # 第二个按钮
        self.start_botton.setObjectName("pushButton_2")

        # 第七个标签
        self.label_7 = QtWidgets.QLabel(Form)
        self.label_7.setGeometry(QtCore.QRect(10, 830, 800, 41))
        self.label_7.setObjectName("label_7")
        # 文本浏览框
        self.console = QtWidgets.QTextBrowser(Form)
        self.console.setGeometry(QtCore.QRect(10, 870, 800, 160))
        self.console.setObjectName("textBrowser")

        self.name = QtWidgets.QLabel(Form)
        self.name.setGeometry(QtCore.QRect(600, 1050, 800, 41))
        self.name.setObjectName("label_name")



        # 信号与槽连接
        self.retranslateUi(Form)
        self.check_botton.clicked.connect(Form.check)
        self.start_botton.clicked.connect(Form.start)
        self.save_botton.clicked.connect(Form.save)
        self.clear_botton.clicked.connect(Form.clear)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "评语生成器"))
        self.welcome.setText(_translate("Form", "欢迎使用评语生成器！"))
        self.name.setText(_translate("Form", "——hzy制作"))
        self.requirement_text.setText(_translate("Form", "请输入要求："))
        self.example_text.setText(_translate("Form", "请输入例子："))
        self.example_prompt.setText(_translate("Form", "（最多20个，例子越多，消耗的token越多、运行速度越慢、质量越好）"))
        self.check_botton.setText(_translate("Form", "检查"))
        self.start_botton.setText(_translate("Form", "开始"))
        self.save_botton.setText(_translate("Form", "保存"))
        self.clear_botton.setText(_translate("Form", "清除"))  # 清除按钮的文本
        self.API_text.setText('请 <a href="如何获取API-key.pdf">获取</a> 并输入API-key：')
        self.API_text.setOpenExternalLinks(False)  # 禁用自动打开链接
        self.API_text.linkActivated.connect(self.open_pdf)  # 绑定点击事件
        self.file_text.setText(_translate("Form", "请将包含评价和关键词的excel文件拖入input文件夹内！"))
        self.label_7.setText(_translate("Form", "进度显示："))
        self.console.setText(_translate("Form","这里将会显示提示词和进度条"))
    def open_pdf(self, link):
        # 使用系统默认的 pdf 打开方式打开文件
        pdf_path = os.path.join(os.getcwd(), 'data', link)  # 使用相对路径，确保文件位置正确
        QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
