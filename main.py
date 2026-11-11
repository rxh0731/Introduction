import os, sys, re, time, logging, json
from pathlib import Path
from layout_model import SETTINGS_VERSION, TITLE_DEFAULTS, TAIL_DEFAULTS, OVERALL_DEFAULTS, migrate_settings, complete_params, place_text
from layout_render import draw_layout, glyph_rect, glyph_font
from PySide6.QtCore import Qt, QRectF, QPointF, QEvent, QTimer, QLocale
from PySide6.QtGui import QFontDatabase, QImage, QPainter, QPen, QColor, QFont, QCursor, QPixmap, QTextCursor, QIntValidator, QDoubleValidator
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFormLayout, QLabel, QPushButton, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QFileDialog, QLineEdit, QScrollArea, QMessageBox, QGroupBox, QProgressDialog, QGridLayout, QSplitter, QSizePolicy, QAbstractSpinBox, QTabWidget)
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrinterInfo

MM = 300 / 25.4
logging.basicConfig(filename='export.log', level=logging.INFO, format='%(asctime)s %(message)s', encoding='utf-8')

# 内置默认参数。首次运行且外部参数设置文件不存在时使用；用户点击“参数保存”
# 后仍会优先读取工作目录中的参数设置.json。
BUILTIN_SETTINGS = {
    'text': '\u3000序言\u3000\n佛法東漸時輪轉動華夏大地照進一縷新的覺悟之光中華文明注入一股新的智慧源泉歷代中外高僧大德篳路藍縷辛苦遭逢白馬馱經而來西行求法而去歷經千年心無疲厭殫精竭慮嘔心瀝血將佛法大小顯密各類經典移譯華夏日益完備裨使華夏總持佛典之全部總集佛法之大成\n然世事無常人間滄桑中國第一個佛教宗派天台宗宗祖南嶽慧思大師生逢身處動蕩分裂的南北朝深體正法住世之不易遂作立誓願文發願持令佛法不滅正法久住又誓願造金字佛經以期法寶不失法輪常轉\n華夏石刻肇自上古先民勒石記事銘功周秦碑碣漢魏摩崖歷六朝而趨盛經唐宋而達巔峰佛法初傳三寶漸全漢魏兩晉石窟營造佛像勒石鐫刻佛經即已發端南北朝際佛法漸趨隆盛刻經蔚然成風泰山金剛經摩崖石刻徂徠摩訶般若經文殊般若經石刻已成大觀\n慧思大師弟子隋靜琬上人承蒙師教以師志為己志學宗親師造金字佛經之精神借鏡已有石刻佛經之經驗發心將眾經大藏刻於石上以期佛說法藏經典長存不滅佛教法身慧命持久永續遂於隋大業年間於今北京房山地區鑿石室刻石經持續卅載直至圓寂刻成經石一百四十六塊計佛經十二部其後靜琬上人開創的刻經事業歷經唐宋遼金元明清千年續刻成為世界上規模最大歷史最久的石刻佛教大藏經共刻佛經千餘部三千餘卷石經版一萬五千餘塊總字數超三千五百多萬字是即北京房山石經誠為佛典之善品華夏之至寶清乾隆帝譽為千年法藏當代趙樸初大德贊為文化長城\n今欣聞家鄉浙江紹興上虞多寶講寺以校勘精審之房山石經善本為主要底本發心聚力歷時數年鐫刻雜阿含經小品般若經大品般若經金剛經心經解深密經法華經觀世音菩薩普門品楞嚴經觀世音菩薩耳根圓通章楞嚴咒大悲咒中論攝大乘論等經論密咒於金石之上成經版三百九十一塊凡五十七萬字講寺勒刻經典顯揚法義其心之誠其力之猛與先賢一脈相承一以貫之與古德同心同德同願同行深為震撼無比讚歎\n多寶講寺此次所選刻之經典選取大藏各部類精華涵蓋了阿含般若中觀法相唯識佛性如來藏密咒等大小顯密全體佛法乃大藏之精華和縮影尤以般若中觀類經典為主體般若乃全體佛法特別是大乘佛法之綱要樞紐與核心般若被稱為諸佛之母一切眾生之祖母大品般若曰摩訶般若波羅蜜是諸菩薩摩訶薩母能生諸佛攝持菩薩心經亦云三世諸佛依般若波羅蜜多故得阿耨多羅三藐三菩提究實而言佛陀在菩提樹下悟道就是以般若正智即通達一切法真如實性之無分別智觀照諸法實相證入真如實際開般若正智即開佛知見能見般若即為見佛\n講寺師祖海公上人一生持戒精嚴特重般若晚年深弘阿含講寺開山敏公上人繼以持戒為本更以弘揚般若為要務兼弘唯識俱舍又結合漢傳圓教大旨深契佛教中國化之精髓盡顯佛門大乘精神之內涵現任住持紹隆師門宗風引領大眾嚴守佛制戒律廣學般若奧義精勤修行護國利民令多寶清淨道場住持正法聞名於世可欽可贊今又發心效仿先德刻經於金石之上以期法寶永續法輪常轉實乃皆大歡喜之盛事吾人樂觀其成並期未來因緣具足之時刻經不斷增廣乃至蔚成一大藏存世永年恒護正法廣利群生\u3000樓宇烈謹識\n\n*佛暦二千五百七十年四月初四\u3000\n*農暦丙午年四月初四\u3000\u3000\u3000\u3000\u3000\n*西暦二千零廿六年五月廿日\u3000\u3000\n*文殊菩薩聖誕日於京西三不堂\u3000', 'dpi': 300, 'cell_h': 45.0, 'cell_w': 50.0, 'cols': 44,
    'settings_version': SETTINGS_VERSION, **TITLE_DEFAULTS, **TAIL_DEFAULTS, **OVERALL_DEFAULTS,
    'rows': 31, 'gap_r': 0.0, 'gap_c': 0.0, 'big': True, 'grid_visible': True,
    'grid_width': 5, 'cross_width': 2, 'frame_width': 10,
    'offset_x': 0.0, 'offset_y': 5.0, 'frames': [50.0]*4,
    'margins': [230.0]*4, 'font': 'FZWeiBei-S03', 'title_font': 'FZWeiBei-S03',
    'font_size': 120, 'title_size': 240, 'tail_font': 'FZWeiBei-S03', 'outdir': '%userprofile%\\Desktop',
    'filename': '序言', 'format': 'PSD/PSB'
}

class WhitespaceTextEdit(QTextEdit):
    """在编辑区显示空格边框，但不改变实际文本内容。"""
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        pen = QPen(QColor('#A8A8A8'), 1, Qt.SolidLine)
        painter.setPen(pen)
        doc = self.document()
        block = doc.begin()
        while block.isValid():
            text = block.text()
            for i, ch in enumerate(text):
                if ch not in (' ', '\u3000'):
                    continue
                pos = block.position() + i
                cursor = QTextCursor(doc)
                cursor.setPosition(pos)
                left = self.cursorRect(cursor)
                cursor.setPosition(pos + 1)
                right = self.cursorRect(cursor)
                width = max(2, right.left() - left.left())
                rect = left.adjusted(0, 2, width, -2)
                painter.drawRect(rect)
            block = block.next()
        painter.end()

class Preview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.params = {}; self.text = ""; self.zoom = 1.0; self.pan = QPointF(0, 0); self.drag_pos = None; self.setMinimumSize(200, 200); self.setMouseTracking(True)
    def set_data(self, params, text):
        self.params, self.text = complete_params(params, text), text
        params = self.params
        self.zoom = 1.0
        if self.width() > 0:
            fit=min((self.width()-30)/max(1,params['canvas_w']*MM),(self.height()-30)/max(1,params['canvas_h']*MM))
            self.pan=QPointF(((self.width()-30)-params['canvas_w']*MM*fit)/2,((self.height()-30)-params['canvas_h']*MM*fit)/2)
        else: self.pan=QPointF(0,0)
        self.update()
    def paintEvent(self, e):
        p = QPainter(self); p.fillRect(self.rect(), QColor("#d9d9d9"))
        self.draw_layout(p, self.width(), self.height())
        p.end()
    def draw_layout(self, p, width, height, export=False):
        if not self.params: return
        scale = self.params['dpi'] / 25.4 if export else min(
            (width-30)/self.params['canvas_w'], (height-30)/self.params['canvas_h']) * self.zoom
        origin = (0, 0) if export else (15+self.pan.x(), 15+self.pan.y())
        self.glyphs, self.warnings = draw_layout(p, self.params, self.text, scale, origin)
    def wheelEvent(self, e):
        delta = e.angleDelta()
        native_alt = False
        if sys.platform == 'win32':
            import ctypes
            native_alt = bool(ctypes.windll.user32.GetAsyncKeyState(0x12) & 0x8000)
        if (e.modifiers() & Qt.AltModifier) or getattr(self, 'alt_pressed', False) or native_alt:
            # Qt 在部分 Windows 触控板驱动中滚轮方向会反转，统一按正值上滚放大。
            direction = delta.y() or e.pixelDelta().y() or delta.x() or e.pixelDelta().x()
            if not direction: return
            old_zoom = self.zoom
            self.zoom = max(.05, self.zoom * (1.1 if direction > 0 else (1 / 1.1)))
            anchor = e.position() - QPointF(15,15)
            self.pan = anchor - (anchor-self.pan)*(self.zoom/old_zoom)
            logging.info('预览缩放：angle=(%s,%s) pixel=(%s,%s) zoom=%.4f -> %.4f', delta.x(),delta.y(),e.pixelDelta().x(),e.pixelDelta().y(),old_zoom,self.zoom)
        else:
            # 主滚轮上下滚动；副滚轮（水平滚轮）左右滚动。
            self.pan += QPointF(delta.x() / 6.0, delta.y() / 6.0)
        self.update(); e.accept()
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag_pos = e.position(); self.setCursor(Qt.ClosedHandCursor); e.accept()
        else:
            super().mousePressEvent(e)
    def mouseMoveEvent(self, e):
        if self.drag_pos is not None:
            self.pan += e.position() - self.drag_pos; self.drag_pos = e.position(); self.update(); e.accept()
        else:
            super().mouseMoveEvent(e)
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag_pos = None; self.setCursor(Qt.ArrowCursor); e.accept()
        else:
            super().mouseReleaseEvent(e)

def render_layout_image(params, text, width=None, *, draw_text=True):
    """独立导出渲染器，不读取当前预览窗口的缩放或平移状态。"""
    params = complete_params(params, text)
    _, warnings = place_text(params, text)
    if warnings: raise ValueError('\n'.join(warnings))
    width=round(params['canvas_w']*params['dpi']/25.4)
    height=round(params['canvas_h']*params['dpi']/25.4)
    image=QImage(width,height,QImage.Format_RGB32); image.fill(QColor('white'))
    if image.isNull(): raise MemoryError('无法分配完整输出画布')
    image.setDotsPerMeterX(round(params['dpi']/0.0254)); image.setDotsPerMeterY(round(params['dpi']/0.0254))
    painter=QPainter(image)
    draw_layout(painter, params, text, params['dpi']/25.4, draw_text=draw_text)
    painter.end()
    return image

def export_layered_psd(params, text, path, compressed, progress):
    params = complete_params(params, text)
    glyphs, warnings = place_text(params, text)
    if warnings: raise ValueError('\n'.join(warnings))
    from PIL import Image
    from psd_tools import PSDImage
    from psd_tools.constants import Compression
    compression = Compression.RLE if compressed else Compression.RAW
    width = round(params['canvas_w'] * params['dpi'] / 25.4)
    height = round(params['canvas_h'] * params['dpi'] / 25.4)
    psb = max(width, height) > 30000 or width * height * 8 > 1800000000
    path = path.with_suffix('.psb' if psb else '.psd')
    document = PSDImage.new('RGBA', (width, height), color=(255, 255, 255, 255))
    if psb: document._record.header.version = 2
    # 使用独立画布只绘制框线，文字以小尺寸透明图层写入。
    grid = render_layout_image(params, text, draw_text=False)
    progress.setLabelText('正在生成透明网格层…'); progress.setValue(25); QApplication.processEvents()
    # 透明化网格背景使用 NumPy 向量运算，避免逐像素 Python 循环。
    # 当前画布可达数亿像素，逐像素访问会成为明显瓶颈。
    import numpy as np
    grid_raw = bytes(grid.bits())
    grid_array = np.frombuffer(grid_raw, dtype=np.uint8).reshape((height, width, 4)).copy()
    # QImage 的 BGRA 顺序：B、G、R、A；白色背景直接将 Alpha 置零。
    white_mask = (grid_array[:, :, 0] > 248) & (grid_array[:, :, 1] > 248) & (grid_array[:, :, 2] > 248)
    grid_array[:, :, 3][white_mask] = 0
    # 转成 PIL 需要的 RGBA 顺序。
    grid_pil = Image.fromarray(grid_array[:, :, [2, 1, 0, 3]], 'RGBA')
    del grid_array, white_mask, grid_raw
    progress.setValue(48); QApplication.processEvents()
    grid_layer = document.create_pixel_layer(grid_pil, name='网格与框', compression=compression)
    grid_layer.name = '网格与框'
    groups = {}
    del grid, grid_pil
    factor = params['dpi']/25.4
    total_layers = len(glyphs)
    for index, glyph in enumerate(glyphs):
        rect = glyph_rect(params, glyph, factor)
        w, h = rect.width(), rect.height()
        tile = QImage(max(1, round(w)), max(1, round(h)), QImage.Format_ARGB32)
        tile.fill(Qt.transparent)
        painter = QPainter(tile)
        painter.setFont(glyph_font(params, glyph.cell.title, factor, glyph.cell.region))
        painter.setPen(QColor('black'))
        painter.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, glyph.text)
        painter.end()
        pil = Image.frombuffer('RGBA', (tile.width(), tile.height()), bytes(tile.bits()), 'raw', 'BGRA', 0, 1)
        group = groups.get(glyph.group_name)
        if group is None:
            group = document.create_group(name=glyph.group_name, open_folder=False)
            groups[glyph.group_name] = group
        text_layer = group.create_pixel_layer(pil, name=glyph.layer_name, left=round(rect.x()),
                                             top=round(rect.y()), compression=compression)
        text_layer.name = glyph.layer_name
        if text_layer.has_mask():
            raise RuntimeError(f'文字图层意外包含蒙版：{glyph.layer_name}')
        if index % 5 == 0:
            progress.setLabelText(f'正在创建文字图层 {index+1}/{total_layers}')
            progress.setValue(50+round(35*(index+1)/max(1,total_layers)))
            QApplication.processEvents()
    grid_layer = next(layer for layer in document if layer.name == '网格与框')
    # psd-tools 的 API 顺序为从底到顶，Photoshop 面板显示时相反。
    # 顶部依次为标题、正文 1、2……，底部为网格与框、纯白。
    def group_key(group):
        if group.name == '标题': return (0, 0)
        if group.name == '尾题': return (2, 0)
        return (1, int(group.name))
    text_groups = sorted(groups.values(), key=group_key)
    for group in text_groups:
        if group.name in ('标题', '尾题'):
            group._layers.sort(key=lambda layer: (int(layer.name.split('.')[0][2:]), int(layer.name.split('.')[1])), reverse=True)
        else:
            group._layers.sort(key=lambda layer: tuple(map(int, layer.name.split('.')[:2])), reverse=True)
    white = Image.new('RGBA', (width, height), (255,255,255,255))
    white_layer = document.create_pixel_layer(white, name='纯白', compression=compression)
    white_layer.name = '纯白'
    document._layers[:] = [white_layer, grid_layer] + list(reversed(text_groups))
    document._update_record()
    document._updated = False
    progress.setLabelText('正在写入分层文件…'); QApplication.processEvents()
    document.save(str(path),encoding='gb18030',compression=compression)
    logging.info('分层输出完成：%s，文字层=%s，总图层=%s',path,len(glyphs),len(document))
    return path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('经文排版程序')
        self.resize(1500, 900)
        self.setCentralWidget(QWidget())
        self.text = WhitespaceTextEdit()
        self.preview = Preview()
        self.fonts = []
        # 显式加载已安装的默认字体，兼容离屏导出时的字体发现。
        import winreg
        for root_key in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(root_key, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts') as key:
                    for index in range(winreg.QueryInfoKey(key)[1]):
                        name, filename, _ = winreg.EnumValue(key, index)
                        if '方正魏碑_GBK' in name:
                            font_path = Path(filename)
                            if not font_path.is_absolute(): font_path = Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'/filename
                            font_id = QFontDatabase.addApplicationFont(str(font_path))
                            loaded = QFontDatabase.applicationFontFamilies(font_id)
                            if loaded: self.default_font_family = loaded[0]
            except OSError:
                pass
        families = QFontDatabase.families()
        for _ in range(3):
            combo = QComboBox(); combo.addItems(families)
            combo.setCurrentText('方正魏碑_GBK' if '方正魏碑_GBK' in families else 'Arial')
            if hasattr(self, 'default_font_family'):
                combo.addItem('方正魏碑_GBK', self.default_font_family)
                combo.setCurrentIndex(combo.count()-1)
            self.fonts.append(combo)
        self.controls = {}
        specs = [
            ('dpi','dpi',300,72,1200,0),
            ('section_gap','section_gap',25,0,2000,2),
            ('cell_h','ch',45,0.01,2000,2), ('cell_w','cw',50,0.01,2000,2),
            ('cols','cols',44,1,200,0), ('rows','rows',31,1,200,0),
            ('gap_r','gap_r',0,0,2000,2), ('gap_c','gap_c',0,0,2000,2),
            ('font_size','fsize',120,1,2000,2), ('title_size','title_size',240,1,2000,2),
            ('grid_width','grid_width',1,1,100,0), ('cross_width','cross_width',1,1,100,0),
            ('frame_width','frame_width',1,1,100,0),
            ('offset_x','offset_x',0,-100,100,2), ('offset_y','offset_y',5,-100,100,2)]
        for key, default in {**TITLE_DEFAULTS, **TAIL_DEFAULTS}.items():
            integer = key in ('title_cols', 'title_rows', 'tail_cols', 'tail_rows')
            minimum = 1 if integer else (0.01 if key.endswith(('cell_h','cell_w')) else (-100 if 'offset' in key else 0))
            specs.append((key,key,default,minimum,200 if integer else (100 if 'offset' in key else 2000),0 if integer else 2))
        for key, attr, default, low, high, decimals in specs:
            control = self.num(default,low,high,decimals)
            self.controls[key] = control
            setattr(self,attr,control)
        self.section_gap.setToolTip('独立一行的半角 # 触发分版；连续标记累计间距，空行仍空一列。')
        self.frames=[self.num(50,0,2000,2) for _ in range(4)]
        self.margins=[self.num(230,0,2000,2) for _ in range(4)]
        self.tail_font = self.fonts[2]
        self.big=QCheckBox('大框'); self.big.setChecked(True)
        self.grid_visible=QCheckBox('田字格'); self.grid_visible.setChecked(True)
        self.outdir=QLineEdit(str(Path.cwd()/'output'))
        self.filename=QLineEdit('经文排版')
        self.format=QComboBox()
        self.rebuild_ui()
        QApplication.instance().installEventFilter(self)

    def rebuild_ui(self):
        old = self.centralWidget()
        root = QWidget(); outer = QHBoxLayout(root)
        splitter = QSplitter(Qt.Horizontal); outer.addWidget(splitter)
        panel = QWidget(); stack = QVBoxLayout(panel)
        text_box=QGroupBox('排版文字（“*”开头：段落底边对齐）'); text_layout=QVBoxLayout(text_box)
        header = QHBoxLayout(); header.addStretch()
        load = QPushButton('载入文本'); load.clicked.connect(self.load_file); header.addWidget(load); text_layout.addLayout(header)
        # 文本框是左侧唯一可扩展区域，取消高度上限以吸收窗口剩余空间。
        self.text.setMinimumHeight(110); self.text.setMaximumHeight(16777215); text_layout.addWidget(self.text, 1)
        stack.addWidget(text_box, 1)
        settings = QGroupBox('参数设置'); settings_layout=QVBoxLayout(settings)
        tabs=QTabWidget(); settings_layout.addWidget(tabs)
        def page(name, items):
            tab=QWidget(); grid=QGridLayout(tab)
            grid.setColumnStretch(1,1); grid.setColumnStretch(3,1)
            for i,(label,control) in enumerate(items):
                row,col=divmod(i,2); col*=2
                lab=QLabel(label); lab.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
                grid.addWidget(lab,row,col)
                control.setMinimumWidth(60); control.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
                grid.addWidget(control,row,col+1)
            tabs.addTab(tab,name)
            return grid
        page('标题', [
            ('字体',self.fonts[1]),('字号',self.title_size),
            ('格高(mm)',self.title_cell_h),('格宽(mm)',self.title_cell_w),
            ('列数',self.title_cols),('行数',self.title_rows),
            ('行距(mm)',self.title_gap_r),('列距(mm)',self.title_gap_c),
            ('文字偏移H(%)',self.title_offset_x),('文字偏移V(%)',self.title_offset_y),
            ('标题缩进(mm)',self.title_top_space),('标题间距(mm)',self.title_body_gap)])
        page('正文', [
            ('字体',self.fonts[0]),('字号',self.fsize),
            ('格高(mm)',self.ch),('格宽(mm)',self.cw),
            ('列数',self.cols),('行数',self.rows),
            ('行距(mm)',self.gap_r),('列距(mm)',self.gap_c),
            ('文字偏移H(%)',self.offset_x),('文字偏移V(%)',self.offset_y)])
        page('尾题', [
            ('字体',self.tail_font),('字号',self.tail_size),
            ('格高(mm)',self.tail_cell_h),('格宽(mm)',self.tail_cell_w),
            ('列数',self.tail_cols),('行数',self.tail_rows),
            ('行距(mm)',self.tail_gap_r),('列距(mm)',self.tail_gap_c),
            ('文字偏移H(%)',self.tail_offset_x),('文字偏移V(%)',self.tail_offset_y),
            ('尾题间距(mm)',self.body_tail_gap)])
        overall=QWidget(); tabs.addTab(overall,'整体')
        grid=QGridLayout(overall)
        items=[
            ('画布 DPI',self.dpi),
            ('分版间距(mm)',self.section_gap),
            ('边框线宽(px)',self.grid_width),('十字线宽(px)',self.cross_width),
            ('大框线宽(px)',self.frame_width)]
        for i,(label,control) in enumerate(items):
            row,col=divmod(i,2); col*=2
            lab=QLabel(label); lab.setAlignment(Qt.AlignRight|Qt.AlignVCenter); grid.addWidget(lab,row,col)
            control.setMinimumWidth(60); control.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed); grid.addWidget(control,row,col+1)
        margins=QGridLayout()
        for i,label in enumerate(('上','下','左','右')):
            lab=QLabel(label); lab.setAlignment(Qt.AlignCenter); margins.addWidget(lab,0,i+1)
        for row,(label,controls) in enumerate((('大框距网格(mm)',self.frames),('画布距网格(mm)',self.margins)),1):
            lab=QLabel(label); lab.setAlignment(Qt.AlignVCenter|Qt.AlignRight); margins.addWidget(lab,row,0)
            for col,control in enumerate(controls,1):
                control.setMinimumWidth(50); margins.addWidget(control,row,col)
        grid.addLayout(margins,3,0,1,4)
        settings.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
        stack.addWidget(settings)
        out=QGroupBox('输出参数'); g=QGridLayout(out)
        g.addWidget(QLabel('输出目录'),0,0); g.addWidget(self.outdir,0,1,1,3)
        choose=QPushButton('选择'); choose.clicked.connect(self.choose_dir); g.addWidget(choose,0,4)
        self.format.clear(); self.format.addItems(['PNG','PSD/PSB','JPG']); self.format.setCurrentText('PSD/PSB')
        g.addWidget(QLabel('文件名'),1,0); g.addWidget(self.filename,1,1); g.addWidget(QLabel('格式'),1,2); g.addWidget(self.format,1,3,1,2)
        save=QPushButton('参数保存'); save.clicked.connect(self.save_settings)
        export=QPushButton('导出'); export.clicked.connect(self.export); export.setMaximumWidth(180)
        g.addWidget(save,2,0,1,2); g.addWidget(export,2,2,1,3)
        out.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        stack.addWidget(out)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(panel); scroll.setMinimumWidth(360)
        self.settings_scroll=scroll
        view=QWidget(); vl=QVBoxLayout(view)
        header=QGridLayout()
        title=QLabel('版面预览'); title.setAlignment(Qt.AlignCenter)
        refresh=QPushButton('刷新预览'); refresh.clicked.connect(self.refresh)
        # 标题在预览区上方居中，刷新按钮与画布左边缘对齐。
        header.addWidget(refresh,0,0,Qt.AlignLeft); header.addWidget(title,0,1)
        options=QWidget(); options_row=QHBoxLayout(options); options_row.setContentsMargins(0,0,0,0)
        options_row.addWidget(self.grid_visible); options_row.addWidget(self.big)
        header.addWidget(options,0,2,Qt.AlignRight)
        side_width=max(refresh.sizeHint().width(),options.sizeHint().width())
        for col in (0,2): header.setColumnMinimumWidth(col,side_width); header.setColumnStretch(col,1)
        header.setColumnStretch(1,1)
        self.grid_visible.toggled.connect(self.update_visibility); self.big.toggled.connect(self.update_visibility)
        vl.addLayout(header)
        self.layout_warning=QLabel(); self.layout_warning.setWordWrap(True); self.layout_warning.setStyleSheet('color: #b04000'); self.layout_warning.hide(); vl.addWidget(self.layout_warning)
        content=QVBoxLayout(); content.addWidget(self.preview,1)
        fit=QPushButton('适应窗口'); fit.clicked.connect(self.fit_preview)
        print_button=QPushButton('打印'); print_button.clicked.connect(self.print_preview)
        fit_row=QGridLayout(); fit_row.setColumnStretch(0,1); fit_row.setColumnStretch(1,1); fit_row.setColumnStretch(2,1)
        fit_row.setColumnMinimumWidth(0,print_button.sizeHint().width()); fit_row.setColumnMinimumWidth(2,print_button.sizeHint().width())
        fit_row.addWidget(fit,0,1,Qt.AlignCenter); fit_row.addWidget(print_button,0,2,Qt.AlignRight)
        content.addLayout(fit_row)
        vl.addLayout(content,1)
        # 文本框是左侧唯一可垂直扩展区域；参数和输出区域保持内容高度。
        stack.setStretch(1, 1); stack.setStretch(2, 0); stack.setStretch(3, 0)
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_splitter=splitter; splitter.addWidget(scroll); splitter.addWidget(view); splitter.setStretchFactor(0,0); splitter.setStretchFactor(1,1)
        self.setCentralWidget(root); old.deleteLater()
        self.setMinimumSize(800,500)
        self.load_settings()
        # 双倍分辨率抗锯齿放大镜，黑白描边适应深浅背景。
        # 不为光标位图写入固定 devicePixelRatio。跨不同 DPI 显示器移动窗口时，
        # Qt 会按当前屏幕自动处理 DPR，固定缓存值会触发 stale DPR 警告。
        pix=QPixmap(64,64); pix.fill(Qt.transparent)
        painter=QPainter(pix); painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor('white'),5,Qt.SolidLine,Qt.RoundCap)); painter.drawLine(19,19,28,28)
        painter.setPen(QPen(QColor('black'),3,Qt.SolidLine,Qt.RoundCap)); painter.drawLine(19,19,28,28)
        painter.setPen(QPen(QColor('white'),3)); painter.setBrush(QColor(255,255,255,210)); painter.drawEllipse(QRectF(3,3,19,19))
        painter.setPen(QPen(QColor('black'),1.5)); painter.drawEllipse(QRectF(3,3,19,19))
        painter.drawLine(8,12,17,12); painter.drawLine(12,8,12,17); painter.end()
        self.zoom_cursor=QCursor(pix,12,12)
        self.preview.alt_pressed=False; self._resize_panels()
        # 启动时预览控件尚未完成布局，set_data 无法计算居中偏移；
        # 在首轮窗口布局完成后再执行一次适应窗口。
        QTimer.singleShot(0, self.fit_preview)
    def _resize_panels(self):
        if not hasattr(self,'main_splitter'): return
        total=max(800,self.width())
        scroll=self.settings_scroll
        left=max(360,scroll.widget().minimumSizeHint().width()+2*scroll.frameWidth()+scroll.verticalScrollBar().sizeHint().width())
        self.main_splitter.setSizes([left,max(300,total-left)])
    def resizeEvent(self,event):
        super().resizeEvent(event); self._resize_panels()
        # 分割器尺寸会在 resizeEvent 返回后才最终确定，延后一轮重新计算居中偏移。
        QTimer.singleShot(0, self.fit_preview)
    def showEvent(self, event):
        super().showEvent(event)
        # showMaximized() 完成后才有最终预览区尺寸，此时重新居中画布。
        QTimer.singleShot(0, self.fit_preview)
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel and isinstance(obj, QAbstractSpinBox):
            return True
        if event.type()==QEvent.KeyPress and event.key()==Qt.Key_Alt:
            self.preview.alt_pressed=True
            self.preview.setCursor(self.zoom_cursor)
            return True
        elif event.type()==QEvent.KeyRelease and event.key()==Qt.Key_Alt:
            self.preview.alt_pressed=False
            self.preview.unsetCursor()
            return True
        elif event.type()==QEvent.ApplicationDeactivate:
            self.preview.alt_pressed=False
            self.preview.unsetCursor()
        elif event.type()==QEvent.Wheel and obj is self.preview:
            # 显式接管预览滚轮，避免 Alt 菜单导航或父级滚动区域吞掉事件。
            self.preview.wheelEvent(event)
            return True
        return super().eventFilter(obj,event)
    def num(self,v,a,b,d):
        # 数值参数使用普通文本框，避免微调箭头和鼠标滚轮误改参数。
        class NumericEdit(QLineEdit):
            def __init__(self, value, integer):
                super().__init__(); self.integer = integer
                validator = QIntValidator(int(a), int(b), self) if integer else QDoubleValidator(a,b,d,self)
                validator.setLocale(QLocale.c())
                if not integer: validator.setNotation(QDoubleValidator.StandardNotation)
                self.setValidator(validator)
                self.setAlignment(Qt.AlignRight)
                self.setValue(value)
                self.editingFinished.connect(self.format_value)
            def value(self):
                if not self.hasAcceptableInput():
                    raise ValueError(f'数值“{self.text()}”无效，请检查范围和小数位数（最多 {d} 位）。')
                return int(self.text()) if self.integer else float(self.text())
            def setValue(self, value):
                self.setText(str(int(value)) if self.integer else f'{float(value):.{d}f}')
            def format_value(self):
                if self.hasAcceptableInput(): self.setValue(self.value())
        return NumericEdit(v, not bool(d))
    def load_file(self):
        fn,_=QFileDialog.getOpenFileName(self,'选择经文文件','','文本文件 (*.txt);;所有文件 (*)')
        if fn:
            self.text.setPlainText(Path(fn).read_text(encoding='utf-8',errors='ignore')); self.refresh()
    def choose_dir(self):
        d=QFileDialog.getExistingDirectory(self,'选择输出目录');
        if d: self.outdir.setText(d)
    def settings_path(self): return Path.cwd() / '参数设置.json'
    def settings_data(self):
        data={key:control.value() for key,control in self.controls.items()}
        data.update(settings_version=SETTINGS_VERSION,text=self.text.toPlainText(),
                    big=self.big.isChecked(),grid_visible=self.grid_visible.isChecked(),
                    frames=[c.value() for c in self.frames],margins=[c.value() for c in self.margins],
                    font=self.fonts[0].currentData() or self.fonts[0].currentText(),
                    title_font=self.fonts[1].currentData() or self.fonts[1].currentText(),
                    tail_font=self.fonts[2].currentData() or self.fonts[2].currentText(),
                    outdir=self.outdir.text(),filename=self.filename.text(),format=self.format.currentText())
        return data
    def save_settings(self):
        try:
            data=self.settings_data()
            self.settings_path().write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        except (ValueError,OSError) as exc:
            QMessageBox.warning(self,'参数保存失败',str(exc)); return
        QMessageBox.information(self,'参数保存','参数已保存到参数设置.json')
    def load_settings(self):
        try:
            path=self.settings_path()
            data=migrate_settings(json.loads(path.read_text(encoding='utf-8'))) if path.exists() else dict(BUILTIN_SETTINGS)
        except (ValueError,OSError) as exc:
            logging.warning('参数设置加载失败，使用内置默认值：%s',exc)
            data=dict(BUILTIN_SETTINGS)
        d=dict(BUILTIN_SETTINGS); d.update(data)
        self.text.setPlainText(d['text'])
        for key,control in self.controls.items(): control.setValue(d[key])
        self.big.setChecked(d['big']); self.grid_visible.setChecked(d['grid_visible'])
        for controls,key in ((self.frames,'frames'),(self.margins,'margins')):
            for control,value in zip(controls,d[key]): control.setValue(value)
        for combo,key in ((self.fonts[0],'font'),(self.fonts[1],'title_font'),(self.fonts[2],'tail_font')):
            target=d[key]; index=combo.findData(target)
            if index < 0: index=combo.findText(target)
            if index >= 0: combo.setCurrentIndex(index)
        self.outdir.setText(os.path.expandvars(d['outdir']))
        self.filename.setText(d['filename']); self.format.setCurrentText(d['format'])
        self.refresh()
    def values(self):
        d=self.settings_data()
        mt,mb,ml,mr=d['margins']; ft,fb,fl,fr=d['frames']
        d.update(margin_t=mt,margin_b=mb,margin_l=ml,margin_r=mr,
                 frame_t=ft,frame_b=fb,frame_l=fl,frame_r=fr,
                 big_frame=d['big'],text_offset_x=d['offset_x'],text_offset_y=d['offset_y'],
                 title_text_offset_x=d['title_offset_x'],title_text_offset_y=d['title_offset_y'],
                 title_font_size=d['title_size'],tail_font_size=d['tail_size'],
                 tail_text_offset_x=d['tail_offset_x'],tail_text_offset_y=d['tail_offset_y'])
        return complete_params(d, self.text.toPlainText())
    def output_data(self):
        try:
            params=self.values(); text=self.text.toPlainText()
            _,warnings=place_text(params,text)
            if warnings: raise ValueError('\n'.join(warnings))
            return params,text
        except ValueError as exc:
            QMessageBox.warning(self,'请检查排版参数',str(exc))
            return None
    def set_zoom(self,z): self.preview.zoom=max(.05,z); self.preview.update()
    def fit_preview(self):
        self.preview.zoom=1.0; p=self.preview.params
        if p and self.preview.width()>0:
            fit=min((self.preview.width()-30)/max(1,p['canvas_w']*MM),(self.preview.height()-30)/max(1,p['canvas_h']*MM))
            self.preview.pan=QPointF(((self.preview.width()-30)-p['canvas_w']*MM*fit)/2,((self.preview.height()-30)-p['canvas_h']*MM*fit)/2)
        else: self.preview.pan=QPointF(0,0)
        self.preview.update()
    def update_visibility(self):
        self.preview.params['grid_visible'] = self.grid_visible.isChecked()
        self.preview.params['big_frame'] = self.big.isChecked()
        self.preview.update()
    def print_preview(self):
        data=self.output_data()
        if data is None: return
        printer = QPrinter(QPrinter.HighResolution)
        default_printer = QPrinterInfo.defaultPrinter()
        if default_printer.isNull():
            QMessageBox.warning(self, '打印', '系统没有可用的本地打印机。')
            return
        printer.setOutputFormat(QPrinter.NativeFormat)
        printer.setPrinterName(default_printer.printerName())
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.Accepted:
            return
        image = render_layout_image(*data)
        painter = QPainter(printer)
        page = printer.pageRect(QPrinter.DevicePixel)
        scale=min(page.width()/image.width(),page.height()/image.height())
        w,h=image.width()*scale,image.height()*scale
        target=QRectF(page.left()+(page.width()-w)/2,page.top()+(page.height()-h)/2,w,h)
        painter.drawImage(target,image)
        painter.end()
    def refresh(self):
        try:
            params=self.values(); text=self.text.toPlainText()
            self.preview.set_data(params,text)
            _,warnings=place_text(params,text)
            self.layout_warning.setText('\n'.join(warnings)); self.layout_warning.setVisible(bool(warnings))
        except ValueError as exc:
            self.layout_warning.setText(str(exc)); self.layout_warning.show()

    def export(self):
        data=self.output_data()
        if data is None: return
        v,text=data
        started=time.perf_counter()
        progress=QProgressDialog('正在导出…','取消',0,100,self); progress.setWindowTitle('导出进度'); progress.setWindowModality(Qt.WindowModal); progress.setAutoClose(False); progress.show(); QApplication.processEvents()
        logging.info('开始导出 format=%s dpi=%s canvas_mm=%.1fx%.1f',self.format.currentText(),v['dpi'],v['canvas_w'],v['canvas_h']); progress.setValue(10); QApplication.processEvents(); logging.info('参数准备 %.3fs',time.perf_counter()-started)
        iw,ih=2400,max(600,round(2400*v['canvas_h']/v['canvas_w'])); logging.info('创建导出画布 %sx%s 像素',iw,ih); img=QImage(1,1,QImage.Format_ARGB32); img.fill('white'); progress.setValue(35); QApplication.processEvents(); logging.info('画布准备 %.3fs',time.perf_counter()-started)
        # 导出时只绘制预览画布区域，避免重复渲染整个窗口导致超长阻塞
        self.preview.set_data(v,text); QApplication.processEvents()
        # 在独立的等比例画布尺寸上重绘整幅版面，避免导出当前视口的局部内容。
        img = render_layout_image(v, text) if self.format.currentText() in ('PNG', 'JPG') else None
        progress.setValue(15); progress.setLabelText('正在准备完整画布…'); QApplication.processEvents(); logging.info('版面渲染 %.3fs',time.perf_counter()-started)
        os.makedirs(self.outdir.text(),exist_ok=True); ext='psd' if self.format.currentText() == 'PSD/PSB' else self.format.currentText().lower(); path=Path(self.outdir.text())/(self.filename.text()+'.'+ext)
        output_path = path
        if ext in ('png', 'jpg'):
            # PNG 的 quality=95 在 Qt 中会造成几乎不压缩；使用默认无损压缩。
            saved = img.save(str(path), 'PNG') if ext == 'png' else img.save(str(path), 'JPG', 95)
            if not saved: raise OSError('图片写入失败')
        else:
            output_path = export_layered_psd(v, text, path, True, progress)

        logging.info('文件写入完成 %.3fs path=%s total=%.3fs',time.perf_counter()-started,output_path,time.perf_counter()-started); progress.setValue(100); progress.close(); QMessageBox.information(self,'导出完成',f'已输出：{output_path}\n耗时：{time.perf_counter()-started:.1f} 秒')

if __name__=='__main__':
        app=QApplication(sys.argv); w=MainWindow(); w.showMaximized(); sys.exit(app.exec())
