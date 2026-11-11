import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import json
import unittest
from pathlib import Path

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QProgressDialog, QLabel, QTabWidget
from psd_tools import PSDImage

import main
from layout_model import complete_params, migrate_settings, cells, place_text
from layout_render import glyph_rect

APP = QApplication.instance() or QApplication([])


def params(**changes):
    p = dict(dpi=72, cell_w=5, cell_h=4, cols=3, rows=5, gap_r=0, gap_c=0,
             margin_t=3, margin_b=4, margin_l=5, margin_r=6,
             frame_t=1, frame_b=1, frame_l=1, frame_r=1,
             title_cell_w=7.5, title_cell_h=6.25, title_cols=1, title_rows=2,
             title_gap_r=0, title_gap_c=0, title_top_space=2.5, title_body_gap=5,
             tail_cell_w=5, tail_cell_h=4, tail_cols=1, tail_rows=2,
             tail_gap_r=0, tail_gap_c=0, body_tail_gap=5,
             text_offset_x=0, text_offset_y=0, title_offset_x=0, title_offset_y=0,
             tail_offset_x=0, tail_offset_y=0,
             font='Arial', title_font='Arial', tail_font='Arial', font_size=8, title_font_size=10, tail_font_size=8,
             grid_visible=True, big_frame=True, grid_width=1, cross_width=1, frame_width=1)
    p.update(changes)
    return complete_params(p)


class LayoutTests(unittest.TestCase):
    def test_ui_settings_roundtrip_and_window_sizes(self):
        with tempfile.TemporaryDirectory() as directory:
            config=Path(directory)/'settings.json'
            class Window(main.MainWindow):
                def settings_path(self): return config
            window=Window()
            self.assertEqual(window.cols.value(),44)
            self.assertEqual(window.fsize.value(),120)
            self.assertEqual(window.title_size.value(),240)
            self.assertEqual(window.title_body_gap.value(),25)
            self.assertEqual(window.title_cell_h.value(),90)
            self.assertEqual(window.title_cell_w.value(),75)
            self.assertEqual(window.title_top_space.value(),45)
            self.assertEqual(window.section_gap.value(),25)
            self.assertIn('分版间距(mm)',[label.text() for label in window.findChildren(QLabel)])
            tabs=window.findChild(QTabWidget)
            tabs.setCurrentIndex(3)
            window.section_gap.setValue(12.75)
            window.text.setPlainText('序\nA\n#\nB')
            window.refresh()
            separated_width=window.preview.params['canvas_w']
            window.text.setPlainText('序\nA\nB')
            window.refresh()
            self.assertAlmostEqual(separated_width-window.preview.params['canvas_w'],12.75)
            window.title_cell_w.setValue(75.25)
            window.title_cell_h.setValue(56.25)
            window.title_cols.setValue(2)
            window.title_offset_y.setValue(8.75)
            window.offset_y.setValue(-2.5)
            self.assertFalse(window.title_cell_w.validator().validate('1.234',0)[0].name=='Acceptable')
            data=window.settings_data()
            config.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
            restored=Window()
            self.assertEqual(restored.settings_data(),data)
            for width,height in ((1920,1080),(1366,768),(1280,720)):
                restored.resize(width,height); restored.show(); APP.processEvents(); APP.processEvents()
                self.assertEqual(restored.settings_scroll.horizontalScrollBar().maximum(),0)
                self.assertGreaterEqual(restored.text.height(),110)
                self.assertGreater(restored.preview.width(),500)
            window.close(); restored.close()

    def test_migration_and_defaults(self):
        old = dict(cols=46, text='序言\n经文', offset_y=7)
        current = migrate_settings(old)
        self.assertEqual((current['cols'], current['title_body_gap'], current['body_tail_gap']), (44, 25, 25))
        self.assertEqual(current['title_offset_y'], 7)
        self.assertEqual(current['section_gap'], 25)
        self.assertEqual(migrate_settings(current), current)
        self.assertEqual(old['cols'], 46)
        self.assertEqual(main.BUILTIN_SETTINGS['cols'], 44)
        self.assertEqual(main.BUILTIN_SETTINGS['font_size'], 120)
        self.assertEqual(main.BUILTIN_SETTINGS['title_size'], 240)
        self.assertEqual(main.BUILTIN_SETTINGS['title_body_gap'], 25)
        self.assertEqual(main.BUILTIN_SETTINGS['body_tail_gap'], 25)
        self.assertEqual(main.BUILTIN_SETTINGS['section_gap'], 25)

    def test_section_marker_geometry_and_numbering(self):
        text='序\nABCDE\n#\nFG\nHI'
        p=complete_params(params(gap_c=2), text)
        glyphs,warnings=place_text(p,text)
        self.assertFalse(warnings)
        body=[g for g in glyphs if g.cell.region=='body']
        a,f,h=(next(g for g in body if g.text==ch) for ch in 'AFH')
        self.assertEqual(a.cell.x-(f.cell.x+f.cell.w),25)
        self.assertEqual(f.cell.x-(h.cell.x+h.cell.w),2)
        self.assertEqual((f.group_name,f.layer_name),('2','2.1.F'))
        self.assertEqual(p['canvas_w']-params(gap_c=2)['canvas_w'],23)
        self.assertEqual(len(list(cells(p))),len(list(cells(params()))))
        self.assertEqual(complete_params(p,text),p)
        cleared=complete_params(p,'序\nABCDE\nFG\nHI')
        self.assertEqual(cleared['canvas_w'],params(gap_c=2)['canvas_w'])

    def test_section_marker_exact_match_empty_lines_and_ends(self):
        for text in ('序\nA#B','序\n##','序\n #','序\n# ','序\n\u3000#'):
            p=complete_params(params(),text)
            glyphs,warnings=place_text(p,text)
            self.assertFalse(warnings)
            self.assertFalse(p['_body_breaks'])
            self.assertTrue(any(g.text=='#' for g in glyphs))
        text='序\n#\nA\n#\n#\nB\n#'
        p=complete_params(params(),text)
        glyphs,warnings=place_text(p,text)
        self.assertFalse(warnings)
        a,b=(next(g for g in glyphs if g.text==ch) for ch in 'AB')
        self.assertEqual(a.cell.x-b.cell.x-b.cell.w,50)
        self.assertEqual(p['_body_breaks'],{1:2})
        self.assertFalse(any(g.text=='#' for g in glyphs))
        p=complete_params(params(),'序\nA\n\nB')
        glyphs,_=place_text(p,'序\nA\n\nB')
        self.assertFalse(p['_body_breaks'])
        self.assertEqual(next(g for g in glyphs if g.text=='B').group_name,'3')

    def test_section_marker_tail_and_fractional_zero_gaps(self):
        text='序\nA\n#\nB\n*尾\n#\n*题 '
        for gap in (0,1.25,25):
            p=complete_params(params(tail_cols=2,tail_gap_c=3,section_gap=gap),text)
            glyphs,warnings=place_text(p,text)
            self.assertFalse(warnings)
            a,b=(next(g for g in glyphs if g.text==ch) for ch in 'AB')
            tail,last=(next(g for g in glyphs if g.text==ch) for ch in '尾题')
            self.assertAlmostEqual(a.cell.x-b.cell.x-b.cell.w,gap)
            self.assertAlmostEqual(tail.cell.x-last.cell.x-last.cell.w,gap)
            self.assertEqual(last.cell.row,0)
        with self.assertRaises(ValueError): params(section_gap=-1)
        _,warnings=place_text(params(tail_cols=1,tail_rows=1),'序\nA\n*尾\n#\n*题')
        self.assertTrue(any('尾题' in warning for warning in warnings))
        for text in ('序\n#\nA\n#\n*尾\n#', '序\n#\n#'):
            p=complete_params(params(),text)
            self.assertEqual((p['_body_breaks'],p['_tail_breaks']),({},{}))

    def test_section_marker_preview_png_and_psd_geometry(self):
        text='序\nA\n#\nB\n*尾\n#\n*题'
        p=complete_params(params(dpi=25.4,cell_w=20,cell_h=15,
                                 tail_cols=2,tail_cell_w=20,tail_cell_h=15),text)
        glyphs,_=place_text(p,text)
        a,b=(next(g for g in glyphs if g.text==ch) for ch in 'AB')
        x=round((a.cell.x+b.cell.x+b.cell.w)/2)
        y=round(a.cell.y+2)
        image=main.render_layout_image(p,text)
        self.assertEqual(image.width(),round(p['canvas_w']))
        self.assertEqual(image.pixelColor(x,y).name(),'#ffffff')
        preview=main.Preview(); preview.set_data(params(dpi=25.4,cell_w=20,cell_h=15,
                                       tail_cols=2,tail_cell_w=20,tail_cell_h=15),text)
        self.assertEqual(preview.params['canvas_w'],p['canvas_w'])
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            self.assertTrue(image.save(str(folder/'sections.png'),'PNG'))
            self.assertEqual(QImage(str(folder/'sections.png')).size(),image.size())
            path=main.export_layered_psd(p,text,folder/'sections.psd',True,QProgressDialog())
            doc=PSDImage.open(path)
            self.assertEqual(doc.size,(image.width(),image.height()))
            grid=next(g for g in doc if g.name=='网格与框').topil()
            self.assertEqual(grid.getpixel((x,y))[3],0)
            layer=next(g for group in doc if group.is_group() for g in group if g.name=='2.1.B')
            rect=glyph_rect(p,b,1)
            self.assertEqual(layer.left,round(rect.x()))
            self.assertEqual([g.name for g in reversed(list(doc))],['标题','1','2','尾题','网格与框','纯白'])

    def test_fractional_dimensions_and_independent_regions(self):
        p = params()
        grid = list(cells(p))
        self.assertEqual(len(grid), 3*5+1*2+1*2)
        title = next(c for c in grid if c.title)
        self.assertEqual((title.w,title.h), (7.5,6.25))
        self.assertEqual(title.x-(p['margin_l']+p['body_w']), 15)
        self.assertEqual(title.y-p['margin_t'], 2.5)
        glyphs,_ = place_text(p,'序言\n佛法')
        body = next(g for g in glyphs if not g.cell.title)
        self.assertEqual(body.group_name,'1')
        self.assertEqual(body.cell.y,p['margin_t'])
        self.assertGreater(title.x,body.cell.x)
        other = params(title_cell_w=15,title_cell_h=30,title_cols=2)
        self.assertEqual(other['body_w'],p['body_w'])
        self.assertEqual(other['body_h'],p['body_h'])

    def test_gaps_margins_and_tall_title(self):
        p = params(gap_r=1.25,gap_c=2.5,title_cols=2,title_gap_c=1.5,
                   title_gap_r=2,title_top_space=10,title_cell_h=20)
        self.assertEqual(p['body_w'],20)
        self.assertEqual(p['body_h'],25)
        self.assertEqual(p['title_w'],16.5)
        self.assertEqual(p['layout_h'],52)
        self.assertEqual(p['canvas_w'],5+5+5+20+5+16.5+6)
        self.assertEqual(p['canvas_h'],3+52+4)

    def test_title_columns_spaces_and_layer_names(self):
        glyphs,warnings=place_text(params(title_cols=2),' 序\u3000言\n佛法')
        self.assertFalse(warnings)
        title=[g for g in glyphs if g.cell.title]
        self.assertEqual([g.layer_name for g in title],['标题1.2.序','标题2.2.言'])
        self.assertGreater(title[0].cell.x,title[1].cell.x)
        body=[g for g in glyphs if g.cell.region=='body']
        self.assertEqual([g.layer_name for g in body],['1.1.佛','1.2.法'])

    def test_paragraphs_full_columns_blank_column_and_signature_spaces(self):
        glyphs,warnings=place_text(params(cols=4,body_tail_gap=0,tail_rows=4),'序\nABCDE\nFG\n\n*H \u3000')
        self.assertFalse(warnings)
        positions={g.text:(g.cell.column,g.cell.row) for g in glyphs if g.cell.region=='body'}
        self.assertEqual(positions['E'],(0,4))
        self.assertEqual(positions['F'],(1,0))
        tail=next(g for g in glyphs if g.text=='H')
        self.assertEqual((tail.cell.region,tail.cell.column,tail.cell.row),('tail',0,1))

    def test_body_tail_gap_adds_blank_columns(self):
        p=params(cols=5, rows=4, cell_w=50, gap_c=0, body_tail_gap=25)
        glyphs,warnings=place_text(p,'序\nAB\n*尾')
        self.assertFalse(warnings)
        tail=next(g for g in glyphs if g.text=='尾')
        self.assertEqual((tail.cell.region,tail.cell.column),('tail',0))
        no_gap=params(cols=5, rows=4, cell_w=50, gap_c=0, body_tail_gap=0)
        glyphs,_=place_text(no_gap,'序\nAB\n*尾')
        self.assertEqual(next(g for g in glyphs if g.text=='尾').cell.column,0)

    def test_title_and_body_offsets_are_independent(self):
        p=params(title_offset_x=10,title_offset_y=5,text_offset_y=-10)
        glyphs,_=place_text(p,'序\n佛')
        title,body=glyphs
        tr,br=glyph_rect(p,title,1),glyph_rect(p,body,1)
        self.assertAlmostEqual(tr.x()-title.cell.x,.75)
        self.assertAlmostEqual(tr.y()-title.cell.y,.3125)
        self.assertAlmostEqual(br.y()-body.cell.y,-.4)
        self.assertEqual(br.x(),body.cell.x)

    def test_capacity_warnings_and_invalid_geometry(self):
        p=params(cols=1,rows=1,title_rows=1)
        _,warnings=place_text(p,'序言\n佛法')
        self.assertEqual(len(warnings),2)
        with self.assertRaises(ValueError): main.render_layout_image(p,'序言\n佛法')
        with self.assertRaises(ValueError): params(title_cell_h=0)
        with self.assertRaises(ValueError): params(title_cols=1.5)

    def test_png_roundtrip_psd_groups_transparency_and_order(self):
        p=params(title_cols=2)
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            image=main.render_layout_image(p,'序言甲乙\nABCDE\n佛法')
            self.assertTrue(image.save(str(folder/'test.png'),'PNG'))
            loaded=QImage(str(folder/'test.png')).convertToFormat(image.format())
            self.assertEqual(bytes(loaded.constBits()),bytes(image.constBits()))
            progress=QProgressDialog()
            path=main.export_layered_psd(p,'序言甲乙\nABCDE\n佛法',folder/'test.psd',True,progress)
            doc=PSDImage.open(path)
            # psd-tools 按从底到顶遍历；Photoshop 面板顺序相反。
            self.assertEqual([g.name for g in reversed(list(doc))],['标题','1','2','网格与框','纯白'])
            groups={g.name:g for g in doc if g.is_group()}
            self.assertEqual([g.name for g in reversed(list(groups['标题']))],
                             ['标题1.1.序','标题1.2.言','标题2.1.甲','标题2.2.乙'])
            self.assertEqual([g.name for g in reversed(list(groups['1']))],
                             [f'1.{i+1}.{char}' for i,char in enumerate('ABCDE')])
            self.assertTrue(all(not g.has_mask() for group in groups.values() for g in group))
            grid=next(g for g in doc if g.name=='网格与框').topil()
            self.assertEqual(grid.getpixel((0,0))[3],0)
            self.assertEqual(grid.getchannel('A').getextrema(),(0,255))
            self.assertEqual(list(doc)[0].topil().getpixel((0,0)),(255,255,255,255))
            for group in groups.values(): self.assertFalse(group.open_folder)

    def test_tail_is_independent_region_and_psd_group(self):
        p=params(tail_cols=2, tail_rows=4, body_tail_gap=25)
        glyphs, warnings=place_text(p, '序\n佛法\n*甲 乙\n*丙')
        self.assertFalse(warnings)
        tail=[g for g in glyphs if g.cell.region=='tail']
        self.assertTrue(tail)
        self.assertTrue(all(g.group_name=='尾题' and g.layer_name.startswith('尾题') for g in tail))
        self.assertLess(next(g for g in tail if g.cell.column==0).cell.x,
                        next(g for g in glyphs if g.cell.region=='body').cell.x)
        with tempfile.TemporaryDirectory() as directory:
            path=main.export_layered_psd(p,'序\n佛法\n*甲 乙\n*丙',Path(directory)/'tail.psd',True,QProgressDialog())
            doc=PSDImage.open(path)
            self.assertIn('尾题',[layer.name for layer in doc])
            tail_group=next(layer for layer in doc if layer.name=='尾题')
            self.assertTrue(all(layer.name.startswith('尾题') for layer in tail_group))

    def test_psb_automatically_selected_for_long_canvas(self):
        p=params(dpi=25.4,cols=1,rows=1,cell_h=.1,cell_w=.1,title_cell_w=30001,
                 title_cell_h=.1,title_rows=1,title_top_space=0,
                 margin_t=1,margin_b=1,margin_l=1,margin_r=1)
        with tempfile.TemporaryDirectory() as directory:
            path=main.export_layered_psd(p,'',Path(directory)/'wide.psd',True,QProgressDialog())
            self.assertEqual(path.suffix,'.psb')
            self.assertEqual(PSDImage.open(path).version,2)


if __name__ == '__main__':
    unittest.main()
