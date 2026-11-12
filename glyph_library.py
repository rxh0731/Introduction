"""图片字库索引、解码、毫米尺寸和任务内缓存；不依赖 FontMgr 的环境。"""
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass
import math
from pathlib import Path
import re

from PIL import Image, ImageChops, ImageOps
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage


IMAGE_DEFAULTS = dict(
    text_source='font', library_dir='', library_naming='character',
    image_alignment='full', image_scale_mode='physical', image_scale_percent=100.0,
    image_auto_scale=True, image_enlarge_threshold=75.0, image_enlarge_target=95.0,
    image_shrink_threshold=150.0, image_shrink_target=95.0, image_cell_percent=95.0,
)
SUPPORTED_EXTENSIONS = frozenset({'.png', '.jpg', '.jpeg', '.jpe', '.tif', '.tiff',
    '.psd', '.psb', '.gif', '.bmp', '.dib', '.webp', '.ico', '.ppm', '.pgm', '.pbm'})
DEFAULT_SOURCE_DPI = 300.0


def image_settings(params):
    p = dict(IMAGE_DEFAULTS)
    p.update(params)
    for key, choices in (
        ('text_source', ('font', 'images')), ('library_naming', ('character', 'paragraph')),
        ('image_alignment', ('full', 'crop')), ('image_scale_mode', ('physical', 'cell')),
    ):
        if p[key] not in choices:
            raise ValueError('文字来源或字库选项无效，请重新选择。')
    if p['text_source'] == 'images':
        active = ('image_cell_percent',) if p['image_scale_mode'] == 'cell' else ('image_scale_percent',)
        if p['image_scale_mode'] == 'physical' and p['image_auto_scale']:
            active += ('image_enlarge_threshold', 'image_enlarge_target',
                       'image_shrink_threshold', 'image_shrink_target')
        for key in active:
            if not isinstance(p[key], (int, float)) or not math.isfinite(p[key]) or p[key] <= 0:
                raise ValueError('字库缩放比例、阈值和目标必须是大于零的有限数值。')
        if p['image_scale_mode'] == 'physical' and p['image_auto_scale']:
            if p['image_enlarge_threshold'] >= p['image_shrink_threshold']:
                raise ValueError('自动放大阈值必须小于自动缩小阈值。')
    return p


def natural_key(path):
    # 将名称中的数字按数值排列，例如 佛2 在 佛10 之前，目录名和扩展名也参与排序。
    return tuple((0, int(part)) if part.isdigit() else (1, part.casefold())
                 for part in re.split(r'(\d+)', str(path)))


@dataclass
class LibraryIndex:
    root: Path
    images: dict
    file_count: int
    issues: list

    @classmethod
    def scan(cls, directory, naming):
        if not str(directory).strip():
            raise ValueError('请选择字库目录。')
        root = Path(directory).expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f'字库目录不存在或无法访问：{root}')
        groups, issues = defaultdict(list), []
        def walk_error(error):
            issues.append(f'目录无法读取：{error.filename}（{error.strerror}）')
        files = []
        for parent, _, names in root.walk(on_error=walk_error, follow_symlinks=False):
            files.extend(parent / name for name in names if Path(name).suffix.lower() in SUPPORTED_EXTENSIONS)
        files.sort(key=lambda path: (natural_key(path.relative_to(root)), str(path)))
        for path in files:
            if naming == 'paragraph':
                match = re.fullmatch(r'([1-9]\d*)\.([1-9]\d*)', path.stem)
                if not match:
                    issues.append(f'未按“段落号.字序号”命名，已跳过：{path.relative_to(root)}')
                    continue
                key = f'{int(match[1])}.{int(match[2])}'
            else:
                key = path.stem[0]
            groups[key].append(path)
        if naming == 'paragraph':
            for key, paths in groups.items():
                if len(paths) > 1:
                    issues.append(f'编码 {key} 对应 {len(paths)} 个文件，使用排序第一项：{paths[0].relative_to(root)}')
        return cls(root, dict(groups), len(files), issues)


@dataclass
class LoadedImage:
    image: Image.Image
    dpi: float
    fallback_dpi: bool
    bounds: tuple


def _valid_dpi(value):
    if isinstance(value, (tuple, list)):
        value = value[0] if value else 0
    try:
        value = float(value)
    except (ValueError, TypeError):
        return 0.0
    return value if math.isfinite(value) and value > 0 else 0.0


def load_image(path):
    """多帧图像使用第1帧；PSD/PSB读取完整合成图，保留源图颜色和透明度。"""
    dpi = 0.0
    if path.suffix.lower() in ('.psd', '.psb'):
        from psd_tools import PSDImage
        from psd_tools.constants import Resource
        psd = PSDImage.open(path)
        resolution = psd.image_resources.get_data(Resource.RESOLUTION_INFO)
        if resolution is not None:
            dpi = _valid_dpi(resolution.horizontal / 65536)
            if resolution.horizontal_unit == 2:
                dpi *= 2.54
        source = psd.topil()
        if source is None:
            source = psd.composite()
        if source is None:
            raise ValueError('PSD/PSB 没有可用的合成图像')
        image = source.convert('RGBA')
        source.close()
    else:
        with Image.open(path) as source:
            dpi = _valid_dpi(source.info.get('dpi'))
            source.seek(0)
            oriented = ImageOps.exif_transpose(source)
            image = oriented.convert('RGBA')
            oriented.close()
    alpha = image.getchannel('A')
    if alpha.getextrema()[0] < 255:
        bounds = alpha.getbbox()
    else:
        # 不透明图片按接近纯白的边缘识别空白，容忍 JPEG 轻微压缩噪声。
        rgb = image.convert('RGB')
        diff = ImageChops.difference(rgb, Image.new('RGB', image.size, 'white'))
        r, g, b = diff.split()
        mask = ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda value: 255 if value > 5 else 0)
        bounds = mask.getbbox()
    if bounds is None:
        image.close()
        raise ValueError('图片没有可见内容')
    return LoadedImage(image, dpi or DEFAULT_SOURCE_DPI, not bool(dpi), bounds)


class AssetCache:
    """以像素字节数限制解码缓存，避免大字库长期占满内存。"""
    def __init__(self, byte_limit=96 * 1024 * 1024):
        self.byte_limit = byte_limit
        self.items = OrderedDict()
        self.bytes = 0

    def get(self, path):
        if path in self.items:
            self.items.move_to_end(path)
            return self.items[path]
        image = load_image(path)
        size = image.image.width * image.image.height * 4
        while self.items and self.bytes + size > self.byte_limit:
            _, removed = self.items.popitem(last=False)
            self.bytes -= removed.image.width * removed.image.height * 4
            removed.image.close()
        if size <= self.byte_limit:
            self.items[path] = image
            self.bytes += size
        return image


@dataclass(frozen=True)
class ImagePlacement:
    path: Path
    bounds: tuple
    # 图片实际物理尺寸（毫米）；已包括全局/自动/相对单元格缩放。
    width_mm: float
    height_mm: float

    def rect(self, cell_rect, scale):
        width, height = self.width_mm * scale, self.height_mm * scale
        return QRectF(cell_rect.center().x() - width / 2, cell_rect.center().y() - height / 2, width, height)


def target_size(params, glyph, loaded, bounds):
    width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    cell = glyph.cell
    if params['image_scale_mode'] == 'cell':
        factor = min(cell.w / width, cell.h / height) * params['image_cell_percent'] / 100
    else:
        factor = 25.4 / loaded.dpi * params['image_scale_percent'] / 100
        occupied = max(width * factor / cell.w, height * factor / cell.h) * 100
        if params['image_auto_scale']:
            if occupied <= params['image_enlarge_threshold']:
                factor *= params['image_enlarge_target'] / occupied
            elif occupied >= params['image_shrink_threshold']:
                factor *= params['image_shrink_target'] / occupied
    return width * factor, height * factor


class ImageSession:
    """一次刷新/输出的固定匹配结果，不随重绘次数改变轮换顺序。"""
    def __init__(self, params, text, glyphs, progress=None):
        self.signature = self.key(params, text)
        self.index = LibraryIndex.scan(params['library_dir'], params['library_naming'])
        self.cache = AssetCache()
        self.placements = {}
        self.issues = list(self.index.issues)
        self.missing = []
        self.fallbacks = set()
        self.failed = {}
        self.qt_cache = OrderedDict()
        self.qt_bytes = 0
        occurrences = Counter()
        for index, glyph in enumerate(glyphs):
            key = glyph.text if params['library_naming'] == 'character' else glyph.source_code
            variants = self.index.images.get(key, ())
            occurrence = occurrences[key]
            occurrences[key] += 1
            placement = None
            if variants:
                path = variants[occurrence % len(variants)] if params['library_naming'] == 'character' else variants[0]
                try:
                    if path in self.failed:
                        raise ValueError(self.failed[path])
                    loaded = self.cache.get(path)
                    bounds = loaded.bounds if params['image_alignment'] == 'crop' else (0, 0, *loaded.image.size)
                    width, height = target_size(params, glyph, loaded, bounds)
                    placement = ImagePlacement(path, bounds, width, height)
                    if loaded.fallback_dpi:
                        self.fallbacks.add(path)
                except Exception as exc:
                    if path not in self.failed:
                        self.failed[path] = str(exc)
                        self.issues.append(f'图片无法读取：{path.relative_to(self.index.root)}（{exc}）')
            if placement is None:
                self.missing.append(glyph)
            self.placements[glyph] = placement
            if progress is not None and (index % 10 == 0 or index + 1 == len(glyphs)):
                progress(index + 1, len(glyphs))

    @staticmethod
    def key(params, text):
        # 包括几何和偏移，但不包括临时缓存对象。
        return text, tuple((key, repr(value)) for key, value in sorted(params.items()) if not key.startswith('_'))

    @property
    def summary(self):
        return (f'字库文件 {self.index.file_count} 个｜索引 {len(self.index.images)} 项｜'
                f'匹配 {len(self.placements) - len(self.missing)}/{len(self.placements)} 字｜'
                f'缺图 {len(self.missing)} 字｜问题 {len(self.issues)} 项｜无 DPI {len(self.fallbacks)} 张（按300）')

    def report(self):
        lines = [self.summary, f'字库目录：{self.index.root}', '', '匹配记录（段落编码 → 图层名 → 文件）：']
        for glyph, placement in self.placements.items():
            path = str(placement.path.relative_to(self.index.root)) if placement else '未找到/无法读取，留空'
            lines.append(f'{glyph.source_code} → {glyph.layer_name} → {path}')
        lines += ['', '字库索引（同字字形按以下顺序轮换）：']
        for key, paths in self.index.images.items():
            lines.append(f'{key} → ' + '；'.join(str(path.relative_to(self.index.root)) for path in paths))
        if self.issues:
            lines += ['', '问题记录：', *self.issues]
        if self.fallbacks:
            lines += ['', '缺少有效 DPI，按 300 DPI 处理：', *(str(p.relative_to(self.index.root)) for p in sorted(self.fallbacks))]
        return '\n'.join(lines)

    def qimage(self, placement, width, height):
        key = (placement.path, placement.bounds, width, height)
        if key in self.qt_cache:
            self.qt_cache.move_to_end(key)
            return self.qt_cache[key]
        loaded = self.cache.get(placement.path)
        cropped = loaded.image.crop(placement.bounds)
        resized = cropped.resize((width, height), Image.Resampling.LANCZOS)
        image = QImage(resized.tobytes(), width, height, width * 4, QImage.Format_RGBA8888).copy()
        cropped.close()
        resized.close()
        size = image.sizeInBytes()
        while self.qt_cache and self.qt_bytes + size > 32 * 1024 * 1024:
            _, removed = self.qt_cache.popitem(last=False)
            self.qt_bytes -= removed.sizeInBytes()
        if size <= 32 * 1024 * 1024:
            self.qt_cache[key] = image
            self.qt_bytes += size
        return image


def prepare_images(params, text, glyphs, *, force=False, progress=None):
    p = image_settings(params)
    if p['text_source'] != 'images':
        return None
    session = p.get('_image_session')
    if force or session is None or session.signature != ImageSession.key(p, text):
        session = ImageSession(p, text, glyphs, progress)
    return session
