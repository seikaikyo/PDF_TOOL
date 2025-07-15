#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
創建 PDF 合併工具的圖示檔案
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_icon():
    """創建應用程式圖示"""

    # 創建 256x256 的圖片
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 背景圓形
    margin = 20
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(52, 152, 219, 255),  # 藍色背景
        outline=(41, 128, 185, 255),
        width=3)

    # 繪製 PDF 文字
    try:
        # 嘗試使用系統字體
        font_size = 40
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # 如果沒有找到字體，使用預設字體
        font = ImageFont.load_default()

    # PDF 文字
    text = "PDF"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2 - 20

    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)

    # 繪製合併箭頭
    arrow_y = text_y + text_height + 10
    arrow_left = size // 2 - 30
    arrow_right = size // 2 + 30
    arrow_middle = size // 2

    # 左側文件
    draw.rectangle([arrow_left - 15, arrow_y, arrow_left - 5, arrow_y + 20],
                   fill=(255, 255, 255, 255))

    # 右側文件
    draw.rectangle([arrow_right + 5, arrow_y, arrow_right + 15, arrow_y + 20],
                   fill=(255, 255, 255, 255))

    # 箭頭
    draw.polygon([(arrow_left, arrow_y + 10), (arrow_middle - 5, arrow_y + 5),
                  (arrow_middle - 5, arrow_y + 8),
                  (arrow_right - 10, arrow_y + 8),
                  (arrow_right - 10, arrow_y + 12),
                  (arrow_middle - 5, arrow_y + 12),
                  (arrow_middle - 5, arrow_y + 15)],
                 fill=(255, 255, 255, 255))

    # 箭頭尖端
    draw.polygon([(arrow_right - 10, arrow_y + 5), (arrow_right, arrow_y + 10),
                  (arrow_right - 10, arrow_y + 15)],
                 fill=(255, 255, 255, 255))

    # 儲存不同尺寸的圖示
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []

    for s in sizes:
        if s == 256:
            images.append(img)
        else:
            resized = img.resize((s, s), Image.LANCZOS)
            images.append(resized)

    # 儲存為 ICO 檔案
    images[0].save('icon.ico', format='ICO', sizes=[(s, s) for s in sizes])
    print("圖示檔案 'icon.ico' 已創建完成！")

    # 同時儲存為 PNG 檔案以供預覽
    img.save('icon.png', format='PNG')
    print("預覽檔案 'icon.png' 已創建完成！")


if __name__ == "__main__":
    create_icon()
