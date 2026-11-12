"""预览、导出和打印共用的绘制函数。"""
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QFont, QPen, QColor
from layout_model import cells, place_text, complete_params
from glyph_library import prepare_images


def glyph_rect(params, glyph, scale, origin=(0, 0)):
    c = glyph.cell
    prefix = 'title_' if c.region == 'title' else ('tail_' if c.region == 'tail' else '')
    dx = c.w * params.get(prefix + 'text_offset_x', params.get(prefix + 'offset_x', 0)) / 100
    dy = c.h * params.get(prefix + 'text_offset_y', params.get(prefix + 'offset_y', 0)) / 100
    return QRectF(origin[0] + (c.x + dx) * scale, origin[1] + (c.y + dy) * scale,
                  c.w * scale, c.h * scale)


def glyph_font(params, title, scale, region=None):
    if region == 'tail':
        family, size = params['tail_font'], params['tail_font_size']
    elif title:
        family, size = params['title_font'], params['title_font_size']
    else:
        family, size = params['font'], params['font_size']
    font = QFont(family)
    font.setPixelSize(max(1, round(size * scale * 25.4 / 72)))
    return font


def image_rect(params, glyph, placement, scale, origin=(0, 0)):
    return placement.rect(glyph_rect(params, glyph, scale, origin), scale)


def draw_glyph(painter, params, glyph, scale, origin=(0, 0), session=None):
    if session is not None:
        placement = session.placements.get(glyph)
        if placement is None:
            return
        rect = image_rect(params, glyph, placement, scale, origin)
        bitmap = session.qimage(placement, max(1, round(rect.width())), max(1, round(rect.height())))
        painter.drawImage(rect, bitmap)
    else:
        painter.setFont(glyph_font(params, glyph.cell.title, scale, glyph.cell.region))
        painter.drawText(glyph_rect(params, glyph, scale, origin), Qt.AlignCenter, glyph.text)


def draw_layout(painter, params, text, scale, origin=(0, 0), *, draw_text=True):
    p = complete_params(params, text)
    glyphs, warnings = place_text(p, text)
    session = prepare_images(p, text, glyphs) if draw_text else None
    ox, oy = origin
    painter.fillRect(QRectF(ox, oy, p['canvas_w'] * scale, p['canvas_h'] * scale), QColor('white'))
    stroke_scale = scale / (p['dpi'] / 25.4)
    if p.get('grid_visible', True):
        edge = QPen(QColor('red'), p.get('grid_width', 1) * stroke_scale)
        cross = QPen(QColor('red'), p.get('cross_width', 1) * stroke_scale)
        cross.setDashPattern([8, 5])
        for c in cells(p):
            x, y, w, h = ox + c.x*scale, oy + c.y*scale, c.w*scale, c.h*scale
            painter.setPen(edge)
            painter.drawRect(QRectF(x, y, w, h))
            painter.setPen(cross)
            painter.drawLine(QPointF(x+w/2, y), QPointF(x+w/2, y+h))
            painter.drawLine(QPointF(x, y+h/2), QPointF(x+w, y+h/2))
    painter.setPen(QColor('black'))
    for glyph in glyphs if draw_text else ():
        draw_glyph(painter, p, glyph, scale, origin, session)
    if p.get('big_frame', True):
        painter.setPen(QPen(QColor('red'), p.get('frame_width', 1) * stroke_scale))
        painter.drawRect(QRectF(ox + (p['margin_l']-p['frame_l'])*scale,
                                oy + (p['margin_t']-p['frame_t'])*scale,
                                (p['layout_w']+p['frame_l']+p['frame_r'])*scale,
                                (p['layout_h']+p['frame_t']+p['frame_b'])*scale))
    return glyphs, warnings
