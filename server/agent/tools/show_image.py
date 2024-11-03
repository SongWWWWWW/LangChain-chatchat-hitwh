from pydantic import BaseModel, Field
import streamlit as st
import os
import imghdr
def show_image(string: str): 
    def is_image_file(path):
        if os.path.exists(path) and os.path.isfile(path):
            try:
                img_format = imghdr.what(path)
                if img_format:
                    return True
                else:
                    return False
            except Exception as e:
                print(f"Error checking image format: {e}")
                return False
        else:
            return False

    if is_image_file(string):
        return st.image(string, caption="LLM's Image", use_column_width=True)
    else:
        return None
class ShowimageInput(BaseModel):
    string: str = Field(description="要展示图片文件的路径")