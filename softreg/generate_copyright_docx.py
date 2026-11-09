# -*- coding: utf-8 -*-
"""Generate software copyright registration Word document."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


OUTPUT = Path(r"D:\论文\软著申请\预制木构件智能缺陷检测与钉合位置优化系统_软件著作权登记申请书.docx")

SOFTWARE_NAME = "预制木构件智能缺陷检测与钉合位置优化系统"
SOFTWARE_SHORT = "智能钉合系统"
VERSION = "V1.0"
COPYRIGHT_OWNER = "王尉廷"


def set_run_font(run, name="宋体", size=12, bold=False):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold


def add_title(doc, text, size=16):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    set_run_font(run, "黑体", size, True)
    p.paragraph_format.space_after = Pt(12)


def add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, "黑体", 14 if level == 1 else 12, True)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)


def add_paragraph(doc, text, indent=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, "宋体", 12)
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.74)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(4)


def add_kv_table(doc, rows):
    table = doc.add_table(rows=len(rows), cols=2)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for i, (k, v) in enumerate(rows):
        c0 = table.rows[i].cells[0]
        c1 = table.rows[i].cells[1]
        c0.width = Cm(4.5)
        c1.width = Cm(11.5)
        r0 = c0.paragraphs[0].add_run(k)
        set_run_font(r0, "宋体", 11, True)
        r1 = c1.paragraphs[0].add_run(v)
        set_run_font(r1, "宋体", 11)
    doc.add_paragraph()


def build_document():
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)

    add_title(doc, "计算机软件著作权登记申请书")
    add_paragraph(doc, f"软件名称：{SOFTWARE_NAME}")
    add_paragraph(doc, f"版本号：{VERSION}")
    add_paragraph(doc, f"著作权人：{COPYRIGHT_OWNER}")

    add_heading(doc, "一、基本信息")
    add_kv_table(
        doc,
        [
            ("软件全称", SOFTWARE_NAME),
            ("软件简称", SOFTWARE_SHORT),
            ("版本号", VERSION),
            ("软件分类", "应用软件"),
            ("分类号", "30999-其他应用软件"),
            ("开发完成日期", "2026年6月"),
            ("首次发表日期", "未发表"),
            ("发表状态", "未发表"),
            ("开发方式", "独立开发"),
            ("权利取得方式", "原始取得"),
            ("权利范围", "全部权利"),
        ],
    )

    add_heading(doc, "二、著作权人信息")
    add_kv_table(
        doc,
        [
            ("著作权人名称", COPYRIGHT_OWNER),
            ("著作权人类型", "个人"),
            ("国籍/地区", "中国"),
            ("联系人", COPYRIGHT_OWNER),
            ("证件类型及号码", "（请填写身份证号码）"),
            ("通讯地址", "（请填写通讯地址）"),
            ("邮政编码", "（请填写）"),
            ("联系电话", "（请填写）"),
            ("电子邮箱", "（请填写）"),
        ],
    )

    add_heading(doc, "三、开发环境与运行环境")
    add_kv_table(
        doc,
        [
            (
                "开发的硬件环境",
                "Intel Core i7 及以上处理器，16GB 及以上内存，512GB SSD，"
                "NVIDIA GPU（8GB 显存及以上）",
            ),
            (
                "运行的硬件环境",
                "Intel Core i5 及以上处理器，8GB 及以上内存，256GB 及以上存储空间；"
                "可选 NVIDIA GPU、工业 RGB 相机及机械臂控制器",
            ),
            (
                "开发该软件的操作系统",
                "Windows 10/11 64 位、Ubuntu 22.04 LTS 64 位",
            ),
            (
                "软件开发环境/开发工具",
                "Python 3.10、PyTorch、Ultralytics YOLOv8、OpenCV、NumPy、SciPy、"
                "Matplotlib、ROS2 Humble、MoveIt!、Gazebo、RViz2、Git",
            ),
            (
                "该软件的运行平台/操作系统",
                "Windows 10/11 64 位、Ubuntu 22.04 LTS 64 位",
            ),
            (
                "软件运行支撑环境/支持软件",
                "Python 3.10 运行时、PyTorch、OpenCV、NumPy、SciPy、Ultralytics、"
                "ROS2 Humble、MoveIt!、Gazebo",
            ),
            ("编程语言", "Python、C++、JSON"),
            ("源程序量", "约 12000 行"),
        ],
    )

    add_heading(doc, "四、软件用途与面向领域")
    add_paragraph(
        doc,
        "开发目的：面向预制木结构墙体钉合、托板钉制等可回收竹木构件智能建造场景，"
        "实现打钉前缺陷与铁钉扫描、多板叠合钉位规划、规范约束智能决策及机械臂执行，"
        "提升木构件钉合作业的自动化水平与质量可追溯性。",
        indent=True,
    )
    add_paragraph(
        doc,
        "面向领域/行业：土木工程、木结构工程、智能建造、工业机器人、计算机视觉、具身智能。",
        indent=True,
    )

    add_heading(doc, "五、软件的主要功能")
    functions = [
        "（1）材料状态感知模块：基于 YOLOv8-seg 实例分割模型，对木材/竹材表面 7 类目标"
        "（活节、死节、裂缝、腐朽、虫洞、既有铁钉及竹材典型缺陷等）进行检测与分割，"
        "输出检测框、分割掩码、类别标签与置信度，并支持手眼标定后将像素坐标映射至板面物理坐标系。",
        "（2）禁区构建与钉位规划模块：将分割掩码栅格化为 1 mm 分辨率代价图，采用圆形结构元素"
        "对缺陷区域进行 10 mm 膨胀，形成原始禁区与膨胀禁区；支持多板叠合时各板禁区并集叠加；"
        "对落入禁区的预设钉位，采用 KD 树最近邻搜索在可行域内求解距设计点最近的合规替代钉位，"
        "并记录偏移量与偏移原因。",
        "（3）装配几何约束模块：针对 T 形叠合等装配场景，计算上下板件俯视投影的几何交集，"
        "得到有效钉合区域；对不在重合区内的候选钉位进行预过滤或就近换位，"
        "确保钉体同时贯穿上下板件。",
        "（4）规范—知识双源智能决策模块：采用基于规则的大语言模型决策架构，"
        "第一层为 Eurocode 5 等规范硬约束校验；第二层为缺陷×基材×纹理决策矩阵；"
        "第三层为 RAG 规范检索与缺陷打钉知识库融合推理，输出结构化 JSON 决策"
        "（NAIL / PREDRILL / RELOCATE / SKIP），并附引用条款与决策理由。",
        "（5）机器人执行与数字孪生模块：基于 ROS2 + MoveIt! + Gazebo 构建仿真与执行环境，"
        "将打钉、预钻孔、换位等动作封装为带权限边界的 Skill 原语，"
        "驱动 KUKA 机械臂完成路径规划与动作执行；RViz2 实时显示板件、禁区、钉位与机械臂状态。",
        "（6）施工质量日志模块：自动记录每次作业的钉位坐标、偏移量、缺陷类型、"
        "决策动作、置信度及时间戳，导出 JSON/PDF 格式施工质量报告，支持质量追溯。",
    ]
    for item in functions:
        add_paragraph(doc, item, indent=True)

    add_heading(doc, "六、软件的技术特点")
    features = [
        "（1）感知—规划—决策—执行四层分层架构：几何坐标由确定性算法（代价图 + KD 树）求解，"
        "语义策略由规则增强大模型推理，兼顾亚毫米级精度与多因素可解释决策。",
        "（2）软代价图与多板叠合禁区模型：将 YOLO 检测置信度引入高斯加权代价图，"
        "支持单板与多板叠合场景下的禁区并集叠加。",
        "（3）规范硬约束与缺陷知识双源融合：RAG 检索 Eurocode 5 等规范条款，"
        "结合竹木缺陷打钉专家规则矩阵，实现可追溯、可引证的智能决策。",
        "（4）装配几何约束优先过滤：在缺陷分析前引入板件重合区约束，"
        "适用于 T 形叠合等复杂装配场景。",
        "（5）Skill 约束执行机制：将机器人权限压缩至预定义安全动作空间，"
        "LLM 仅输出策略类型，不直接输出运动指令，保障工业安全。",
        "（6）开源数据集兼容：支持 Kodytek et al. (2021) Zenodo 木材缺陷数据集"
        "及 Roboflow 补充数据集的训练与推理接口。",
    ]
    for item in features:
        add_paragraph(doc, item, indent=True)

    add_heading(doc, "七、系统架构说明")
    architecture = (
        "输入层：RGB 图像 / 预设钉合 Pattern / 装配配置文件(JSON)\n"
        "    ↓\n"
        "感知层（模块 1）\n"
        "  ├── 1A 缺陷检测：YOLOv8-seg → 掩码 + 置信度\n"
        "  ├── 1B 铁钉扫描：外露/齐平/锈蚀铁钉识别\n"
        "  └── 1C 探伤接口：超声波/金属探测器融合架构（预留）\n"
        "    ↓\n"
        "规划层（模块 2）\n"
        "  ├── 栅格化（1 mm/格）\n"
        "  ├── 形态学膨胀（r = 10 mm）\n"
        "  ├── 多板禁区并集\n"
        "  └── KD 树最近合规钉位搜索\n"
        "    ↓\n"
        "认知层（模块 2.5）\n"
        "  ├── 第 0 层：装配重合区过滤\n"
        "  ├── 第 1 层：规范硬约束\n"
        "  ├── 第 2 层：缺陷决策矩阵\n"
        "  └── 第 3 层：LLM + RAG 融合推理\n"
        "    ↓\n"
        "执行层（模块 3）\n"
        "  ├── ROS2 + MoveIt! + Gazebo 数字孪生\n"
        "  ├── Skill 原语：NAIL / PREDRILL / RELOCATE / SKIP\n"
        "  └── KUKA 机械臂控制\n"
        "    ↓\n"
        "输出层：施工质量日志(JSON/PDF) + 可视化结果"
    )
    add_paragraph(doc, architecture)

    add_heading(doc, "八、鉴别材料清单")
    add_kv_table(
        doc,
        [
            ("源程序", "前后各连续 30 页，共 60 页；每页不少于 50 行；页眉标注软件名称与版本号"),
            ("文档", "前后各连续 30 页，共 60 页；可使用用户手册、设计说明书或操作说明"),
            ("申请表", "在线填报后打印，签字确认"),
            ("身份证明", "著作权人身份证复印件"),
        ],
    )

    add_heading(doc, "九、申请人声明")
    add_paragraph(
        doc,
        f"本人 {COPYRIGHT_OWNER} 系上述软件的著作权人，"
        f"该软件《{SOFTWARE_NAME}》（{VERSION}）系本人独立开发完成，"
        "软件内容真实、合法，不存在侵犯他人知识产权的情形。"
        "如有不实，本人愿承担相应法律责任。",
        indent=True,
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run("著作权人（签字）：________________")
    set_run_font(run, "宋体", 12)

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run2 = p2.add_run("日期：______年______月______日")
    set_run_font(run2, "宋体", 12)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    path = build_document()
    print(f"Generated: {path}")
