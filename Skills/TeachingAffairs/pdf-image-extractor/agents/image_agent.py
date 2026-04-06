#!/usr/bin/env python3
"""
图片处理代理
负责提取、处理和优化PDF中的图片
"""

import hashlib
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import io
from PIL import Image


@dataclass
class ImageInfo:
    """图片信息"""
    xref: int
    page: int
    index: int
    data: bytes
    format: str
    width: int
    height: int
    hash: str
    bbox: Optional[Tuple[float, float, float, float]]
    image_type: str  # 'vector' or 'raster'
    colorspace: Optional[str]


class ImageAgent:
    """图片处理代理"""
    
    # 支持的图片格式
    SUPPORTED_FORMATS = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'gif', 'webp']
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化图片处理代理
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.min_size = self.config.get('min_image_size', 50)
        self.max_size = self.config.get('max_image_size', 5000)
        self.deduplicate = self.config.get('deduplicate', True)
        self.image_hashes = set()
        
        # 图片处理选项
        self.convert_to_rgb = self.config.get('convert_to_rgb', False)
        self.resize_large = self.config.get('resize_if_large', None)
        self.optimize = self.config.get('optimize', False)
        self.quality = self.config.get('image_quality', 85)
    
    def extract_from_page(self, page, page_num: int, doc) -> List[ImageInfo]:
        """
        从页面提取图片
        
        Args:
            page: PyMuPDF页面对象
            page_num: 页码
            doc: PyMuPDF文档对象
            
        Returns:
            ImageInfo列表
        """
        images = []
        image_list = page.get_images(full=True)
        
        for idx, img in enumerate(image_list, 1):
            xref = img[0]
            
            try:
                # 提取图片数据
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue
                
                image_bytes = base_image["image"]
                image_ext = base_image["ext"].lower()
                
                # 格式检查
                if image_ext not in self.SUPPORTED_FORMATS:
                    continue
                
                # 获取图片尺寸
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)
                
                # 尺寸过滤
                if width < self.min_size or height < self.min_size:
                    continue
                if width > self.max_size or height > self.max_size:
                    if not self.resize_large:
                        continue
                
                # 去重检查
                img_hash = hashlib.md5(image_bytes).hexdigest()[:16]
                if self.deduplicate and img_hash in self.image_hashes:
                    continue
                
                # 处理图片
                processed_data = self._process_image(image_bytes, image_ext, width, height)
                if processed_data is None:
                    continue
                
                # 判断图片类型
                img_type = self._classify_image_type(base_image)
                
                # 获取图片位置
                bbox = self._get_image_bbox(page, xref)
                
                image_info = ImageInfo(
                    xref=xref,
                    page=page_num + 1,
                    index=idx,
                    data=processed_data[0],
                    format=processed_data[1],
                    width=processed_data[2],
                    height=processed_data[3],
                    hash=img_hash,
                    bbox=bbox,
                    image_type=img_type,
                    colorspace=base_image.get("colorspace")
                )
                
                self.image_hashes.add(img_hash)
                images.append(image_info)
                
            except Exception as e:
                print(f"  警告: 提取图片失败 (xref={xref}): {e}")
        
        return images
    
    def _process_image(self, image_bytes: bytes, original_format: str,
                      original_width: int, original_height: int) -> Optional[Tuple[bytes, str, int, int]]:
        """
        处理图片（转换格式、调整大小、优化等）
        
        Returns:
            (processed_bytes, format, width, height) 或 None
        """
        try:
            # 打开图片
            img = Image.open(io.BytesIO(image_bytes))
            
            width, height = original_width, original_height
            out_format = original_format
            
            # 转换为RGB
            if self.convert_to_rgb:
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                out_format = 'jpg'  # RGB转为JPEG
            
            # 调整大小
            if self.resize_large and (width > self.resize_large or height > self.resize_large):
                ratio = min(self.resize_large / width, self.resize_large / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                width, height = new_width, new_height
            
            # 优化
            if self.optimize:
                # 保存到字节流
                output = io.BytesIO()
                save_kwargs = {'optimize': True}
                
                if out_format.lower() == 'jpg' or out_format.lower() == 'jpeg':
                    save_kwargs['quality'] = self.quality
                    save_kwargs['subsample'] = 2
                
                img.save(output, format=out_format.upper(), **save_kwargs)
                processed_bytes = output.getvalue()
                
                # 如果优化后文件更大，使用原图
                if len(processed_bytes) > len(image_bytes):
                    return image_bytes, original_format, original_width, original_height
                
                return processed_bytes, out_format, width, height
            
            return image_bytes, original_format, original_width, original_height
            
        except Exception as e:
            print(f"  图片处理失败: {e}")
            return None
    
    def _classify_image_type(self, base_image: Dict) -> str:
        """判断图片类型（矢量图或位图）"""
        ext = base_image.get("ext", "").lower()
        if ext in ["svg", "wmf", "emf", "eps"]:
            return "vector"
        return "raster"
    
    def _get_image_bbox(self, page, xref: int) -> Optional[Tuple]:
        """获取图片在页面上的位置"""
        try:
            # 遍历页面内容查找图片位置
            for img in page.get_images():
                if img[0] == xref:
                    # PyMuPDF 不直接提供位置，需要解析页面内容
                    # 这里返回None，后续可以通过其他方式获取
                    return None
        except Exception:
            pass
        return None
    
    def get_image_stats(self, images: List[ImageInfo]) -> Dict:
        """获取图片统计信息"""
        if not images:
            return {}
        
        total_size = sum(len(img.data) for img in images)
        
        return {
            'total_count': len(images),
            'total_size_mb': total_size / (1024 * 1024),
            'unique_hashes': len(set(img.hash for img in images)),
            'formats': list(set(img.format for img in images)),
            'types': {
                'vector': sum(1 for img in images if img.image_type == 'vector'),
                'raster': sum(1 for img in images if img.image_type == 'raster')
            },
            'avg_width': sum(img.width for img in images) / len(images),
            'avg_height': sum(img.height for img in images) / len(images)
        }
    
    def save_image(self, image_info: ImageInfo, filepath: Path) -> bool:
        """保存图片到文件"""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(image_info.data)
            return True
        except Exception as e:
            print(f"保存图片失败: {e}")
            return False