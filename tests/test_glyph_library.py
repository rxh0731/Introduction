import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from PIL import Image, ImageDraw
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QProgressDialog, QTabWidget, QScrollArea
from psd_tools import PSDImage
from psd_tools.constants import Resource
from psd_tools.psd.image_resources import ImageResource, ResoulutionInfo

import main
from glyph_library import (IMAGE_DEFAULTS, AssetCache, LibraryIndex, image_settings,
                           load_image, prepare_images)
from layout_model import complete_params, place_text
from layout_render import draw_layout, image_rect
from test_independent_layout import APP, params


def save_glyph(path, size=(40, 60), box=None, color='black', dpi=25.4, opaque=False):
    image=Image.new('RGB' if opaque else 'RGBA',size,'white' if opaque else (0,0,0,0))
    ImageDraw.Draw(image).rectangle(box or (0,0,size[0]-1,size[1]-1),fill=color)
    options={} if dpi is None else {'dpi':(dpi,dpi)}
    image.save(path,**options)


def image_params(directory, **changes):
    p=dict(IMAGE_DEFAULTS)
    p.update(text_source='images',library_dir=str(directory),image_auto_scale=False,
             image_scale_mode='cell',image_cell_percent=80)
    p.update(changes)
    return params(**p)


class GlyphLibraryTests(unittest.TestCase):
    def test_index_recursive_natural_order_and_stable_rotation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); nested=root/'子目录'; nested.mkdir()
            for name in ('佛10.png','佛2.png','序.png'): save_glyph(root/name)
            save_glyph(nested/'法1.tif')
            p=image_params(root)
            text='序\n佛佛佛法缺'
            glyphs,warnings=place_text(p,text)
            self.assertFalse(warnings)
            session=prepare_images(p,text,glyphs)
            names=[entry.path.name if entry else None for entry in session.placements.values()]
            self.assertEqual(names,['序.png','佛2.png','佛10.png','佛2.png','法1.tif',None])
            self.assertEqual(session.index.file_count,4)
            self.assertEqual([g.text for g in session.missing],['缺'])
            p['_image_session']=session
            self.assertIs(prepare_images(p,text,glyphs),session)
            self.assertEqual([entry.path.name if entry else None for entry in
                prepare_images(p,text,glyphs,force=True).placements.values()],names)
            self.assertIn('佛2.png；佛10.png',session.report())

    def test_paragraph_codes_ignore_markers_preserve_spaces_and_wrap(self):
        text=' 序言\n佛 法\n\n#\n法\n*尾\u3000題\n#\n*末'
        p=params(title_rows=4,cols=4,rows=2,tail_cols=3,tail_rows=4)
        glyphs,warnings=place_text(p,text)
        self.assertFalse(warnings)
        self.assertEqual([(g.text,g.source_code) for g in glyphs],
            [('序','1.2'),('言','1.3'),('佛','2.1'),('法','2.3'),('法','3.1'),
             ('尾','4.1'),('題','4.3'),('末','5.1')])
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for glyph in glyphs: save_glyph(root/(glyph.source_code+'.png'))
            save_glyph(root/'错误命名.png')
            save_glyph(root/'1.2.tif')
            p.update(image_params(root,library_naming='paragraph'))
            # prepare_images 只使用传入字位，不根据视觉列号重新编码。
            session=prepare_images(p,text,glyphs)
            self.assertFalse(session.missing)
            for glyph,entry in session.placements.items(): self.assertEqual(entry.path.stem,glyph.source_code)
            self.assertTrue(any('使用排序第一项' in issue for issue in session.issues))
            self.assertTrue(any('已跳过' in issue for issue in session.issues))

    def test_dpi_full_crop_aspect_ratio_and_region_offsets(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            save_glyph(root/'序.png',size=(100,80),box=(10,5,29,44))
            save_glyph(root/'佛.png',size=(100,80),box=(10,5,29,44),opaque=True)
            text='序\n佛'
            p=image_params(root,image_scale_mode='physical',title_offset_x=10,
                           title_offset_y=-5,text_offset_x=-10,text_offset_y=20)
            glyphs,_=place_text(p,text)
            full=prepare_images(p,text,glyphs)
            for entry in full.placements.values():
                self.assertEqual(entry.bounds,(0,0,100,80))
                self.assertAlmostEqual(entry.width_mm,100,places=3)
                self.assertAlmostEqual(entry.height_mm,80,places=3)
            p['image_alignment']='crop'
            cropped=prepare_images(p,text,glyphs)
            for glyph,entry in cropped.placements.items():
                self.assertEqual(entry.bounds,(10,5,30,45))
                self.assertAlmostEqual(entry.width_mm/entry.height_mm,.5)
                rect=image_rect(p,glyph,entry,1)
                x=10 if glyph.cell.title else -10
                y=-5 if glyph.cell.title else 20
                self.assertAlmostEqual(rect.center().x(),glyph.cell.x+glyph.cell.w*(.5+x/100))
                self.assertAlmostEqual(rect.center().y(),glyph.cell.y+glyph.cell.h*(.5+y/100))

    def test_physical_global_auto_thresholds_cell_scaling_and_fallback_dpi(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); save_glyph(root/'佛.png',size=(10,20))
            p=image_params(root,cell_w=20,cell_h=40,image_scale_mode='physical')
            glyphs,_=place_text(p,'序\n佛')
            glyph=next(g for g in glyphs if g.text=='佛')
            def dimensions(**changes):
                settings=dict(p); settings.update(changes)
                entry=prepare_images(settings,'序\n佛',glyphs).placements[glyph]
                return entry.width_mm,entry.height_mm
            self.assertEqual(dimensions(),(10,20))
            self.assertEqual(dimensions(image_scale_percent=200),(20,40))
            self.assertEqual(dimensions(image_auto_scale=True),(19,38))
            self.assertEqual(dimensions(image_auto_scale=True,image_scale_percent=600),(19,38))
            # 位于两阈值之间时维持全局比例；等于阈值时触发自动缩放。
            self.assertEqual(dimensions(image_auto_scale=True,image_scale_percent=200),(20,40))
            self.assertEqual(dimensions(image_auto_scale=True,image_scale_percent=150),(19,38))
            self.assertEqual(dimensions(image_auto_scale=True,image_scale_percent=300),(19,38))
            self.assertEqual(dimensions(image_scale_mode='cell',image_cell_percent=95),(19,38))
            save_glyph(root/'佛.png',size=(300,150),dpi=None)
            session=prepare_images(p,'序\n佛',glyphs)
            entry=session.placements[glyph]
            self.assertEqual(len(session.fallbacks),1)
            self.assertAlmostEqual(entry.width_mm,25.4)
            self.assertAlmostEqual(entry.height_mm,12.7)

    def test_formats_first_frame_psd_psb_and_bad_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for extension in ('png','jpg','tif','gif','bmp','webp'):
                path=root/f'佛.{extension}'
                save_glyph(path,opaque=extension in ('jpg','bmp'),box=(10,10,29,49))
                loaded=load_image(path)
                self.assertEqual(loaded.image.size,(40,60))
                self.assertIsNotNone(loaded.bounds)
            for extension in ('psd','psb'):
                path=root/f'法.{extension}'
                doc=PSDImage.new('RGBA',(40,60))
                if extension=='psb': doc._record.header.version=2
                doc.create_pixel_layer(Image.new('RGBA',(40,60),'black'),name='字图')
                doc.image_resources[Resource.RESOLUTION_INFO]=ImageResource(
                    key=Resource.RESOLUTION_INFO,
                    data=ResoulutionInfo(horizontal=600*65536,horizontal_unit=1,
                                        vertical=600*65536,vertical_unit=1))
                doc.save(path,encoding='gb18030')
                loaded=load_image(path)
                self.assertEqual(loaded.image.size,(40,60))
                self.assertEqual(loaded.dpi,600)
                self.assertFalse(loaded.fallback_dpi)
            path=root/'多帧.gif'
            Image.new('RGB',(8,10),'red').save(path,save_all=True,
                append_images=[Image.new('RGB',(8,10),'blue')],duration=100,loop=0)
            self.assertEqual(load_image(path).image.getpixel((2,2)),(255,0,0,255))
            (root/'坏.png').write_bytes(b'not an image')
            Image.new('RGBA',(10,10),(0,0,0,0)).save(root/'空.png')
            p=image_params(root); glyphs,_=place_text(p,'序\n坏空缺')
            session=prepare_images(p,'序\n坏空缺',glyphs)
            self.assertEqual(len(session.missing),4)
            self.assertEqual(len(session.failed),2)
            self.assertEqual(len(session.issues),2)

    def test_preview_export_png_jpg_psd_missing_transparency_and_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            save_glyph(root/'序.png',color='red')
            save_glyph(root/'佛1.png',color='black')
            save_glyph(root/'佛2.png',color='blue')
            save_glyph(root/'尾.png',color='green')
            p=image_params(root,dpi=25.4,cell_w=20,cell_h=30,title_cell_w=30,
                           title_cell_h=40,tail_cell_w=20,tail_cell_h=30,rows=4,
                           grid_visible=False,big_frame=False,text_offset_y=0)
            text='序\n佛佛缺\n*尾'
            glyphs,_=place_text(p,text)
            session=prepare_images(p,text,glyphs); p['_image_session']=session
            image=main.render_layout_image(p,text)
            for glyph,color in zip(glyphs,('red','black','blue','white','green')):
                center=QRectF(glyph.cell.x,glyph.cell.y,glyph.cell.w,glyph.cell.h).center()
                self.assertEqual(image.pixelColor(round(center.x()),round(center.y())).name(),
                                 {'red':'#ff0000','black':'#000000','blue':'#0000ff','white':'#ffffff','green':'#008000'}[color])
            for extension in ('png','jpg'):
                self.assertTrue(image.save(str(root/('result.'+extension)),extension.upper()))
                self.assertEqual(QImage(str(root/('result.'+extension))).size(),image.size())
            # 同一绘制接口在预览、打印、位图导出中保持一致。
            comparison=QImage(image.size(),image.format()); comparison.fill('white')
            painter=QPainter(comparison); draw_layout(painter,p,text,1); painter.end()
            self.assertEqual(bytes(comparison.constBits()),bytes(image.constBits()))
            preview=main.Preview(); preview.set_data(p,text)
            self.assertIs(preview.params['_image_session'],session)
            path=main.export_layered_psd(p,text,root/'result.psd',True,QProgressDialog())
            document=PSDImage.open(path)
            self.assertEqual([g.name for g in reversed(list(document))],['标题','1','尾题','网格与框','纯白'])
            layers=[g for group in document if group.is_group() for g in group]
            self.assertEqual(len(layers),4)
            self.assertFalse(any('缺' in g.name for g in layers))
            for glyph in glyphs:
                entry=session.placements[glyph]
                if entry is None: continue
                layer=next(g for g in layers if g.name==glyph.layer_name)
                rect=image_rect(p,glyph,entry,1)
                self.assertEqual((layer.left,layer.top),(round(rect.x()),round(rect.y())))
                self.assertEqual(layer.size,(round(rect.width()),round(rect.height())))
                self.assertFalse(layer.has_mask())
            for group in document:
                if group.is_group(): self.assertFalse(group.open_folder)

            # 狭长画布跨过 PSD 尺寸限制时仍保留正确图片层和 PSB 版本。
            long_params=dict(p,margin_r=30001)
            path=main.export_layered_psd(long_params,text,root/'long.psd',True,QProgressDialog())
            self.assertEqual(path.suffix,'.psb')
            long_document=PSDImage.open(path)
            self.assertEqual(long_document.version,2)
            long_layers=[layer for group in long_document if group.is_group() for layer in group]
            self.assertEqual(len(long_layers),4)
            self.assertEqual(long_layers[0].topil().getchannel('A').getextrema(),(255,255))

    def test_ui_options_reload_refresh_and_small_window_sizes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); config=root/'settings.json'; save_glyph(root/'序.png')
            class Window(main.MainWindow):
                def settings_path(self): return config
            window=Window()
            self.addCleanup(window.close)
            self.assertEqual(window.text_source.currentData(),'font')
            window.text.setPlainText('序\n佛')
            window.text_source.setCurrentIndex(1)
            window.library_dir.setText(str(root))
            self.assertFalse(window.title_size.isEnabled())
            self.assertFalse(window.fonts[0].isEnabled())
            self.assertTrue(window.offset_x.isEnabled())
            window.image_scale_mode.setCurrentIndex(1)
            window.image_cell_percent.setValue(92.5)
            window.refresh()
            self.assertTrue(window.preview.params)
            self.assertIsNotNone(window._library_session)
            self.assertEqual(len(window._library_session.missing),1)
            first=window._library_session
            save_glyph(root/'佛.png')
            window.refresh()
            self.assertIsNot(first,window._library_session)
            self.assertFalse(window._library_session.missing)
            data=window.settings_data(); config.write_text(json.dumps(data),encoding='utf-8')
            restored=Window(); self.addCleanup(restored.close)
            self.assertEqual(restored.settings_data(),data)
            self.assertEqual(restored.image_cell_percent.value(),92.5)
            tabs=restored.findChild(QTabWidget); tabs.setCurrentIndex(3)
            for width,height in ((1920,1080),(1366,768),(1280,720)):
                restored.resize(width,height); restored.show(); APP.processEvents(); APP.processEvents()
                self.assertEqual(restored.settings_scroll.horizontalScrollBar().maximum(),0)
                self.assertEqual(tabs.widget(3).horizontalScrollBar().maximum(),0)
                self.assertGreater(restored.preview.width(),500)
            restored.text_source.setCurrentIndex(0)
            self.assertTrue(restored.fonts[0].isEnabled())
            restored.refresh()
            self.assertNotIn('_image_session',restored.preview.params)

    def test_export_button_pipeline_full_canvas_and_failure_feedback(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); library=root/'library'; library.mkdir()
            save_glyph(library/'序.png',color='red')
            save_glyph(library/'佛.png',color='blue')
            config=root/'settings.json'
            settings=dict(main.BUILTIN_SETTINGS)
            settings.update(image_params(library),text='序\n佛缺',outdir=str(root/'output'),
                            filename='按钮导出',frames=[1]*4,margins=[5]*4,
                            offset_x=0,offset_y=0,title_offset_x=0,title_offset_y=0)
            config.write_text(json.dumps(settings),encoding='utf-8')
            class Window(main.MainWindow):
                def settings_path(self): return config
            window=Window(); self.addCleanup(window.close)
            # 输出不能取当前预览的缩放、平移或窗口尺寸。
            window.preview.zoom=5
            window.preview.pan.setX(-10000)
            expected=main.render_layout_image(window.values(),window.text.toPlainText())
            with patch.object(main.QMessageBox,'information') as information, \
                 patch.object(main.QMessageBox,'warning') as warning:
                for format,extension in (('PNG','png'),('JPG','jpg'),('PSD/PSB','psd')):
                    window.format.setCurrentText(format)
                    window.export()
                    path=root/'output'/('按钮导出.'+extension)
                    self.assertTrue(path.is_file())
                    self.assertGreater(path.stat().st_size,0)
                    self.assertIn('缺少图片 1 字',information.call_args.args[2])
                    if extension=='psd':
                        doc=PSDImage.open(path)
                        layers=[layer for group in doc if group.is_group() for layer in group]
                        self.assertEqual(len(layers),2)
                        self.assertFalse(any(layer.has_mask() for layer in layers))
                    else:
                        result=QImage(str(path))
                        self.assertEqual(result.size(),expected.size())
                        if extension=='png':
                            self.assertEqual(bytes(result.constBits()),bytes(expected.constBits()))
                warning.assert_not_called()
                information.reset_mock()
                window.format.setCurrentText('PNG')
                with patch.object(main,'render_layout_image',side_effect=OSError('模拟写入失败')):
                    window.export()
                information.assert_not_called()
                self.assertIn('模拟写入失败',warning.call_args.args[2])

    def test_validation_invalid_paths_and_bounded_cache(self):
        for changes in ({'image_scale_percent':0}, {'image_enlarge_threshold':150},
                        {'image_scale_percent':float('nan')}):
            p=dict(IMAGE_DEFAULTS); p.update(text_source='images',**changes)
            with self.assertRaises(ValueError): image_settings(p)
        for path in ('','__不存在的字库目录__'):
            with self.assertRaises(ValueError): LibraryIndex.scan(path,'character')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); save_glyph(root/'甲.png',size=(10,10)); save_glyph(root/'乙.png',size=(10,10))
            cache=AssetCache(byte_limit=500)
            cache.get(root/'甲.png'); cache.get(root/'乙.png')
            self.assertLessEqual(cache.bytes,500)
            self.assertEqual(list(cache.items),[root/'乙.png'])
            cache=AssetCache(byte_limit=100)
            loaded=cache.get(root/'甲.png')
            self.assertEqual(loaded.image.size,(10,10))
            self.assertFalse(cache.items)


if __name__=='__main__': unittest.main()
