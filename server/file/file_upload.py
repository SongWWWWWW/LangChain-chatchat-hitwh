import os
from fastapi import UploadFile
from typing import List

async def upload_file(files: List[UploadFile] = ...):
    # 使用 os.path.expanduser 来正确解析用户主目录的路径
    print(files[0])
    if len(files) > 1:
        return {"false":"设定可上传文件数量为1,请不要超过此长度文件数量"}
    local_path = os.path.expanduser("~/wcc/Langchain-Chatchat/save_pdf/")
    # 确保目标目录存在
    os.makedirs(local_path, exist_ok=True)
    result = []
    for file in files:
        try:
            # # 使用 os.path.join 来安全地拼接路径
            file_path = os.path.join(local_path, file.filename)
            # # file.save(file_path)
            # with open(file_path, "w")as f:
            #     f.write(await file)
            # # await f.save(file_path)  # 保存文件
            # result.append(file.filename)  # 添加成功的文件名到结果列表
            filebytes = file.file.read()
            # name = file.filename
            with open(file_path,'wb') as f:
                f.write(filebytes)
            result.append(file.filename)
        except Exception as e:
            # 将异常信息记录到日志或单独处理，而不是添加到结果列表中
            print(f"{file.filename}: {e}")

    return {"files_uploaded": result}