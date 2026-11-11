import os, sys, re, time, logging, json
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QPointF, QEvent, QTimer
from PySide6.QtGui import QFontDatabase, QImage, QPainter, QPen, QColor, QFont, QCursor, QPixmap, QTextCursor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFormLayout, QLabel, QPushButton, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QFileDialog, QLineEdit, QScrollArea, QMessageBox, QGroupBox, QProgressDialog, QGridLayout, QSplitter, QSizePolicy, QAbstractSpinBox)
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrinterInfo

MM = 300 / 25.4
logging.basicConfig(filename='export.log', level=logging.INFO, format='%(asctime)s %(message)s', encoding='utf-8')

# 内置默认参数。首次运行且外部参数设置文件不存在时使用；用户点击“参数保存”
# 后仍会优先读取工作目录中的参数设置.json。
BUILTIN_SETTINGS = {
    'text': '\u3000序言\u3000\n佛法東漸時輪轉動華夏大地照進一縷新的覺悟之光中華文明注入一股新的智慧源泉歷代中外高僧大德篳路藍縷辛苦遭逢白馬馱經而來西行求法而去歷經千年心無疲厭殫精竭慮嘔心瀝血將佛法大小顯密各類經典移譯華夏日益完備裨使華夏總持佛典之全部總集佛法之大成\n然世事無常人間滄桑中國第一個佛教宗派天台宗宗祖南嶽慧思大師生逢身處動蕩分裂的南北朝深體正法住世之不易遂作立誓願文發願持令佛法不滅正法久住又誓願造金字佛經以期法寶不失法輪常轉\n華夏石刻肇自上古先民勒石記事銘功周秦碑碣漢魏摩崖歷六朝而趨盛經唐宋而達巔峰佛法初傳三寶漸全漢魏兩晉石窟營造佛像勒石鐫刻佛經即已發端南北朝際佛法漸趨隆盛刻經蔚然成風泰山金剛經摩崖石刻徂徠摩訶般若經文殊般若經石刻已成大觀\n慧思大師弟子隋靜琬上人承蒙師教以師志為己志學宗親師造金字佛經之精神借鏡已有石刻佛經之經驗發心將眾經大藏刻於石上以期佛說法藏經典長存不滅佛教法身慧命持久永續遂於隋大業年間於今北京房山地區鑿石室刻石經持續卅載直至圓寂刻成經石一百四十六塊計佛經十二部其後靜琬上人開創的刻經事業歷經唐宋遼金元明清千年續刻成為世界上規模最大歷史最久的石刻佛教大藏經共刻佛經千餘部三千餘卷石經版一萬五千餘塊總字數超三千五百多萬字是即北京房山石經誠為佛典之善品華夏之至寶清乾隆帝譽為千年法藏當代趙樸初大德贊為文化長城\n今欣聞家鄉浙江紹興上虞多寶講寺以校勘精審之房山石經善本為主要底本發心聚力歷時數年鐫刻雜阿含經小品般若經大品般若經金剛經心經解深密經法華經觀世音菩薩普門品楞嚴經觀世音菩薩耳根圓通章楞嚴咒大悲咒中論攝大乘論等經論密咒於金石之上成經版三百九十一塊凡五十七萬字講寺勒刻經典顯揚法義其心之誠其力之猛與先賢一脈相承一以貫之與古德同心同德同願同行深為震撼無比讚歎\n多寶講寺此次所選刻之經典選取大藏各部類精華涵蓋了阿含般若中觀法相唯識佛性如來藏密咒等大小顯密全體佛法乃大藏之精華和縮影尤以般若中觀類經典為主體般若乃全體佛法特別是大乘佛法之綱要樞紐與核心般若被稱為諸佛之母一切眾生之祖母大品般若曰摩訶般若波羅蜜是諸菩薩摩訶薩母能生諸佛攝持菩薩心經亦云三世諸佛依般若波羅蜜多故得阿耨多羅三藐三菩提究實而言佛陀在菩提樹下悟道就是以般若正智即通達一切法真如實性之無分別智觀照諸法實相證入真如實際開般若正智即開佛知見能見般若即為見佛\n講寺師祖海公上人一生持戒精嚴特重般若晚年深弘阿含講寺開山敏公上人繼以持戒為本更以弘揚般若為要務兼弘唯識俱舍又結合漢傳圓教大旨深契佛教中國化之精髓盡顯佛門大乘精神之內涵現任住持紹隆師門宗風引領大眾嚴守佛制戒律廣學般若奧義精勤修行護國利民令多寶清淨道場住持正法聞名於世可欽可贊今又發心效仿先德刻經於金石之上以期法寶永續法輪常轉實乃皆大歡喜之盛事吾人樂觀其成並期未來因緣具足之時刻經不斷增廣乃至蔚成一大藏存世永年恒護正法廣利群生\u3000樓宇烈謹識\n\n*佛暦二千五百七十年四月初四\u3000\n*農暦丙午年四月初四\u3000\u3000\u3000\u3000\u3000\n*西暦二千零廿六年五月廿日\u3000\u3000\n*文殊菩薩聖誕日於京西三不堂\u3000', 'dpi': 300, 'cell_h': 45.0, 'cell_w': 50.0, 'cols': 46,
    'rows': 31, 'gap_r': 0.0, 'gap_c': 0.0, 'big': True, 'grid_visible': True,
    'scheme': 0, 'grid_width': 5, 'cross_width': 2, 'frame_width': 10,
    'offset_x': 0.0, 'offset_y': 5.0, 'frames': [50.0]*4,
    'margins': [200.0]*4, 'font': 'FZWeiBei-S03', 'title_font': 'FZWeiBei-S03',
    'font_size': 120, 'title_size': 200, 'outdir': '%userprofile%\\Desktop',
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

def layout_body(paragraphs, rows, columns, capacities=None):
    """空格与文字统一占位，到列底立即换列，避免空格使行号越界。"""
    tokens = []
    r = c = 0
    for paragraph in paragraphs:
        if paragraph == '':
            c += 1
            r = 0
            continue
        bottom = paragraph.startswith('*')
        paragraph = paragraph[1:] if bottom else paragraph
        capacity = capacities[c] if capacities and c < len(capacities) else rows
        if bottom:
            length = len(paragraph.replace('\n', ''))
            r = (capacity - length % capacity) % capacity
        for char in paragraph:
            if char == '\n':
                if r:
                    c += 1
                    r = 0
                continue
            if c >= columns:
                break
            if char not in (' ', '\u3000'):
                tokens.append((r, c, char))
            r += 1
            if r == capacity:
                c += 1
                r = 0
                capacity = capacities[c] if capacities and c < len(capacities) else rows
        if r:
            c += 1
            r = 0
    return tokens

class Preview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.params = {}; self.text = ""; self.zoom = 1.0; self.pan = QPointF(0, 0); self.drag_pos = None; self.setMinimumSize(200, 200); self.setMouseTracking(True)
    def set_data(self, params, text):
        self.params, self.text = params, text
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
        dpi = self.params['dpi']; scale = dpi / 300 if export else min((width-30)/max(1,self.params['canvas_w']*MM), (height-30)/max(1,self.params['canvas_h']*MM)) * self.zoom
        ox, oy = (0, 0) if export else (15 + self.pan.x(), 15 + self.pan.y()); cw, ch = self.params['cell_w']*MM*scale, self.params['cell_h']*MM*scale
        cols, rows = self.params['cols'], self.params['rows']; grid_pen=QPen(QColor('#FF0000') if self.params.get('grid_visible', True) else QColor(Qt.transparent), float(self.params.get('grid_width', 1)) * (1 if export else scale * 300 / dpi)); grid_pen.setStyle(Qt.SolidLine); p.setPen(grid_pen)
        p.fillRect(QRectF(ox, oy, self.params['canvas_w']*MM*scale, self.params['canvas_h']*MM*scale), QColor('white'))
        left = ox + self.params['margin_l']*MM*scale; top = oy + self.params['margin_t']*MM*scale
        # 普通列：右向左排列；最右列单元格为 2×2 标准单元格大小
        for r in range(rows):
            for c in range(cols - 2):
                visual_c = cols - 3 - c; x = left + visual_c*cw; y = top + r*ch; w = cw
                p.drawRect(QRectF(x, y, w, ch))
                dash=QPen(QColor('#FF0000') if self.params.get('grid_visible', True) else QColor(Qt.transparent), float(self.params.get('cross_width', 1)) * (1 if export else scale * 300 / dpi)); dash.setDashPattern([max(2.0, 8*scale), max(2.0, 5*scale)]); p.setPen(dash); p.drawLine(x+w/2, y, x+w/2, y+ch); p.drawLine(x, y+ch/2, x+w, y+ch/2); p.setPen(grid_pen)
        scheme = self.params.get('scheme', 1)
        first_x = left + (cols-2)*cw
        start_y = top if scheme == 2 else top + (rows % 2)*ch
        title_count = max(1, len(self.text.splitlines()[0]) if self.text else 1) if scheme == 2 else rows // 2
        # 方案二标题区只按标题文字数量绘制大田字格，不再额外追加空格。
        big_count = min(rows // 2, title_count)
        for r in range(0, big_count * 2, 2):
            y = start_y + r*ch; w = cw*2; h = ch*2
            p.drawRect(QRectF(first_x, y, w, h))
            dash=QPen(QColor('#FF0000') if self.params.get('grid_visible', True) else QColor(Qt.transparent), float(self.params.get('cross_width', 1)) * (1 if export else scale * 300 / dpi)); dash.setDashPattern([max(2.0, 8*scale), max(2.0, 5*scale)]); p.setPen(dash); p.drawLine(first_x+w/2, y, first_x+w/2, y+h); p.drawLine(first_x, y+h/2, first_x+w, y+h/2); p.setPen(grid_pen)
        if scheme == 2:
            for rr in range(big_count * 2, rows):
                for sub in range(2):
                    x = first_x + (1 - sub) * cw; y = top + rr * ch
                    p.drawRect(QRectF(x, y, cw, ch))
                    dash=QPen(QColor('#FF0000') if self.params.get('grid_visible', True) else QColor(Qt.transparent), float(self.params.get('cross_width', 1)) * (1 if export else scale * 300 / dpi)); dash.setDashPattern([max(2.0, 8*scale), max(2.0, 5*scale)]); p.setPen(dash); p.drawLine(x+cw/2,y,x+cw/2,y+ch); p.drawLine(x,y+ch/2,x+cw,y+ch/2); p.setPen(grid_pen)
        font = QFont(self.params['font']); font.setPixelSize(max(1, round(self.params['font_size']*300/72*scale))); p.setFont(font); p.setPen(QColor('#111'))
        raw = self.text.rstrip('\r\n')
        if raw:
            lines = raw.splitlines()
            title_line = lines[0]
            # 每个换行分隔一个段落，保留空段以占用一个空白列。
            paragraphs = [title_line] + lines[1:]
        else:
            paragraphs = []
        title_text = paragraphs[0] if paragraphs else ''
        formal = paragraphs[1:]
        if scheme == 2:
            body_rows = rows - big_count * 2
            capacities = ([body_rows, body_rows] if body_rows else []) + [rows]*(cols-2)
            placed = layout_body(formal, rows, len(capacities), capacities)
            tokens = []
            for r, c, chv in placed:
                if body_rows and c < 2:
                    tokens.append((r + big_count*2, cols-1-c, chv))
                else:
                    tokens.append((r, c-(2 if body_rows else 0), chv))
        else:
            tokens = layout_body(formal, rows, cols-2)
        # 标题写入最右侧 2×2 单元格
        title_chars = [x for x in title_text if x not in ('\r', '\n')]
        for i, chv in enumerate(title_chars[:rows//2]):
            if chv in (' ', '\u3000'): continue
            tr = i * 2
            if tr >= rows: break
            tokens.append((tr, cols-1, chv))
        geometry = []
        for r, c, chv in tokens:
            if c == cols - 1 and not (scheme == 2 and r >= big_count * 2):
                x, y, ww, hh = first_x, start_y + (r//2)*2*ch, cw*2, ch*2
            elif scheme == 2 and c in (cols - 1, cols - 2) and r >= big_count * 2:
                x, y, ww, hh = first_x + (c - (cols - 2)) * cw, top + r*ch, cw, ch
            else:
                x, y, ww, hh = left + (cols-3-c)*cw, top + r*ch, cw, ch
            if c == cols - 1 and not (scheme == 2 and r >= big_count * 2):
                tf = QFont(self.params.get('title_font', self.params['font'])); tf.setPixelSize(max(1, round(self.params.get('title_font_size', self.params['font_size'])*300/72*scale))); p.setFont(tf)
            else:
                p.setFont(font)
            geometry.append((x, y, ww, hh, c == cols-1 and not (scheme == 2 and r >= big_count*2)))
            dx = ww * float(self.params.get('text_offset_x', 0)) / 100
            dy = hh * float(self.params.get('text_offset_y', 0)) / 100
            p.drawText(QRectF(x + dx, y + dy, ww, hh), Qt.AlignCenter, chv)
        self.text_tokens = tokens
        self.text_geometry = geometry
        if self.params['big_frame']:
            p.setPen(QPen(QColor('#FF0000'), float(self.params.get('frame_width', 1)) * (1 if export else scale * 300 / dpi))); p.drawRect(QRectF(left-self.params['frame_l']*MM*scale, top-self.params['frame_t']*MM*scale, cols*cw+self.params['frame_l']*MM*scale+self.params['frame_r']*MM*scale, rows*ch+self.params['frame_t']*MM*scale+self.params['frame_b']*MM*scale))
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

def render_layout_image(params, text, width=None):
    """独立导出渲染器，不读取当前预览窗口的缩放或平移状态。"""
    width=round(params['canvas_w']*params['dpi']/25.4)
    height=round(params['canvas_h']*params['dpi']/25.4)
    widget=Preview(); widget.set_data(params,text)
    image=QImage(width,height,QImage.Format_RGB32); image.fill(QColor('white'))
    if image.isNull(): raise MemoryError('无法分配完整输出画布')
    image.setDotsPerMeterX(round(params['dpi']/0.0254)); image.setDotsPerMeterY(round(params['dpi']/0.0254))
    painter=QPainter(image); widget.draw_layout(painter,width,height,export=True); painter.end()
    return image

def export_layered_psd(params, text, path, compressed, progress):
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
    grid = render_layout_image(params, '')
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
    document.create_pixel_layer(grid_pil, name='网格与框', compression=compression)
    groups = {}
    del grid, grid_pil
    layout = Preview(); layout.set_data(params, text)
    probe = QImage(1,1,QImage.Format_ARGB32); painter = QPainter(probe)
    layout.draw_layout(painter,width,height,export=True); painter.end()
    tokens = layout.text_tokens
    factor = params['dpi']/25.4
    cw, ch = params['cell_w']*factor, params['cell_h']*factor
    left, top = params['margin_l']*factor, params['margin_t']*factor
    total_layers=len(tokens)
    for index, (row, column, char) in enumerate(tokens):
        x, y, w, h, title = layout.text_geometry[index]
        x += w * params.get('text_offset_x', 0) / 100
        y += h * params.get('text_offset_y', 0) / 100
        tile = QImage(round(w),round(h),QImage.Format_ARGB32); tile.fill(Qt.transparent)
        painter = QPainter(tile)
        font = QFont(params['title_font'] if title else params['font'])
        font.setPixelSize(round(params['title_font_size' if title else 'font_size']*params['dpi']/72))
        painter.setFont(font); painter.setPen(QColor('black'))
        painter.drawText(QRectF(0,0,w,h),Qt.AlignCenter,char); painter.end()
        pil = Image.frombuffer('RGBA', (tile.width(),tile.height()), bytes(tile.bits()), 'raw','BGRA',0,1)
        if title:
            group_number = 1 if params.get('scheme', 1) == 1 else 0
            row_number = row // 2 + 1
        else:
            group_number = column + (3 if params.get('scheme', 1) == 1 else 1)
            # 方案二的正文列组号按实际阅读方向连续编号：旧组 46、45、1、2……
            # 分别变为 1、2、3、4……；方案一保留标题组 1、跳过组 2、正文从 3 开始。
            if params.get('scheme', 1) == 2:
                # 默认 46 列时：46→1、45→2、1→3、2→4；使用列数计算，
                # 避免修改列数后仍被固定常量 45/46 影响。
                column_count = int(params.get('cols', 46))
                group_number = (column_count + 1 - group_number
                                if group_number >= column_count - 1
                                else group_number + 2)
            row_number = row + 1
        group = groups.get(group_number)
        if group is None:
            group = document.create_group(name=str(group_number), open_folder=False)
            groups[group_number] = group
        name = f"{group_number}.{row_number}.{char}"
        # 文字透明度直接存于像素 Alpha 通道，不创建图层蒙版。
        text_layer = group.create_pixel_layer(pil,name=name,left=round(x),top=round(y),compression=compression)
        if text_layer.has_mask():
            raise RuntimeError(f'文字图层意外包含蒙版：{name}')
        if index % 5 == 0:
            progress.setLabelText(f'正在创建文字图层 {index+1}/{total_layers}')
            progress.setValue(50+round(35*(index+1)/max(1,total_layers)))
            QApplication.processEvents()
    # 组与组内图层按编号升序排列，纯白背景固定在最底层。
    grid_layer = next(layer for layer in document if layer.name == '网格与框')
    text_groups = sorted(groups.values(), key=lambda g: int(g.name))
    for group in text_groups:
        group._layers.sort(key=lambda layer: int(layer.name.split('.', 2)[1]))
    white = Image.new('RGBA', (width, height), (255,255,255,255))
    white_layer = document.create_pixel_layer(white, name='纯白', compression=compression)
    # 组对象建立后，psd-tools 已经把底层 layer records 按建立顺序串起来；
    # 仅修改 ``_layers`` 不会改变写盘顺序。显式重排 records（以及对应的
    # channel data），保证 Photoshop 面板从上到下为组号递增、网格与框、纯白。
    info = document._record.layer_and_mask_information.layer_info
    records, channels = info.layer_records, info.channel_image_data
    chunks = {}
    for group in text_groups:
        opening = next(i for i, rec in enumerate(records) if rec.name == group.name)
        closing = next(i for i in range(opening - 1, -1, -1) if records[i].name == '</Layer group>')
        # Photoshop 对组内记录也是反向显示；将字符记录倒置后，
        # 面板中即可按行号从上到下显示 1、2、3……。
        children = list(range(closing + 1, opening))
        chunks[group.name] = [closing] + list(reversed(children)) + [opening]
    used = {i for ids in chunks.values() for i in ids}
    grid_i = next(i for i, rec in enumerate(records) if rec.name == grid_layer.name)
    white_i = next(i for i, rec in enumerate(records) if rec.name == white_layer.name)
    # Photoshop 面板显示顺序与底层记录顺序相反，因此记录按目标面板顺序倒置写入：
    # 纯白记录放在首端，随后是网格层，再按组号递减写入文字组。
    order = [white_i, grid_i] + [i for g in reversed(text_groups) for i in chunks[g.name]]
    order += [i for i in range(len(records)) if i not in used and i not in (grid_i, white_i)]
    records_reordered = [records[i] for i in order]
    records[:] = records_reordered
    # ChannelImageData 是带有内部长度表的 list 子类，必须原地重排，
    # 否则写盘时无法更新每个图层的通道长度。
    reordered_channels = [channels[i] for i in order]
    channel_lengths = list(channels._lengths)
    channels[:] = reordered_channels
    channels._lengths[:] = [channel_lengths[i] for i in order]
    document._layers[:] = list(text_groups) + [grid_layer, white_layer]
    document._updated = False
    progress.setLabelText('正在写入分层文件…'); QApplication.processEvents()
    document.save(str(path),encoding='gb18030',compression=compression)
    logging.info('分层输出完成：%s，文字层=%s，总图层=%s',path,len(tokens),len(document))
    return path

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('经文排版程序'); self.resize(1500, 900)
        root=QWidget(); self.setCentralWidget(root); layout=QHBoxLayout(root)
        left=QVBoxLayout(); mid=QVBoxLayout(); right=QVBoxLayout(); layout.addLayout(left,2); layout.addLayout(mid,4); layout.addLayout(right,2)
        self.text=WhitespaceTextEdit(); left.addWidget(QLabel('经文文字')); left.addWidget(self.text,1)
        load=QPushButton('载入经文文件'); load.clicked.connect(self.load_file); left.addWidget(load)
        fg=QGroupBox('字体设置'); ff=QFormLayout(fg); self.fonts=[]
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
        cb=QComboBox(); families=QFontDatabase.families(); cb.addItems(families); preferred='方正魏碑_GBK'; fallback='Arial'; cb.setCurrentText(preferred if preferred in families else fallback); self.fonts.append(cb); ff.addRow('经文字体',cb)
        cb_title=QComboBox(); cb_title.addItems(families); cb_title.setCurrentText(preferred if preferred in families else fallback); self.fonts.append(cb_title); ff.addRow('标题字体',cb_title)
        if hasattr(self, 'default_font_family'):
            for combo in self.fonts:
                combo.addItem('方正魏碑_GBK', self.default_font_family)
                combo.setCurrentIndex(combo.count()-1)
        self.fsize=QSpinBox(); self.fsize.setRange(6,500); self.fsize.setValue(120); ff.addRow('经文大小',self.fsize)
        self.title_size=QSpinBox(); self.title_size.setRange(6,800); self.title_size.setValue(240); ff.addRow('标题大小',self.title_size)
        left.addWidget(fg)
        title=QLabel('版面预览'); title.setAlignment(Qt.AlignCenter); mid.addWidget(title); self.preview=Preview(); mid.addWidget(self.preview,1); tools=QHBoxLayout(); refresh=QPushButton('刷新预览'); refresh.clicked.connect(self.refresh); minus=QPushButton('−'); plus=QPushButton('＋'); fit=QPushButton('适应窗口'); minus.clicked.connect(lambda: self.set_zoom(self.preview.zoom/1.2)); plus.clicked.connect(lambda: self.set_zoom(self.preview.zoom*1.2)); fit.clicked.connect(self.fit_preview); [tools.addWidget(x) for x in (minus,plus,fit,refresh)]; mid.addLayout(tools)
        box=QGroupBox('排版参数'); form=QFormLayout(box)
        self.dpi=self.num(300,72,1200,0); self.ch=self.num(45,1,500,1); self.cw=self.num(50,1,500,1); self.cols=self.num(46,1,200,0); self.rows=self.num(31,1,200,0); self.gap_r=self.num(0,0,100,1); self.gap_c=self.num(0,0,100,1)
        for lab,w in [('画布 DPI',self.dpi),('单元格高(mm)',self.ch),('单元格宽(mm)',self.cw),('列数',self.cols),('行数',self.rows),('行间距(mm)',self.gap_r),('列间距(mm)',self.gap_c)]: form.addRow(lab,w)
        self.big=QCheckBox('绘制大框'); self.big.setChecked(True); form.addRow(self.big)
        self.scheme=QComboBox(); self.scheme.addItems(['方案一：首列大田字格','方案二：紧凑标题列']); form.addRow('排版方案',self.scheme)
        self.grid_width=self.num(1,1,100,0); form.addRow('田字格边框线宽(px)',self.grid_width)
        self.cross_width=self.num(1,1,100,0); form.addRow('十字线宽(px)',self.cross_width)
        self.frame_width=self.num(1,1,100,0); form.addRow('大框线宽(px)',self.frame_width)
        self.offset_x=self.num(0,-100,100,1); form.addRow('文字水平偏移(%)',self.offset_x)
        self.offset_y=self.num(0,-100,100,1); form.addRow('文字垂直偏移(%)',self.offset_y)
        self.frames=[]
        for lab in ('大框上边距(mm)','大框下边距(mm)','大框左边距(mm)','大框右边距(mm)'):
            w=self.num(50,0,1000,1); self.frames.append(w); form.addRow(lab,w)
        self.margins=[]
        for lab,val in (('画布上边距(mm)',230),('画布下边距(mm)',230),('画布左边距(mm)',230),('画布右边距(mm)',230)):
            w=self.num(val,0,2000,1); self.margins.append(w); form.addRow(lab,w)
        right.addWidget(box)
        out=QGroupBox('输出参数'); of=QFormLayout(out); self.outdir=QLineEdit(str(Path.cwd()/'output')); b=QPushButton('选择'); b.clicked.connect(self.choose_dir); row=QHBoxLayout(); row.addWidget(self.outdir); row.addWidget(b); of.addRow('输出目录',row); self.filename=QLineEdit('经文排版'); of.addRow('文件名',self.filename); self.format=QComboBox(); self.format.addItems(['PNG','PSD']); self.format.setCurrentText('PSD'); of.addRow('文件格式',self.format); self.compress=QCheckBox('PSD 压缩'); self.compress.setChecked(True); of.addRow(self.compress); exp=QPushButton('导出'); exp.clicked.connect(self.export); of.addRow(exp); right.addWidget(out); right.addStretch(); self.rebuild_ui(); QApplication.instance().installEventFilter(self); self.refresh()
    def rebuild_ui(self):
        old = self.centralWidget()
        root = QWidget(); outer = QHBoxLayout(root)
        splitter = QSplitter(Qt.Horizontal); outer.addWidget(splitter)
        panel = QWidget(); stack = QVBoxLayout(panel)
        header = QHBoxLayout(); header.addWidget(QLabel('排版文字（“*”开头：段落底边对齐）')); header.addStretch()
        load = QPushButton('载入文本'); load.clicked.connect(self.load_file); header.addWidget(load); stack.addLayout(header)
        # 文本框是左侧唯一可扩展区域，取消高度上限以吸收窗口剩余空间。
        self.text.setMinimumHeight(110); self.text.setMaximumHeight(16777215); stack.addWidget(self.text, 1)
        settings = QGroupBox('参数设置'); grid = QGridLayout(settings)
        grid.setColumnStretch(1, 1); grid.setColumnStretch(3, 1)
        def pair(row, label, control, col=0):
            grid.addWidget(QLabel(label), row, col)
            control.setMinimumWidth(65); control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            grid.addWidget(control, row, col+1)
        pair(0,'排版方案',self.scheme); pair(0,'画布 DPI',self.dpi,2)
        pair(1,'经文字体',self.fonts[0]); pair(1,'字号',self.fsize,2)
        pair(2,'标题字体',self.fonts[1]); pair(2,'字号',self.title_size,2)
        pair(3,'水平偏移(%)',self.offset_x); pair(3,'垂直偏移(%)',self.offset_y,2)
        items=[('列数',self.cols),('格高(mm)',self.ch),('行数',self.rows),('格宽(mm)',self.cw),('行距(mm)',self.gap_r),('列距(mm)',self.gap_c),('边框线宽(px)',self.grid_width),('十字线宽(px)',self.cross_width),('大框线宽(px)',self.frame_width)]
        for i,(label,control) in enumerate(items): pair(4+i//2,label,control,(i%2)*2)
        margins=QGridLayout()
        for i,label in enumerate(('上','下','左','右')):
            header_label=QLabel(label); header_label.setAlignment(Qt.AlignCenter); margins.addWidget(header_label,0,i+1)
        for row,(label,controls) in enumerate((('大框距单元格(mm)',self.frames),('画布距单元格(mm)',self.margins)),1):
            row_label=QLabel(label); row_label.setAlignment(Qt.AlignVCenter|Qt.AlignRight); margins.addWidget(row_label,row,0)
            for col,control in enumerate(controls,1): control.setMinimumWidth(60); margins.addWidget(control,row,col)
        grid.addLayout(margins,9,0,1,4)
        settings.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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
        view=QWidget(); vl=QVBoxLayout(view)
        header=QHBoxLayout()
        title=QLabel('版面预览'); title.setAlignment(Qt.AlignCenter)
        refresh=QPushButton('刷新预览'); refresh.clicked.connect(self.refresh)
        # 标题在预览区上方居中，刷新按钮与画布左边缘对齐。
        header.addWidget(refresh); header.addStretch(); header.addWidget(title); header.addStretch()
        self.big.setText('大框'); self.grid_visible=QCheckBox('田字格'); self.grid_visible.setChecked(True)
        header.addWidget(self.grid_visible); header.addWidget(self.big)
        self.grid_visible.toggled.connect(self.update_visibility); self.big.toggled.connect(self.update_visibility)
        vl.addLayout(header)
        content=QVBoxLayout(); content.addWidget(self.preview,1)
        fit=QPushButton('适应窗口'); fit.clicked.connect(self.fit_preview)
        print_button=QPushButton('打印'); print_button.clicked.connect(self.print_preview)
        fit_row=QHBoxLayout(); fit_row.addStretch(); fit_row.addWidget(fit); fit_row.addStretch(); fit_row.addWidget(print_button)
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
        total=max(800,self.width()); left=max(360,min(500,round(total*0.27)))
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
                super().__init__(str(value)); self.integer = integer
                self.setAlignment(Qt.AlignRight)
            def value(self):
                try:
                    return int(float(self.text())) if self.integer else float(self.text())
                except (TypeError, ValueError):
                    return 0 if self.integer else 0.0
            def setValue(self, value): self.setText(str(int(value) if self.integer else value))
        return NumericEdit(v, not bool(d))
    def load_file(self):
        fn,_=QFileDialog.getOpenFileName(self,'选择经文文件','','文本文件 (*.txt);;所有文件 (*)')
        if fn:
            self.text.setPlainText(Path(fn).read_text(encoding='utf-8',errors='ignore')); self.refresh()
    def choose_dir(self):
        d=QFileDialog.getExistingDirectory(self,'选择输出目录');
        if d: self.outdir.setText(d)
    def settings_path(self): return Path.cwd() / '参数设置.json'
    def save_settings(self):
        data={'text':self.text.toPlainText(),'dpi':self.dpi.value(),'cell_h':self.ch.value(),'cell_w':self.cw.value(),'cols':self.cols.value(),'rows':self.rows.value(),'gap_r':self.gap_r.value(),'gap_c':self.gap_c.value(),'big':self.big.isChecked(),'grid_visible':self.grid_visible.isChecked(),'scheme':self.scheme.currentIndex(),'grid_width':self.grid_width.value(),'cross_width':self.cross_width.value(),'frame_width':self.frame_width.value(),'offset_x':self.offset_x.value(),'offset_y':self.offset_y.value(),'frames':[x.value() for x in self.frames],'margins':[x.value() for x in self.margins],'font':self.fonts[0].currentData() or self.fonts[0].currentText(),'title_font':self.fonts[1].currentData() or self.fonts[1].currentText(),'font_size':self.fsize.value(),'title_size':self.title_size.value(),'outdir':self.outdir.text(),'filename':self.filename.text(),'format':self.format.currentText()}
        self.settings_path().write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8'); QMessageBox.information(self,'参数保存','参数已保存到参数设置.json')
    def load_settings(self):
        path=self.settings_path()
        if not path.exists():
            d = BUILTIN_SETTINGS
            # 继续走统一赋值逻辑，确保首次启动与载入保存文件的行为一致。
        else:
            d = None
        try:
            if d is None: d=json.loads(path.read_text(encoding='utf-8'))
            self.text.setPlainText(d.get('text','')); self.dpi.setValue(d.get('dpi',300)); self.ch.setValue(d.get('cell_h',45)); self.cw.setValue(d.get('cell_w',50)); self.cols.setValue(d.get('cols',46)); self.rows.setValue(d.get('rows',31)); self.gap_r.setValue(d.get('gap_r',0)); self.gap_c.setValue(d.get('gap_c',0)); self.scheme.setCurrentIndex(d.get('scheme',0)); self.grid_width.setValue(d.get('grid_width',1)); self.cross_width.setValue(d.get('cross_width',1)); self.frame_width.setValue(d.get('frame_width',1)); self.offset_x.setValue(d.get('offset_x',0)); self.offset_y.setValue(d.get('offset_y',0)); self.big.setChecked(d.get('big',True)); self.grid_visible.setChecked(d.get('grid_visible',True)); self.fsize.setValue(d.get('font_size',120)); self.title_size.setValue(d.get('title_size',240)); self.outdir.setText(d.get('outdir',str(Path.cwd()/'output'))); self.filename.setText(d.get('filename','经文排版')); self.format.setCurrentText(d.get('format','PSD/PSB'))
            for controls,key in ((self.frames,'frames'),(self.margins,'margins')):
                for control,value in zip(controls,d.get(key,[])): control.setValue(value)
            for combo,key in ((self.fonts[0],'font'),(self.fonts[1],'title_font')):
                target=d.get(key)
                if target:
                    index=combo.findData(target)
                    combo.setCurrentIndex(index if index >= 0 else combo.findText(target))
            self.refresh()
        except Exception as exc: logging.warning('参数设置加载失败：%s',exc)
    def values(self):
        dpi=float(self.dpi.value()); w=self.cw.value(); h=self.ch.value(); cols=self.cols.value(); rows=self.rows.value(); ml,mt,mr,mb=[x.value() for x in self.margins]; canvas_w=cols*w+ml+mr; canvas_h=rows*h+mt+mb
        return dict(dpi=dpi,cell_w=w,cell_h=h,cols=cols,rows=rows,margin_l=ml,margin_t=mt,margin_r=mr,margin_b=mb,frame_t=self.frames[0].value(),frame_b=self.frames[1].value(),frame_l=self.frames[2].value(),frame_r=self.frames[3].value(),big_frame=self.big.isChecked(),grid_visible=self.grid_visible.isChecked(),scheme=self.scheme.currentIndex()+1,grid_width=self.grid_width.value(),cross_width=self.cross_width.value(),frame_width=self.frame_width.value(),text_offset_x=self.offset_x.value(),text_offset_y=self.offset_y.value(),canvas_w=canvas_w,canvas_h=canvas_h,font=self.fonts[0].currentData() or self.fonts[0].currentText(),font_size=self.fsize.value(),title_font=self.fonts[1].currentData() or self.fonts[1].currentText(),title_font_size=self.title_size.value())
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
        printer = QPrinter(QPrinter.HighResolution)
        default_printer = QPrinterInfo.defaultPrinter()
        if not default_printer.isValid():
            QMessageBox.warning(self, '打印', '系统没有可用的本地打印机。')
            return
        printer.setOutputFormat(QPrinter.NativeFormat)
        printer.setPrinterName(default_printer.printerName())
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.Accepted:
            return
        image = render_layout_image(self.values(), self.text.toPlainText())
        painter = QPainter(printer)
        page = printer.pageRect(QPrinter.DevicePixel)
        scaled = image.scaled(page.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawImage(page.left() + (page.width() - scaled.width()) // 2,
                          page.top() + (page.height() - scaled.height()) // 2, scaled)
        painter.end()
    def refresh(self): self.preview.set_data(self.values(), self.text.toPlainText())
    def export(self):
        started=time.perf_counter()
        progress=QProgressDialog('正在导出…','取消',0,100,self); progress.setWindowTitle('导出进度'); progress.setWindowModality(Qt.WindowModal); progress.setAutoClose(False); progress.show(); QApplication.processEvents()
        v=self.values(); logging.info('开始导出 format=%s dpi=%s canvas_mm=%.1fx%.1f',self.format.currentText(),v['dpi'],v['canvas_w'],v['canvas_h']); progress.setValue(10); QApplication.processEvents(); logging.info('参数准备 %.3fs',time.perf_counter()-started)
        iw,ih=2400,max(600,round(2400*v['canvas_h']/v['canvas_w'])); logging.info('创建导出画布 %sx%s 像素',iw,ih); img=QImage(1,1,QImage.Format_ARGB32); img.fill('white'); progress.setValue(35); QApplication.processEvents(); logging.info('画布准备 %.3fs',time.perf_counter()-started)
        # 导出时只绘制预览画布区域，避免重复渲染整个窗口导致超长阻塞
        self.preview.set_data(v,self.text.toPlainText()); QApplication.processEvents()
        # 在独立的等比例画布尺寸上重绘整幅版面，避免导出当前视口的局部内容。
        img = render_layout_image(v, self.text.toPlainText()) if self.format.currentText() in ('PNG', 'JPG') else None
        progress.setValue(15); progress.setLabelText('正在准备完整画布…'); QApplication.processEvents(); logging.info('版面渲染 %.3fs',time.perf_counter()-started)
        os.makedirs(self.outdir.text(),exist_ok=True); ext='psd' if self.format.currentText() == 'PSD/PSB' else self.format.currentText().lower(); path=Path(self.outdir.text())/(self.filename.text()+'.'+ext)
        output_path = path
        if ext in ('png', 'jpg'):
            # PNG 的 quality=95 在 Qt 中会造成几乎不压缩；使用默认无损压缩。
            saved = img.save(str(path), 'PNG') if ext == 'png' else img.save(str(path), 'JPG', 95)
            if not saved: raise OSError('图片写入失败')
        else:
            output_path = export_layered_psd(v, self.text.toPlainText(), path, True, progress)

        logging.info('文件写入完成 %.3fs path=%s total=%.3fs',time.perf_counter()-started,output_path,time.perf_counter()-started); progress.setValue(100); progress.close(); QMessageBox.information(self,'导出完成',f'已输出：{output_path}\n耗时：{time.perf_counter()-started:.1f} 秒')

if __name__=='__main__':
        app=QApplication(sys.argv); w=MainWindow(); w.showMaximized(); sys.exit(app.exec())
