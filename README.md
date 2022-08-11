# AppPackageSizeDecrease

iOS App包体积优化脚本工具。包含的功能：无用图片清理，相似图片检测，图片压缩。
##### 执行环境
python3
##### 用到的工具
https://github.com/ggreer/the_silver_searcher  

https://github.com/ImageOptim/ImageOptim  

https://github.com/JamieMason/ImageOptim-CLI  

##### 使用介绍
- 无用图片检测：clear_unused_img.py
- 相似图片检测：clean_same_img_in_project.py
- 图片压缩：png_img_compress.py

打开python脚本，将root_path变量修改为项目路径，然后命令行执行
```
python3 xxx.py
```

##### 问题说明
- 错误：ModuleNotFoundError: No module named 'PIL'
  ```
  python3 -m pip install pillow
  ```
