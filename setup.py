from setuptools import setup, find_packages
import os
import io
import sys

QARK_DIR = "qark"
LIB_DIR = os.path.join(QARK_DIR, "lib")

# قائمة الملفات المطلوبة للتثبيت
exploit_apk_files = [os.path.join(dir_path, filename).replace(os.path.join(QARK_DIR, ""), "")
                     for dir_path, _, files in os.walk(os.path.join(QARK_DIR, "exploit_apk"))
                     for filename in files]

with io.open('README.rst', 'rt', encoding='utf8') as f:
    long_description = f.read()

# وظيفة لإنشاء ملف qark التنفيذي
def create_qark_script():
    # استخدام مسار مفسر Python الحالي (الخاص بالبيئة الافتراضية)
    python_path = sys.executable
    # المسار النسبي لـ qark.py داخل المشروع
    qark_py_path = os.path.abspath(os.path.join(QARK_DIR, "qark.py"))
    # مسار السكربت التنفيذي
    qark_script_path = os.path.join(QARK_DIR, "qark")
    
    with open(qark_script_path, 'w') as f:
        f.write('#!/bin/sh\n')
        f.write(f'exec {python_path} {qark_py_path} "$@"\n')
    os.chmod(qark_script_path, 0o755)  # جعل الملف قابلًا للتنفيذ

# إنشاء السكربت أثناء التثبيت
create_qark_script()

setup(
    name="qark",
    version="4.0.0",
    packages=find_packages(exclude=["tests*"]),
    package_dir={QARK_DIR: QARK_DIR},
    package_data={
        QARK_DIR: [
            os.path.join("lib", "decompilers", "*.jar"),
            os.path.join("lib", "apktool", "*.jar"),
            os.path.join("lib", "dex2jar-2.0", "*"),
            os.path.join("lib", "dex2jar-2.0", "lib", "*"),
            os.path.join("templates", "*.jinja"),
        ] + exploit_apk_files,
    },
    install_requires=[
        "requests[security]",
        "pluginbase",
        "jinja2",
        "javalang",
        "click",
        "six",
    ],
    author="Tushar Dalvi & Tony Trummer",
    author_email="tushardalvi@gmail.com, tonytrummer@hotmail.com",
    description="Android static code analyzer",
    long_description=long_description,
    license="Apache 2.0",
    keywords="android security qark exploit",
    url="https://www.github.com/linkedin/qark",
    entry_points="""
        [console_scripts]
        qark=qark.qark:cli""",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3.6",
    ],
    scripts=[os.path.join(QARK_DIR, "qark")],
)