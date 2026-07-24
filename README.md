# imgconvert - 图片格式转换工具

支持 PDF、ICO、JPG、PNG 四种格式之间的相互转换。提供命令行和可视化 Web 界面两种使用方式。

## 支持的转换

| 源格式 | 目标格式      |
|--------|--------------|
| PDF    | JPG, PNG, ICO |
| JPG    | PDF, PNG, ICO |
| PNG    | PDF, JPG, ICO |
| ICO    | PDF, JPG, PNG |

**转换说明：**
- PDF 转图片：每页以 200 DPI 渲染，多页 PDF 生成对应数量的图片（JPG/PNG/ICO 取首页）
- 图片转 PDF：保持原始尺寸，200 DPI
- ICO 输出：自动生成标准多尺寸（256、128、64、48、32、16 px）
- 透明 PNG/ICO 转 JPG 时自动合成为白底

## 安装

```bash
pip install -r requirements.txt
```

## 使用方式

### Web 可视化界面

启动本地 Web 服务，在浏览器中拖拽上传文件进行转换：

```bash
python -m imgconvert serve
```

浏览器访问 `http://127.0.0.1:5080`，上传文件、选择目标格式，一键转换并下载。

自定义地址和端口：

```bash
python -m imgconvert serve -H 0.0.0.0 -p 8080
```

### 命令行

**单文件转换（指定输出路径）：**

```bash
python -m imgconvert convert input.png output.jpg
```

**单文件转换（自动命名，`-f` 指定目标格式）：**

```bash
python -m imgconvert convert input.png -f .pdf
```

**批量转换：**

```bash
python -m imgconvert batch *.png -f .jpg -o ./converted/
```

**调整 JPEG 质量（默认 95）：**

```bash
python -m imgconvert convert input.png output.jpg -q 85
```
