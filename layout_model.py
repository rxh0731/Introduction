"""标题、正文和尾题共用的毫米坐标布局，不依赖预览窗口或 Qt。"""
from dataclasses import dataclass
import math

SETTINGS_VERSION = 2
TITLE_DEFAULTS = dict(title_cell_w=75.0, title_cell_h=90.0, title_cols=1,
                      title_rows=15, title_gap_r=0.0, title_gap_c=0.0,
                      title_offset_x=0.0, title_offset_y=5.0,
                      title_top_space=45.0, title_body_gap=25.0,
                      body_tail_gap=25.0)
TAIL_DEFAULTS = dict(tail_size=120, tail_cell_w=50.0, tail_cell_h=45.0, tail_cols=4,
                     tail_rows=31, tail_gap_r=0.0, tail_gap_c=0.0,
                     tail_offset_x=0.0, tail_offset_y=5.0)
OVERALL_DEFAULTS = dict(section_gap=25.0)


def migrate_settings(settings):
    """旧列数包含两列标题；仅在首次迁移时扣除，后续列数就是正文列数。"""
    data = dict(settings)
    if data.get('settings_version', 0) < SETTINGS_VERSION:
        data['cols'] = max(1, int(data.get('cols', 46)) - 2)
        data.setdefault('title_offset_x', data.get('offset_x', 0))
        data.setdefault('title_offset_y', data.get('offset_y', 5))
    for key, value in TITLE_DEFAULTS.items():
        data.setdefault(key, value)
    for key, value in TAIL_DEFAULTS.items():
        data.setdefault(key, value)
    for key, value in OVERALL_DEFAULTS.items():
        data.setdefault(key, value)
    data.pop('scheme', None)
    data['settings_version'] = SETTINGS_VERSION
    return data


def span(count, size, gap):
    return count * size + (count - 1) * gap


def split_regions(text):
    lines = text.splitlines()
    title = lines[0] if lines else ''
    paragraphs = lines[1:]
    tail_start = next((i for i, line in enumerate(paragraphs) if line.startswith('*')), len(paragraphs))
    return title, paragraphs[:tail_start], paragraphs[tail_start:]


def flow_region(paragraphs, rows, cols, tail=False, with_sources=False):
    """统一计算文字位置和分版边界；只有独立的 # 行是标记。"""
    positions, breaks = [], {}
    column, pending = 0, 0
    has_content, overflow = False, False
    paragraph_number = 0
    for paragraph in paragraphs:
        if paragraph == '#':
            pending += 1
            continue
        if tail and paragraph.startswith('*'):
            paragraph = paragraph[1:]
        if not paragraph:
            column += 1
            continue
        paragraph_number += 1
        if column >= cols:
            overflow = True
            break
        if pending and has_content:
            breaks[column] = pending
        pending = 0
        has_content = True
        row = (rows - len(paragraph) % rows) % rows if tail else 0
        for character_number, char in enumerate(paragraph, 1):
            if column >= cols:
                overflow = True
                break
            if char not in (' ', '\u3000'):
                position = (row, column, char)
                if with_sources:
                    position += (paragraph_number, character_number)
                positions.append(position)
            row += 1
            if row == rows:
                column += 1
                row = 0
        if row:
            column += 1
        if overflow:
            break
    return positions, breaks, overflow


def complete_params(params, text=None):
    p = dict(params)
    for key, default in {**TITLE_DEFAULTS, **TAIL_DEFAULTS, **OVERALL_DEFAULTS}.items():
        p.setdefault(key, default)
    for key in ('cols', 'rows', 'title_cols', 'title_rows', 'tail_cols', 'tail_rows'):
        value = float(p[key])
        if not math.isfinite(value) or value < 1 or not value.is_integer():
            raise ValueError('标题和正文的行数、列数必须为正整数')
        p[key] = int(value)
    for key in ('cell_w', 'cell_h', 'title_cell_w', 'title_cell_h', 'tail_cell_w', 'tail_cell_h', 'dpi'):
        if not math.isfinite(p[key]) or p[key] <= 0:
            raise ValueError('格高、格宽及 DPI 必须大于零')
    for key in ('gap_r', 'gap_c', 'title_gap_r', 'title_gap_c', 'tail_gap_r', 'tail_gap_c',
                'title_top_space', 'title_body_gap', 'margin_t', 'margin_b',
                'margin_l', 'margin_r', 'frame_t', 'frame_b', 'frame_l', 'frame_r',
                'body_tail_gap', 'section_gap'):
        if not math.isfinite(p[key]) or p[key] < 0:
            raise ValueError('间距、留白和边距不能为负数')
    if text is not None:
        _, body, tail = split_regions(text)
        p['_body_breaks'] = flow_region(body, p['rows'], p['cols'])[1]
        p['_tail_breaks'] = flow_region(tail, p['tail_rows'], p['tail_cols'], tail=True)[1]
    p.setdefault('_body_breaks', {})
    p.setdefault('_tail_breaks', {})
    p['body_w'] = span(p['cols'], p['cell_w'], p['gap_c']) + sum(
        count * p['section_gap'] - p['gap_c'] for count in p['_body_breaks'].values())
    p['body_h'] = span(p['rows'], p['cell_h'], p['gap_r'])
    p['title_w'] = span(p['title_cols'], p['title_cell_w'], p['title_gap_c'])
    p['title_h'] = span(p['title_rows'], p['title_cell_h'], p['title_gap_r'])
    p['tail_w'] = span(p['tail_cols'], p['tail_cell_w'], p['tail_gap_c']) + sum(
        count * p['section_gap'] - p['tail_gap_c'] for count in p['_tail_breaks'].values())
    p['tail_h'] = span(p['tail_rows'], p['tail_cell_h'], p['tail_gap_r'])
    p['layout_w'] = p['tail_w'] + p['body_tail_gap'] + p['body_w'] + p['title_body_gap'] + p['title_w']
    p['layout_h'] = max(p['body_h'], p['title_top_space'] + p['title_h'])
    p['canvas_w'] = p['margin_l'] + p['layout_w'] + p['margin_r']
    p['canvas_h'] = p['margin_t'] + p['layout_h'] + p['margin_b']
    return p


@dataclass(frozen=True)
class Cell:
    row: int
    column: int
    x: float
    y: float
    w: float
    h: float
    title: bool
    region: str = 'body'


@dataclass(frozen=True)
class Glyph:
    cell: Cell
    text: str
    paragraph: int = 0
    character: int = 0

    @property
    def source_code(self):
        return f'{self.paragraph}.{self.character}'

    @property
    def group_name(self):
        if self.cell.region == 'title': return '标题'
        if self.cell.region == 'tail': return '尾题'
        return str(self.cell.column + 1)

    @property
    def layer_name(self):
        if self.cell.region == 'title': prefix = f'标题{self.cell.column + 1}'
        elif self.cell.region == 'tail': prefix = f'尾题{self.cell.column + 1}'
        else: prefix = str(self.cell.column + 1)
        return f'{prefix}.{self.cell.row + 1}.{self.text}'


def cell_at(p, row, column, title=False):
    prefix = 'title_' if title else ''
    w, h = p[prefix + 'cell_w'], p[prefix + 'cell_h']
    cols = p[prefix + 'cols']
    region = 'title' if title else 'body'
    left = p['margin_l'] + (p['tail_w'] + p['body_tail_gap'] if not title else
                            p['tail_w'] + p['body_tail_gap'] + p['body_w'] + p['title_body_gap'])
    top = p['margin_t'] + (p['title_top_space'] if title else 0)
    gap = p[prefix + 'gap_c']
    adjustment = 0 if title else sum(count * p['section_gap'] - gap
                                    for boundary, count in p['_body_breaks'].items() if boundary <= column)
    width = p['title_w'] if title else p['body_w']
    return Cell(row, column, left + width - w - column * (w + gap) - adjustment,
                top + row * (h + p[prefix + 'gap_r']), w, h, title, region)


def tail_cell_at(p, row, column):
    w, h = p['tail_cell_w'], p['tail_cell_h']
    adjustment = sum(count * p['section_gap'] - p['tail_gap_c']
                     for boundary, count in p['_tail_breaks'].items() if boundary <= column)
    return Cell(row, column,
                p['margin_l'] + p['tail_w'] - w - column * (w + p['tail_gap_c']) - adjustment,
                p['margin_t'] + row * (h + p['tail_gap_r']), w, h, False, 'tail')


def cells(p):
    for title in (False, True):
        prefix = 'title_' if title else ''
        for column in range(p[prefix + 'cols']):
            for row in range(p[prefix + 'rows']):
                yield cell_at(p, row, column, title)
    for column in range(p['tail_cols']):
        for row in range(p['tail_rows']):
            yield tail_cell_at(p, row, column)


def place_text(p, text):
    p = complete_params(p, text)
    title, body_lines, tail_lines = split_regions(text)
    glyphs, warnings = [], []
    capacity = p['title_cols'] * p['title_rows']
    if len(title) > capacity:
        warnings.append(f'标题需要 {len(title)} 格，当前只有 {capacity} 格，请增加标题行数或列数。')
    for i, char in enumerate(title[:capacity]):
        if char not in (' ', '\u3000'):
            glyphs.append(Glyph(cell_at(p, i % p['title_rows'], i // p['title_rows'], True), char, 1, i + 1))
    body, _, overflow = flow_region(body_lines, p['rows'], p['cols'], with_sources=True)
    tail, _, tail_overflow = flow_region(tail_lines, p['tail_rows'], p['tail_cols'], tail=True, with_sources=True)
    # 编码独立于视觉列号：空行及 # 不算段落，空格占字序，尾题 * 不占字序。
    body_count = sum(bool(line) and line != '#' for line in body_lines)
    glyphs.extend(Glyph(cell_at(p, row, col), char, para + 1, index)
                  for row, col, char, para, index in body)
    glyphs.extend(Glyph(tail_cell_at(p, row, col), char, para + body_count + 1, index)
                  for row, col, char, para, index in tail)
    if tail_overflow:
        warnings.append('尾题超出当前网格容量，请增加尾题行数或列数。')
    if overflow:
        warnings.append('正文超出当前网格容量，请增加正文行数或列数；导出和打印前需解决此问题。')
    return glyphs, warnings
