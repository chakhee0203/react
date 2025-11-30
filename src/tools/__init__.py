from .general import web_search, calculator, current_time
from .files import python_interpreter, list_uploaded_files
from .dev import json_formatter, hash_generator, encoding_tool, timestamp_converter, qrcode_generator, sql_formatter
from .office import excel_to_csv_from_upload, csv_to_excel_from_upload, markdown_to_html
from .image import (
    image_resize_base64,
    image_convert_base64,
    image_crop_base64,
    image_compress_base64,
    image_rotate_base64,
    image_add_text_watermark_base64,
    image_add_image_watermark_base64,
    image_remove_watermark_base64,
    image_upload_to_base64,
    image_crop_upload,
    image_compress_upload,
    image_rotate_upload,
    image_add_text_watermark_upload,
    image_add_image_watermark_upload,
    image_remove_watermark_upload,
)

def get_tools():
    return [
        web_search, 
        calculator, 
        current_time, 
        python_interpreter, 
        list_uploaded_files,
        json_formatter,
        hash_generator,
        encoding_tool,
        timestamp_converter,
        qrcode_generator,
        sql_formatter,
        excel_to_csv_from_upload,
        csv_to_excel_from_upload,
        markdown_to_html,
        image_resize_base64,
        image_convert_base64,
        image_crop_base64,
        image_compress_base64,
        image_rotate_base64,
        image_add_text_watermark_base64,
        image_add_image_watermark_base64,
        image_remove_watermark_base64,
        image_upload_to_base64,
        image_crop_upload,
        image_compress_upload,
        image_rotate_upload,
        image_add_text_watermark_upload,
        image_add_image_watermark_upload,
        image_remove_watermark_upload,
    ]
