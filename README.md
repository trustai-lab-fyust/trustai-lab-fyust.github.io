# TrustAI Lab 主页

安全可信智能联合实验室（Joint Laboratory of Trustworthy and Secure Intelligence，TrustAI Lab）对外主页。
纯静态站点：内容在 `data/*.yaml`，模板在 `templates/`，样式在 `assets/css/main.css`，
运行 `python3 build.py` 生成 `dist/`。中文站在 `dist/` 根目录，英文简版在 `dist/en/`。

## 目录

```
data/            内容（改这里）
  site.yaml      名称、一句话定位、简介、地址、邮箱、导航、界面文案
  research.yaml  三个研究方向
  people.yaml    成员（教师 / 博士生 / 硕士生 / 本科生与实习生 / 校友）
  publications.yaml  论文
  news.yaml      新闻动态
  join.yaml      加入我们
templates/       页面模板（一般不用改）
assets/          样式、logo、成员照片（assets/img/people/）
build.py         生成脚本
tests/           构建自检
dist/            生成结果，可直接上传
.github/workflows/pages.yml  GitHub Actions 自动发布
```

## 本机生成与预览

依赖：Python 3.9+，`pip install jinja2 pyyaml`（自检另需 `pytest`）。

```bash
python3 build.py                     # 生成 dist/
python3 -m pytest -q tests           # 自检：页面齐全、链接有效、英文页无中文
python3 -m http.server -d dist 8000  # 浏览器打开 http://localhost:8000
```

## 常见更新

- 加学生：在 `data/people.yaml` 按注释里的示例增加一条，`tier` 填 `phd` / `master` / `intern` / `alumni`；
  照片放 `assets/img/people/<id>.jpg` 并填 `photo: <id>.jpg`，不放照片会自动生成首字母占位图。
- 加论文：在 `data/publications.yaml` 增加一条，`id` 唯一，`year` 决定排序；想在研究方向页展示，把 `id` 加进
  `data/research.yaml` 对应方向的 `highlights`。
- 加动态：在 `data/news.yaml` 增加一条，`date` 写 `YYYY-MM` 或 `YYYY-MM-DD`。
- 改招生说明：`data/join.yaml`。
- 改后运行 `python3 build.py`，把 `dist/` 一起提交。

## 上线

### 方式一：GitHub Pages，自动构建（推荐）

1. 注册 GitHub 账号，新建组织（Organization），例如 `trustai-lab-fyust`。
2. 在组织下新建公开仓库，名字必须是 `<组织名>.github.io`，例如 `trustai-lab-fyust.github.io`。
3. 把本目录全部文件上传到仓库的 `main` 分支（网页端 "Add file → Upload files" 拖进去即可，或用 git push）。
4. 仓库 Settings → Pages → Build and deployment → Source 选 **GitHub Actions**。
5. 等 Actions 跑完，站点地址为 `https://<组织名>.github.io/`。以后每次提交自动重建。

### 方式二：GitHub Pages，只上传生成结果

把 `dist/` 里的全部文件（含隐藏文件 `.nojekyll`）上传到仓库根目录，Settings → Pages → Source 选
"Deploy from a branch"，分支 `main`，目录 `/ (root)`。

### 方式三：腾讯云 EdgeOne Pages（国内访问更快）

1. 注册腾讯云国际站 EdgeOne（https://pages.edgeone.ai/ ），不需要备案。
2. 新建 Pages 项目：导入上面的 GitHub 仓库，构建命令 `pip install jinja2 pyyaml && python3 build.py`，
   输出目录 `dist`；或者直接上传 `dist/` 压缩包。
3. 得到 `https://<项目名>.edgeone.app/`。

### 自定义域名

有域名后，在 GitHub Pages 或 EdgeOne 的设置里绑定即可；学校子域名（如 `trustai.fyust.edu.cn`）需请学校网络中心
把 CNAME 指到对应平台给出的地址。
