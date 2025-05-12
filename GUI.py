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
from PyQt5.QtCore import QThread, pyqtSignal
from get_introduction import get_introduction

# 检查是否有且仅有一个excel文件# 检查是否有且仅有一个excel文件
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


#窗口组件
#多线程调用函数填写评语
class Worker(QThread):
    # 自定义信号，传递要显示的文本
    update_text = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, example, requirement,modelname ,API_key, parent=None):
        super().__init__(parent)
        self.example = example
        self.requirement = requirement
        self.API_key = API_key
        self.model=modelname

    def run(self):
        folder_path = 'input'
        files = os.listdir(folder_path)
        excel_files = [file for file in files if file.endswith('.xlsx') or file.endswith('.xls')]
        file_name = os.path.join(folder_path, excel_files[0])
        df = pd.read_excel(file_name)
        ans = 0
        start_time = time.time()
        for index, row in df.iterrows():
            if pd.isna(df.at[index, '评语']):
                start_time2 = time.time()
                check, answer = get_comment(df.at[index, '关键词'], self.example, self.requirement,self.model,self.API_key)
                end_time2 = time.time()
                if check:
                    df.at[index, '评语'] = answer
                    self.update_text.emit(f"已填写{df.at[index, '姓名']}的评语，用时{end_time2 - start_time2}")
                    ans += 1
                else:
                    self.update_text.emit(answer)
                    return None
        end_time = time.time()
        with pd.ExcelWriter(file_name, mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, index=False)
        self.update_text.emit(f"总共处理{ans}个同学的评语，用时{end_time - start_time}s")

        # 任务完成时，发出完成信号
        self.finished.emit()
#主窗口
class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.requirements = ""
        self.examples = ""
        self.api_key = ""
        self.check_value = 0
        self.load_data()
        self.thread = None

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

            self.requirements=data.get("requirements", "")
            self.examples=data.get("examples", "")
            self.model = data.get("model","")
            if data.get("model","")=="deepseek-chat":
                self.ui.comboBox.setCurrentIndex(0)
                self.api_key = data["d_api_key"]
                self.ui.API_input.setText(data["d_api_key"])
            elif data.get("model","")=="GPT-4o-mini":
                self.ui.comboBox.setCurrentIndex(1)
                self.api_key = data["c_api_key"]
                self.ui.API_input.setText(data["c_api_key"])
            self.ui.console.append("已从文件加载数据")
        else:
            self.ui.console.append("文件不存在，无法加载数据")

        if data["AI_welcome"]:
            self.ui.emoji_label.setText(get_introduction() + "\n（本欢迎语由人工智障yzh自动生成，不消耗您的token）")
        else:
            self.ui.emoji_label.setText("人工智障yzh难过的退下了😭\n写欢迎语是它这三个月以来找到的唯一的工作👉👈\n真的不能给它一个机会吗🥺")

    #按钮功能
    # 保存
    def save(self):
        self.requirements = self.ui.requirement_input.toPlainText()
        self.examples = self.ui.example_input.toPlainText()
        self.api_key = self.ui.API_input.text()
        file_path = 'data/data.json'
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        data["requirements"] = self.requirements
        data["examples"] = self.examples
        data["model"] = self.model
        if self.model=="deepseek-chat":
            data["d_api_key"] = self.api_key
        else:
            data["c_api_key"]=self.api_key

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)  # ensure_ascii=False 确保中文字符正确保存
        self.ui.console.append("输入已保存")
    # 清除
    def clear(self):
        file_path = 'data/data.json'
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        self.ui.requirement_input.clear()
        self.ui.example_input.clear()
        self.ui.API_input.clear()
        data["requirements"]=None
        data["examples"] = None
        data["model"] = "deepseek-chat"
        data["c_api_key"]=None
        data["d_api_key"] = None
        data["AI_welcome"] = 1
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        self.ui.console.append("输入已清除")
    # 检查
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
    # 开始
    def start(self):
        if self.check_value:
            self.thread = Worker(self.requirements, self.examples, self.model,self.api_key)
            self.thread.update_text.connect(self.update_label)
            self.thread.finished.connect(self.task_finished)
            self.thread.start()
            self.check_value=0
        else:
            self.ui.console.append("请先点击检查按钮，保证所有参数完整")
    # 模型选择函数
    def on_combobox_changed(self,index):
        file_path = 'data/data.json'
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        if index == 0:
            self.model = "deepseek-chat"
            self.ui.console.append(f"已更改模型为{self.model}")
            self.api_key = data["d_api_key"]
            self.ui.API_input.setText(data["d_api_key"])
        elif index == 1:
            self.model = "GPT-4o-mini"
            self.ui.console.append(f"已更改模型为{self.model}")
            self.api_key = data["c_api_key"]
            self.ui.API_input.setText(data["c_api_key"])
        self.ui.console.append("已从文件加载保存的API-key")
    #多线程信号接受
    def task_finished(self):
        # 任务完成时更新标签
        self.ui.console.append("任务完成！")
    def update_label(self, text):
        # 更新标签文本
        self.ui.console.append(text)
#主窗口GUI设定
class Ui_Form(object):
    def setupUi(self, Form):

        Form.setObjectName("Form")
        Form.resize(828, 1450)
        font = QtGui.QFont()
        font.setPointSize(16)  # 设置字体大小为16
        Form.setFont(font)

        # 标题标签
        self.welcome = QtWidgets.QLabel(Form)
        self.welcome.setGeometry(QtCore.QRect(10, 10, 800, 41))  # 改为顶部显示
        self.welcome.setObjectName("label")
        font_label = QtGui.QFont()
        font_label.setPointSize(20)
        self.welcome.setFont(font_label)

        # 分隔线
        self.line = QtWidgets.QFrame(Form)  # 创建一个 QFrame
        self.line.setGeometry(QtCore.QRect(10, 58, 800, 3))  # 设置分隔线位置和尺寸
        self.line.setFrameShape(QtWidgets.QFrame.HLine)  # 设置为水平线
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)  # 设置线条样式
        self.line.setObjectName("line")

        # 欢迎语
        self.emoji_label = QtWidgets.QLabel(Form)
        self.emoji_label.setGeometry(QtCore.QRect(10, 60, 800, 220))  # 设置位置和大小
        self.emoji_label.setObjectName("emoji_label")
        font_label = QtGui.QFont()
        font_label.setPointSize(15)
        self.emoji_label.setFont(font_label)

        # 分隔线
        self.line = QtWidgets.QFrame(Form)  # 创建一个 QFrame
        self.line.setGeometry(QtCore.QRect(10, 282, 800, 3))  # 设置分隔线位置和尺寸
        self.line.setFrameShape(QtWidgets.QFrame.HLine)  # 设置为水平线
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)  # 设置线条样式
        self.line.setObjectName("line")

        #帮助文档
        self.help_text = QtWidgets.QLabel(Form)
        self.help_text.setGeometry(QtCore.QRect(10, 312, 800, 60))  # 下移避免重叠
        self.help_text.setObjectName("label_22")
        font_label_22 = QtGui.QFont()
        font_label_22.setPointSize(20)
        font_label_22.setBold(True)  # 设置加粗
        self.help_text.setFont(font_label_22)  # 应用到标题标签

        # 分隔线
        self.line = QtWidgets.QFrame(Form)  # 创建一个 QFrame
        self.line.setGeometry(QtCore.QRect(10, 398, 800, 3))  # 设置分隔线位置和尺寸
        self.line.setFrameShape(QtWidgets.QFrame.HLine)  # 设置为水平线
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)  # 设置线条样式
        self.line.setObjectName("line")

        #要求
        self.requirement_text = QtWidgets.QLabel(Form)
        self.requirement_text.setGeometry(QtCore.QRect(10, 400, 800, 41))  # 下移避免重叠
        self.requirement_text.setObjectName("label_2")
        self.requirement_prompt = QtWidgets.QLabel(Form)
        self.requirement_prompt.setGeometry(QtCore.QRect(10, 440, 800, 41))  # 下移到适当位置
        self.requirement_prompt.setObjectName("label_21")
        font_label_21 = QtGui.QFont()
        font_label_21.setPointSize(12)
        self.requirement_prompt.setFont(font_label_21)
        self.requirement_input = QtWidgets.QTextEdit(Form)
        self.requirement_input.setGeometry(QtCore.QRect(10, 480, 800, 160))  # 下移到适当位置
        self.requirement_input.setObjectName("textEdit")

        #例子
        self.example_text = QtWidgets.QLabel(Form)
        self.example_text.setGeometry(QtCore.QRect(10, 640, 800, 41))  # 下移以避免重叠
        self.example_text.setObjectName("label_3")
        self.example_prompt = QtWidgets.QLabel(Form)
        self.example_prompt.setGeometry(QtCore.QRect(10, 680, 800, 41))  # 下移到适当位置
        self.example_prompt.setObjectName("label_4")
        font_label_4 = QtGui.QFont()
        font_label_4.setPointSize(12)
        self.example_prompt.setFont(font_label_4)
        self.example_input = QtWidgets.QTextEdit(Form)
        self.example_input.setGeometry(QtCore.QRect(10, 720, 800, 160))  # 下移到适当位置
        self.example_input.setObjectName("textEdit_2")

        #API
        self.API_text1 = QtWidgets.QLabel(Form)
        self.API_text1.setGeometry(QtCore.QRect(10, 880, 800, 41))
        self.API_text1.setObjectName("label_51")
        self.API_text2 = QtWidgets.QLabel(Form)
        self.API_text2.setGeometry(QtCore.QRect(430, 880, 800, 41))
        self.API_text2.setObjectName("label_52")
        self.API_input = QtWidgets.QLineEdit(Form)
        self.API_input.setGeometry(QtCore.QRect(10, 920, 800, 41))
        self.API_input.setObjectName("lineEdit")
        self.comboBox = QtWidgets.QComboBox(Form)
        self.comboBox.setGeometry(QtCore.QRect(172, 880, 250, 40))
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("deepseek-chat")
        self.comboBox.addItem("gpt-4o-mini")

        # 文件提示
        self.file_text1 = QtWidgets.QLabel(Form)
        self.file_text1.setGeometry(QtCore.QRect(10, 960, 800, 41))  # 下移到适当位置
        self.file_text1.setObjectName("label_6")
        self.file_text2 = QtWidgets.QLabel(Form)
        self.file_text2.setGeometry(QtCore.QRect(10, 1000, 800, 41))  # 下移到适当位置
        self.file_text2.setObjectName("label_6")
        self.file_text3 = QtWidgets.QLabel(Form)
        self.file_text3.setGeometry(QtCore.QRect(10, 1040, 800, 41))  # 下移到适当位置
        self.file_text3.setObjectName("label_6")
        self.file_text4 = QtWidgets.QLabel(Form)
        self.file_text4.setGeometry(QtCore.QRect(10, 1080, 800, 41))  # 下移到适当位置
        self.file_text4.setObjectName("label_6")
        self.file_text5 = QtWidgets.QLabel(Form)
        self.file_text5.setGeometry(QtCore.QRect(10, 1120, 800, 41))  # 下移到适当位置
        self.file_text5.setObjectName("label_6")
        self.file_text1.setFont(font_label)
        self.file_text2.setFont(font_label)
        self.file_text3.setFont(font_label)
        self.file_text4.setFont(font_label)
        self.file_text5.setFont(font_label)
        #按钮部分
        #保存
        self.save_botton = QtWidgets.QPushButton(Form)
        self.save_botton.setGeometry(QtCore.QRect(480, 1160, 75, 41))  # 第三个按钮
        self.save_botton.setObjectName("pushButton_3")
        #清除
        self.clear_botton = QtWidgets.QPushButton(Form)
        self.clear_botton.setGeometry(QtCore.QRect(560, 1160, 75, 41))  # 清除按钮
        self.clear_botton.setObjectName("pushButton_4")
        #检查
        self.check_botton = QtWidgets.QPushButton(Form)
        self.check_botton.setGeometry(QtCore.QRect(640, 1160, 75, 41))  # 第一个按钮
        self.check_botton.setObjectName("pushButton")
        #开始
        self.start_botton = QtWidgets.QPushButton(Form)
        self.start_botton.setGeometry(QtCore.QRect(720, 1160, 75, 41))  # 第二个按钮
        self.start_botton.setObjectName("pushButton_2")

        # 进度显示
        self.console_text = QtWidgets.QLabel(Form)
        self.console_text.setGeometry(QtCore.QRect(10, 1200, 800, 41))
        self.console_text.setObjectName("label_7")
        self.console = QtWidgets.QTextBrowser(Form)
        self.console.setGeometry(QtCore.QRect(10, 1240, 800, 160))
        self.console.setObjectName("textBrowser")

        #署名
        self.name = QtWidgets.QLabel(Form)
        self.name.setGeometry(QtCore.QRect(300, 1400, 800, 41))
        self.name.setObjectName("label_name")

        # 信号与槽连接
        self.retranslateUi(Form)
        self.check_botton.clicked.connect(Form.check)
        self.start_botton.clicked.connect(Form.start)
        self.save_botton.clicked.connect(Form.save)
        self.clear_botton.clicked.connect(Form.clear)
        QtCore.QMetaObject.connectSlotsByName(Form)
        self.comboBox.currentIndexChanged.connect(lambda: Form.on_combobox_changed(self.comboBox.currentIndex()))

    #GUI文字设置
    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "评语生成器"))
        self.welcome.setText(_translate("Form", "欢迎使用评语生成器！"))
        self.help_text.setText('如果遇到问题，请查看 <a href="README.pdf">帮助文档</a>🌹🌹🌹')
        self.help_text.setOpenExternalLinks(False)  # 禁用自动打开链接
        self.help_text.linkActivated.connect(self.open_pdf)  # 绑定点击事件
        self.name.setText(_translate("Form", "——hzy和她的小助手叶子黄🤖制作"))
        self.requirement_text.setText(_translate("Form", "请输入要求："))
        self.requirement_prompt.setText(_translate("Form", "（字数，风格，语气，其它特殊要求，越详细效果越好）"))
        self.example_text.setText(_translate("Form", "请输入例子："))
        self.example_prompt.setText(_translate("Form", "（例子越多，消耗的token越多、运行速度越慢、质量越好）"))
        self.check_botton.setText(_translate("Form", "检查"))
        self.start_botton.setText(_translate("Form", "开始"))
        self.save_botton.setText(_translate("Form", "保存"))
        self.clear_botton.setText(_translate("Form", "清除"))  # 清除按钮的文本
        self.API_text2.setText(',<a href="如何获取API-key.pdf">获取</a>并输入你的API-key：')
        self.API_text1.setText(_translate("Form", "请选择模型"))
        self.API_text2.setOpenExternalLinks(False)  # 禁用自动打开链接
        self.API_text2.linkActivated.connect(self.open_pdf)  # 绑定点击事件
        self.file_text1.setText(_translate("Form", "请将包含评价和关键词两列的excel文件拖入input文件夹内！"))
        self.file_text2.setText(_translate("Form", "保存内容后，下次打开程序参数将自动填写"))
        self.file_text3.setText(_translate("Form", "如果要分享本程序，请点击清除按钮，以防你的API-key泄露"))
        self.file_text4.setText(_translate("Form", "程序会自动填写excel中空白的评价单元格。若对结果不满意，"))
        self.file_text5.setText(_translate("Form", "删除该单元格内容后再次运行程序，已填写内容不会被修改。"))
        self.console_text.setText(_translate("Form", "进度显示："))
        self.console.setText(_translate("Form","这里将会显示提示词和进度条"))
    def open_pdf(self, link):
        # 使用系统默认的 pdf 打开方式打开文件
        pdf_path = os.path.join(os.getcwd(), 'data', link)  # 使用相对路径，确保文件位置正确
        QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
