# imgconvert - 图片格式转换工具

支持 PDF、ICO、JPG、PNG 四种格式之间的相互转换。提供命令行和可视化 Web 界面两种使用方式。

## 快速上手（无需安装）

1. 前往 [Releases](https://github.com/Simon404Error/imgconvert/releases) 下载 `imgconvert-v1.0.0.zip`
2. 解压后双击 `imgconvert.exe`
3. 浏览器自动打开，上传文件即可转换

> Windows 10/11 64 位，无需安装 Python 或任何依赖。

## 一键部署（公网访问）

点击下方按钮，将项目免费部署到 Render，自动获得公网域名：

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Simon404Error/imgconvert)

部署后任何人通过 Render 分配的域名即可访问。

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

## 从源码安装

```bash
pip install -r requirements.txt
```

## 使用方式

### Web 可视化界面

**本地访问：**

```bash
python -m imgconvert serve
```

浏览器访问 `http://127.0.0.1:5080`，上传文件、选择目标格式，一键转换并下载。

**局域网共享（同网络下其他设备可访问）：**

```bash
python -m imgconvert serve -H 0.0.0.0
```

然后用本机 IP 地址访问，如 `http://192.168.1.100:5080`。

**公网访问（ngrok 隧道）：**

```bash
python -m imgconvert serve --ngrok
```

启动后自动生成公网 URL，分享即可。使用前需注册 [ngrok](https://ngrok.com) 并配置 authtoken。

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
