from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement


ROOT = Path(r"D:\论文\软著申请")
SOURCE = ROOT / "预制木构件智能缺陷检测与钉合位置优化系统V1.0_软件著作权登记申请材料_修订版_20260817_06.docx"
OUTPUT = ROOT / "预制木构件智能缺陷检测与钉合位置优化系统V1.0_软件著作权登记申请材料_代码核对修订版_20261025_09.docx"
EXPECTED_SHA256 = "822e2f4214d44d4d9c85b74ce2c66b1798a0e2d64939f1b445923e5b0b7531cf"


def replace_para(para, value: str) -> None:
    # Keep paragraph styling, numbering, indentation and spacing from the source.
    for run in para.runs:
        run.text = ""
    if para.runs:
        para.runs[0].text = value
    else:
        para.add_run(value)


def table_value(table, row_number: int, expected_label: str, value: str) -> None:
    row = table.rows[row_number]
    actual = row.cells[0].text.strip()
    assert actual == expected_label, (row_number, actual, expected_label)
    cell = row.cells[-1]
    replace_para(cell.paragraphs[0], value)
    for para in cell.paragraphs[1:]:
        replace_para(para, "")


assert SOURCE.is_file()
assert sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SHA256
assert not OUTPUT.exists(), OUTPUT
doc = Document(SOURCE)

paragraphs = {
    6: "源程序量统计口径：以2026年10月25日核对的D:\\论文\\机械臂大论文\\src为准，统计xylab/frontend/src中的TypeScript、TSX、CSS，xylab/backend中的Python，以及ai/qwen25vl中的Python；共63个文件、8,734个物理行（含空行和注释）。其中前端38个文件、6,981行，后端23个文件、1,637行，Qwen接口与验证脚本2个文件、116行。前端mock示例数据3个文件、259行。该统计不含node_modules、dist、依赖锁文件、上传图片、模型权重、公开数据和第三方软件，最终交存页数须按实际排版另行核定。",
    12: "负责开发React/TypeScript前端控制界面、路由、状态管理和交互画布。当前代码有总控、装配标定、感知、长板进料、规划、规则库、决策矩阵、决策台、机器人模拟、二维流程演示、日志等11个页面路由。",
    13: "实现预设板件几何的T形叠合重合区计算、多边形判定及有效可钉区域约束；现有标定页展示样例板件和预设手眼参数，真实板件标定数据的录入与实测手眼标定尚未接入。",
    14: "实现浏览器端ROI过滤、缺陷栅格化、圆形结构元膨胀、软代价图、KD-tree最近可行点搜索、钉位偏移记录；另实现图像源场景下的像素网格候选点与示例死节禁区规划。",
    15: "实现Eurocode 5相关间距/边距参数的独立展示计算器、缺陷决策矩阵和浏览器端规则化动作建议。计算器目前未作为钉位规划流水线中的自动工程校核；规范文本及参数公式本身不主张原创，工程适用性须另行核验。",
    16: "负责FastAPI后端开发，实现图片、视频和本地摄像头输入、帧获取、可编辑多边形检测区、样例缺陷标注、候选钉位规划，以及前后端通信与服务状态检查。当前后端缺陷检测采用固定演示框，不能表述为已接入真实YOLO自动识别。",
    17: "负责长板逐钉位拍照、标注图生成、规则化分等、红外设备接口与Qwen2.5-VL视觉服务接口的开发和集成。申请人确认：已使用开源Qwen模型验证服务调用并打通路径；开源模型权重和第三方推理库不计入自有源程序。",
    18: "实现二维上料—扫描—打钉流程动画、机器人技能原语与状态的界面模拟、逐钉日志及JSON/CSV导出。当前没有ROS2/MoveIt实机控制，也没有PDF报告生成。",
    19: "另完成与学位论文相关的重竹钉拉拔、双剪试验数据采集；这些实验数据属于独立研究资料，不作为本软件已接入的数据库或已实现的力学计算模块申报。",
    23: "React、React Router、Zustand、Vite、TypeScript、FastAPI、Pydantic、OpenCV、Pillow、PyTorch、Transformers等第三方框架和依赖。",
    24: "YOLOv8/YOLO11及Qwen2.5-VL等开源模型的预训练权重和第三方底层实现；本项目自有的是业务接口、规则、页面、数据流和联调代码。",
    34: "（1）系统总控与流程编排：显示规划、决策和模拟执行等阶段状态，提供板面样例视图、统计信息和一键运行浏览器端示例规划流程。",
    35: "（2）图像源与缺陷展示：后端支持上传照片、视频文件及读取本地摄像头，获取帧并保存多边形检测区；当前检测器返回按图像尺寸缩放的固定演示死节框。感知页另使用本地模拟缺陷数据。YOLO训练记录与系统自动识别能力应分开表述。",
    36: "（3）装配几何约束：基于预设板件样例计算T形叠合的投影重合区，浏览器端规划可将区外区域排除；真实板件位置录入、相机标定和手眼标定仍需补充。",
    37: "（4）缺陷禁区与ROI：浏览器端支持ROI选择、缺陷栅格化和按安全半径膨胀；图片、视频和摄像头输入通道还支持保存、缩放与筛选多边形区域。两条通道的坐标与规划实现各自独立。",
    38: "（5）钉位规划：浏览器端对示例设计钉位使用KD-tree最近可行点或软代价函数优化；后端图像源通道在像素坐标下按网格生成候选点，并避开演示死节框的外扩区域。",
    39: "（6）规则与决策展示：前端展示缺陷×基材×纹理的示例规则及四类动作建议；另有Eurocode 5参数计算器。当前后端规范检索返回空结果、决策接口返回固定占位值，不能作为已部署RAG或真实大模型决策申报，也不能据此认定钉位已通过规范校核。",
    40: "（7）二维过程与机器人界面模拟：Canvas动画展示上料、扫描和逐钉打钉时序；机器人页面的动作与急停为界面状态模拟，未连接ROS2、MoveIt、RoboDK或实体机械臂。",
    41: "（8）日志导出：浏览器端记录设计坐标、规划坐标、偏移量、动作、理由、规则标签和时间戳，可导出JSON及CSV；未实现PDF自动导出。",
    42: "（9）长板进料与辅助判断：可按板长设置钉位，逐位上传照片、生成演示缺陷标注图并作规则化分等；可向已联调的开源Qwen视觉服务发送标注图和提示词，获得文字建议。红外通道提供模拟结果及可配置HTTP设备接口，真实探伤设备尚未接入。",
    44: "1. 浏览器端规划计算：预设板件几何求交、缺陷栅格化、形态学膨胀、KD-tree最近邻和软代价优化由TypeScript代码执行。",
    45: "2. 双通道规划：浏览器端样例规划在板件坐标中处理重合区、ROI和缺陷禁区；后端图像源规划在像素坐标下处理多边形检测区、固定演示缺陷框和规则网格点。两者尚未合并为经过实测标定的一条生产流程。",
    46: "3. 可查看的规则结果：浏览器端输出动作、位置偏移、理由和规则标签；这些标签与示例参数便于人工复核，但不等于工程规范符合性证明。",
    47: "4. 分层接口：图片、视频、摄像头、规划、规则检索、Qwen视觉问答及红外网关有独立接口；各接口的实测能力和演示数据状态按本稿第六节及接口状态表区分。",
    48: "5. 结果留痕：逐钉记录设计值、规划值、偏移、动作与理由并导出结构化文件；长板进料模块另保存站位照片的标注结果和分等信息。",
    49: "6. 当前运行边界：已经实现交互界面、样例规划、图像源接入和Qwen视觉服务调用路径；真实YOLO推理、工业相机/红外设备联调、机械臂控制与三维仿真尚未由当前代码证明完成。",
    51: "1. 用户可在浏览器示例场景中读取预设板件、缺陷和钉位，也可在图像源页面上传照片、视频或选择本地摄像头并设置多边形检测区。",
    52: "2. 示例场景调用本地模拟缺陷；图像源后端目前返回固定演示死节框。前端可展示结果并对ROI或置信度作筛选，不能据此表述为真实图像自动识别。",
    53: "3. 浏览器端使用预设板件位置计算叠合有效区域；真实标定数据及相机到板面物理坐标的转换仍需接入。",
    54: "4. 浏览器端将示例缺陷栅格化并按设定安全半径膨胀，叠加ROI和装配区域；独立的Eurocode 5参数计算器不自动向该规划链提供合规结论。",
    55: "5. 浏览器端在可行域中用KD-tree或软代价函数寻找候选点；图像源后端另在像素平面使用规则网格避开演示缺陷框，两套结果不应混作同一实测规划输出。",
    56: "6. 浏览器端按示例规则给出直接打钉、预钻后打钉、换位或跳过的建议；长板进料页面可将站位照片送至已联调的Qwen视觉服务获取文字建议。",
    57: "7. 二维界面演示操作时序并导出JSON/CSV日志；机械臂实际运动指令、现场检测准确率和规范符合性须待设备及材料参数接入后验证。",
    59: "九、模型与第三方数据说明",
    60: "既有YOLOv8与YOLO11训练记录属于独立实验材料；本次核对的xylab后端并未加载训练权重，/api/detect实际调用固定演示标注器，不能称为已实现真实木材缺陷自动检测。ai/qwen25vl目录包含基于开源Qwen2.5-VL权重的独立服务与烟测脚本，长板模块通过HTTP接口调用；申请人确认已用开源模型完成联调验证。模型生成的文字建议不直接驱动机械臂或替代确定性钉位校核。",
    61: "训练图像和标注来自网络公开数据集；提交前应补齐名称、来源、许可和使用范围。公开数据、YOLO及Qwen权重、Ultralytics/Transformers等依赖不作为自有源程序；仅将本人负责开发和集成的应用层代码纳入登记材料。",
    64: "以下文字按2026年10月25日所见源代码编制，可作为在线填报字段的基础；软件完成日期和对外发表状态须以最终提交版本及实际公开记录核定。",
    66: "面向预制木构件的缺陷展示、钉位规划和作业记录，开发支持照片、视频及摄像头输入的交互系统，提供板件装配区域分析、示例规则决策、长板逐钉位照片上传与辅助判断，便于研究验证和作业流程追溯。",
    68: "本软件提供预制木构件钉合规划界面。可导入照片、视频或本地摄像头画面，设置多边形检测区并展示缺陷标注；当前后端检测采用固定演示标注。浏览器端可基于预设板件和示例缺陷计算T形叠合区、ROI及膨胀禁区，使用KD-tree或软代价函数调整候选钉位，并按规则给出打钉、预钻、换位或跳过建议。长板进料模块支持设置钉位、逐位上传照片、生成标注图和规则化分等；Qwen2.5-VL开源模型服务已完成接口联调，可输出文字建议。系统提供二维作业流程演示和JSON/CSV日志导出；机械臂实机控制、真实YOLO自动识别及红外探伤设备接入尚未完成。",
    70: "软件将浏览器端几何规划、后端图像源处理和长板进料业务分为独立模块。前端实现ROI、栅格化、膨胀、软代价及KD-tree候选点优化；后端实现照片、视频、摄像头接入与多边形区域保存，并在像素平面生成演示候选点。长板模块把钉位照片、标注、规则化分等与Qwen视觉问答接口串联；外部模型只提供辅助文字说明，不直接产生机械臂控制命令。规划日志记录坐标、动作和理由，支持导出复核。",
    74: "1. 前部代码：frontend/src的程序入口、路由、状态管理、交互画布、进料页、图像源页及主要页面。",
    75: "2. 核心代码：frontend/src/lib中的geometry.ts、grid.ts、morphology.ts、kdtree.ts、costmap.ts、pipeline.ts、decision.ts；ec5.ts作为独立参数计算页的代码。",
    76: "3. 后部代码：frontend/src/api客户端，backend/api、sources、planning、intake、inference及main.py；另附ai/qwen25vl中的自有接口与联调脚本。按源文件原始顺序截取连续前后页，不混入权重、样本图像或第三方源码。",
    77: "4. 生成交存材料前先修复当前前端TypeScript编译错误，随后统一软件名称、版本号、页眉和连续页码，并按实际代码及文档排版核定每页行数。",
    78: "5. 不将dist、node_modules、package-lock、第三方依赖、上传图片、公开数据与标签、训练权重、模型缓存或ROS-Industrial代码计为本人源程序。",
    82: "□ 依据拟提交的前后端和Qwen接口版本，重新确认实际开发完成日期；当前源文件最晚修改至2026年9月28日，旧稿的2026年8月16日不能直接沿用。另确认是否已对外发表及首次发表日期。",
    83: "□ 补充公开木材缺陷数据集名称、来源、作者和许可；保留Qwen模型名称、来源、许可证以及本人接口联调记录。",
    85: "□ 按登记系统最新选项核定软件类别、行业类别等字段；登记名称和V1.0版本须与源程序页眉、说明文档一致，代码内部的XYLab名称仅作为研发项目名。",
    86: "□ 修复frontend/src/pages/Intake.tsx第104行的TypeScript类型错误，再完成前端构建与功能核验；另行制作源程序和用户手册/设计说明书鉴别材料。",
    88: "本人确认：本稿列明的前端、后端、长板进料模块及Qwen视觉服务接口由本人负责开发、集成与验证，无共同程序开发者；木材缺陷公开数据、前端演示数据与真实试验数据分别管理。开源Qwen模型、YOLO预训练权重、第三方框架、公开标准和机器人开源软件不作为本人原创代码申报。重竹钉拉拔与双剪试验数据由本人在导师课题组内采集，数据及成果使用遵循浙江大学和课题组要求。",
}

for index, value in paragraphs.items():
    replace_para(doc.paragraphs[index], value)

# In the source, section 6 uses a bold lead-in and regular body within each item.
for index in range(34, 43):
    lead, body = paragraphs[index].split("：", 1)
    runs = doc.paragraphs[index].runs
    runs[0].text = lead + "："
    if len(runs) < 2:
        runs.append(doc.paragraphs[index].add_run())
    runs[1].text = body
    runs[1].bold = False

# Registration facts; the completion date is deliberately left for version-based confirmation.
table_value(doc.tables[1], 8, "开发期间", "2025年4月至2026年9月（起始时间沿用原记录，结束时间据本次源文件修改时间；最终以版本记录核定）")
table_value(doc.tables[1], 9, "开发完成日期", "【待核定】当前纳入的进料及Qwen代码最晚修改于2026年9月28日，不沿用旧稿2026年8月16日")
table_value(doc.tables[1], 12, "源程序量", "8,734个物理行、63个源文件（前端6,981行/38个；后端1,637行/23个；Qwen 116行/2个；含注释及空行）")

# Provenance of datasets, examples and model interfaces.
table_value(doc.tables[3], 3, "前端mock示例数据", "仅供浏览器离线示例与流程展示，不能作为真实检测结果或实验数据；本次统计为3个文件、259个物理行")
table_value(doc.tables[3], 4, "YOLO训练结果", "训练材料由申请人另行提供；当前xylab后端未加载YOLO权重，不能将训练结果写成已部署的自动识别能力")

table_value(doc.tables[4], 1, "开发目的", "构建用于预制木构件图像源展示、样例缺陷避让、钉位规划、长板逐位拍照和作业记录的交互软件，支撑研发验证与流程追溯。")
table_value(doc.tables[4], 4, "主要输入", "样例板件与缺陷数据、照片/视频/本地摄像头帧、多边形检测区、预设钉位与规划参数、长板站位照片")
table_value(doc.tables[4], 5, "主要输出", "演示缺陷标注、候选钉位与动作建议、站位标注图与规则化分等、Qwen辅助文字建议、JSON/CSV日志")

table_value(doc.tables[5], 1, "开发硬件环境", "【待核定】实际开发设备CPU、内存和GPU型号；Qwen开源模型的联调环境另需列明GPU及模型路径")
table_value(doc.tables[5], 2, "运行硬件环境", "前端需现代浏览器；后端图像源与摄像头需相应采集设备；独立Qwen视觉服务需满足所用开源模型的GPU资源要求")
table_value(doc.tables[5], 3, "开发操作系统", "【待核定】前端、后端及Qwen服务的实际开发/联调系统；Qwen脚本写有Linux模型路径和CUDA设备")
table_value(doc.tables[5], 5, "后端接口工具", "Python、FastAPI、Uvicorn、Pydantic、Pillow、OpenCV；Qwen服务另使用PyTorch、Transformers及qwen-vl-utils")
table_value(doc.tables[5], 6, "运行平台", "Chrome、Edge等现代浏览器；FastAPI后端；Qwen2.5-VL独立HTTP服务（配置后调用）")

states = [
    ("图像/视频/摄像头", "上传、帧获取、暂停/恢复及多边形区保存代码已实现；实际相机设备运行未核验", "可描述为支持图像源接入与区域管理；不据此宣称完成工业相机现场联调"),
    ("YOLO与缺陷检测", "现有后端调用固定演示标注器；YOLO训练记录与系统接入分离", "仅写演示缺陷框与外部模型适配空间，不写已实现真实自动识别"),
    ("规则检索与决策", "前端样例规则与确定性动作建议代码已实现；后端检索为空、决策为固定占位", "不宣称已部署RAG、LLM决策或已通过工程规范校核"),
    ("Qwen视觉问答", "本人开发独立Qwen2.5-VL服务和调用接口；据申请人确认已用开源权重验证调用路径", "可写开源模型辅助文字建议的接口已联调；模型权重不计原创代码"),
    ("长板进料与红外", "逐位照片上传、标注图、规则化分等已实现；红外为模拟桩或可配置网关", "不宣称真实红外探伤设备已完成接入"),
    ("机械臂与二维演示", "二维Canvas流程动画和机器人界面模拟；无ROS2/MoveIt实机命令", "写二维演示和执行界面，不写机器人实际控制"),
    ("报告导出", "JSON、CSV已实现；PDF未实现", "仅申报JSON、CSV导出"),
]
table = doc.tables[6]
while len(table.rows) < len(states) + 1:
    table._tbl.append(deepcopy(table.rows[-1]._tr))
for row_index, values in enumerate(states, start=1):
    for col_index, value in enumerate(values):
        cell = table.rows[row_index].cells[col_index]
        replace_para(cell.paragraphs[0], value)
        for para in cell.paragraphs[1:]:
            replace_para(para, "")

table_value(doc.tables[7], 1, "源程序鉴别材料", "从本次核定的自有TypeScript/TSX/CSS/Python源文件选取连续代码；排除依赖、构建产物、上传图片、模型权重及第三方源码；制作前先修复前端编译错误")

# Repeat table headings when a table continues onto a new page.
for table in doc.tables[:8]:
    tr_pr = table.rows[0]._tr.get_or_add_trPr()
    if not any(child.tag.endswith("tblHeader") for child in tr_pr):
        tr_pr.append(OxmlElement("w:tblHeader"))

doc.core_properties.title = "预制木构件智能缺陷检测与钉合位置优化系统 V1.0 软件著作权登记申请材料（代码核对修订版）"
doc.core_properties.subject = "依据2026年10月25日所见前后端及Qwen接口代码核对"
doc.save(OUTPUT)
print(OUTPUT)
