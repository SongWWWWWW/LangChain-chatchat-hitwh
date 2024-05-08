# -*- coding: utf-8 -*-
"""
loguru 封装类，导入即可直接使用
# 当前文件名 logger.py
"""
import sys
from functools import wraps
import os
import datetime
import loguru


# 单例类的装饰器
def singleton_class_decorator(cls):
    """
    装饰器，单例类的装饰器
    """
    # 在装饰器里定义一个字典，用来存放类的实例。
    _instance = {}

    # 装饰器，被装饰的类
    @wraps(cls)
    def wrapper_class(*args, **kwargs):
        # 判断，类实例不在类实例的字典里，就重新创建类实例
        if cls not in _instance:
            # 将新创建的类实例，存入到实例字典中
            _instance[cls] = cls(*args, **kwargs)
        # 如果实例字典中，存在类实例，直接取出返回类实例
        return _instance[cls]

    # 返回，装饰器中，被装饰的类函数
    return wrapper_class


@singleton_class_decorator # 这是一个单例类，单例类是指一个类只能实例化一个对象
class Logger:
    def __init__(self, log_dir=None):
        self.log_dir = log_dir or self.get_default_log_dir()
        self.logger_add()

    def get_default_log_dir(self):
        # 获取当前脚本的目录
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        # 默认日志目录设置为当前脚本目录下的 'log' 文件夹
        return os.path.join(current_script_dir, 'log')

    def get_log_format(self):
        # 定义日志格式，将MAC地址放在日期时间之前
        return f"{{time:YYYY-MM-DD HH:mm:ss.SSS}} | {{level: <8}} | {{name}}:{{function}}:{{line}} - {{message}}"


    def get_log_path(self):
        # 日志文件名
        project_log_filename = 'runtime_{}.log'.format(datetime.date.today())
        # 日志文件路径
        project_log_path = os.path.join(self.log_dir, project_log_filename)
        # 返回日志路径
        return project_log_path

    def logger_add(self):
        loguru.logger.add(
            sink=self.get_log_path(),
            rotation='00:00',
            retention='1 year',
            compression='zip',
            encoding="utf-8",
            enqueue=True,
            format=self.get_log_format()
        )

        # # 控制台日志，同样更新filter函数
        # loguru.logger.add(
        #     sink=sys.stdout,
        #     format=self.get_log_format()
        # )


    @property
    def get_logger(self):
        return loguru.logger

logger = Logger().get_logger

if __name__ == '__main__':
    '''
    # 实例化日志类
    '''
    logger = Logger().get_logger
    logger.debug('调试代码')
    logger.info('输出信息')
    logger.success('输出成功')
    logger.warning('错误警告')
    logger.error('代码错误')
    logger.critical('崩溃输出')

    """
    pip install loguru 

    """
    logger.info('----原始测试----')
