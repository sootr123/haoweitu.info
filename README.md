# haoweitu.info — HTU.

個人網站與作品集。純靜態網頁，放在 GitHub Pages。所有頁面都由 `content/` 裡的資料產生，**不要直接改 HTML**。

## 本機預覽

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

打開 http://127.0.0.1:8765/

## 檔案在哪

| 要改什麼 | 改這裡 |
| --- | --- |
| 作品（標題、說明、團隊、獎項、圖片、影片、順序） | `content/projects.json` |
| 每件作品的主圖、段落、圖片組合與版型 | `content/project-layouts.json` |
| 首頁介紹 | `content/home.json` |
| 首頁文章與演講浮動視窗、網站截圖 | `content/press.json`、`assets/press/` |
| index 每列的選圖、動畫與圖組寬度 | `content/index-layouts.json` |
| 簡介、獎項、媒體報導、聯絡連結 | `content/about.json` |
| 版面與樣式 | `assets/site.css` |
| 互動（中英切換、圖地圓形、作品亂序與篩選、影片） | `assets/site.js` |
| 首頁視窗（初始交疊、拖曳、縮放、關閉與重新開啟） | `assets/windows.js` |
| 產生頁面的程式 | `scripts/build_site.py` |
| 圖片尺寸與來源指紋（自動產生） | `content/images.json` |
| About 照片的預覽與展開版本（自動產生） | `content/about-images.json`、`assets/about/` |
| 影片尺寸、長度、來源指紋與擷取範圍（自動產生） | `content/media.json` |

`projects.json` 保留作品的基準順序，供產生頁面與作品內頁導覽使用。作品 index 每次進入時重新隨機排列；切換分類只篩選當次順序，不會重新洗牌。

下架的作品（含說明和圖片來源）都存在 `content/archive.json`，要放回網站就把那一筆搬回 `projects.json`，並在 `project-layouts.json` 補上版面，再跑一次下面的三個指令。重建時，已下架作品的頁面、圖片和影片會自動從網站資料夾移除；原始素材不會修改。

## 新增或修改作品

1. 在 `content/projects.json` 加一筆作品（照著現有的格式抄一份最快）。圖片的 `source` 可以直接指向原始檔，例如 `"~/Documents/TIGDA/DIGITAL/xxx.jpg"`，TIFF、PSD 合成圖、PNG、JPG 都可以。
2. 在 `content/project-layouts.json` 增加同一個作品 ID 的版面。`lead` 指定主圖；`sections` 逐段指定中英文標題、內文、圖片或影片。圖片說明放在 `projects.json` 各圖片的 `caption.en`／`caption.zh`。每張內頁圖片應安排一次，包含主圖。
3. 影片：在作品的 `media` 加一筆。
   - YouTube：`{"kind": "youtube", "id": "影片 ID", "title": {...}}`
   - 本機影片：`{"kind": "film", "name": "case-film", "source": "~/Documents/.../xxx.mp4", "title": {...}}`
   - 短的循環動畫或 GIF：`"kind": "loop"`，輸出為靜音 MP4。
   - 從影片擷取片段：加上秒數 `"start": 205, "duration": 14`，不會改動原影片。
   - 索引預覽：在 `content/index-layouts.json` 選定每件作品的圖片、動畫與圖組寬度；`kind` 可為 `image`、`loop` 或指定額外照片的 `custom`。只用於索引的片段設為 `"placement": "index"`。
4. 依序執行：

```sh
python3 scripts/build_images.py   # 只轉新增或來源改變的圖片（800 / 1600px WebP）
python3 scripts/build_about_images.py # About 照片：480px 浮圖、1200px 展開版，保留原檔
python3 scripts/build_media.py    # 只轉新增、來源或擷取範圍改變的影片
python3 scripts/build_site.py     # 重新產生所有頁面、sitemap、llms.txt
```

影片轉檔需要 ffmpeg，可使用 `brew install ffmpeg`，或以 `--ffmpeg /path/to/ffmpeg`／`HTU_FFMPEG` 指定現有程式。也支援已安裝的 `imageio-ffmpeg`。只處理某件作品可加 `--project endoaware`；需要強制重新轉檔時加 `--force`。轉檔程式記錄來源檔案指紋與時間範圍，未變更的輸出會沿用。影片來源與版本選擇記錄在 `content/media-selection.json`。

原始檔放在 `Por/`（已加入 `.gitignore`，不會上傳）或 `~/Documents` 都可以。網站使用 `assets/work/` 的 WebP、`assets/media/` 的壓縮影片與封面，以及 `assets/previews/` 的額外索引圖片。

## PDF 精選圖片

目前共有 15 件作品、53 張內頁圖片：12 件作品的 43 張圖片直接取自 `Por/HTU Portfolio.pdf`（2026-08-22，15 頁），另有 10 張原始素材，包含 Innovation Twenty 的藍色紙飛機、指定的畢業展海報與 Summer 的乾淨工具組照片。逐張 PDF 選圖記錄在 `content/portfolio-selection.json`。索引另行指定的照片放在 `assets/previews/`，不計入內頁圖片數量。

`projects.json` 的圖片可使用：

```json
{"file": "pdf-01", "alt": "作品畫面描述", "source_pdf": {"path": "Por/HTU Portfolio.pdf", "page": 3, "bbox": [56.693, 56.694, 768.189, 559.69]}}
```

`page` 從 1 起算，`bbox` 為 PDF points、左上角原點。產圖需要 Poppler（`brew install poppler`）；程式依 PDF 的既有圖片框輸出，保留原本背景、色彩、透明遮罩與向量元素，不再自動去背或裁黑邊。改變 PDF、頁碼或範圍後，執行 `python3 scripts/build_images.py` 會自動更新；沒有改變的圖會直接沿用。

個別圖片如需調整展示範圍，可明確設定 `display_crop`。Innovation Twenty 藍色海報的原始檔與輸出圖均保留黑色展示邊，頁面只透過 CSS 隱藏外側展示邊，使五張海報以接近的高度並排；海報本身的藍色設計背景保留。

網站輸出為 800 / 1600px WebP，品質 88。原始 PDF、素材和這次修改前的本機備份都不會上傳。`scripts/cutout.py` 為先前實驗保留，現有網站不再使用去背結果。

## 設計說明

- 首頁以 HTU. 識別與簡短介紹開場，不放散落的作品圖片。字樣只等比例調整字級，保留字型原始比例；句點為正方形。滑鼠掠過字樣時，小圓形局部反轉黑白；手機與偏好減少動態的裝置使用靜態構圖。
- 首頁的 Communication Arts、Swinburne 與 TEDx 是三個直式浮動視窗，直接覆在 HTU. 主視覺上，沒有獨立的文章區塊。初始位置在右側隨機交疊；視窗固定於畫面，可拖曳標題列、從角落調整尺寸、按 × 關閉，再由底部工具列開啟。□ 按鈕會在新分頁開啟各自的原網站，不會放大視窗。
- Communication Arts 使用指定的 `CA1.png`、`CA2.png` 接續顯示；Swinburne 使用網頁截圖與介紹。兩者均可在視窗內捲動，內容是本機預覽，原文連結保留。TEDx 採直式 YouTube 閱讀介面，影片由訪客點擊播放。
- 字體：Archivo、思源黑體（Noto Sans TC）。分類與正文保持正常層級，以留白、欄寬與段落節奏安排資訊。
- 作品總覽只使用索引排列，每次進入時隨機排序，可依分類篩選。每件作品依內容安排 1、2、3 或 5 個預覽，圖組靠右、組寬不同；Innovation Twenty 的五張海報全部並排，A Crack in Everything 的兩張書籍圖片使用較窄的圖組。沒有散落圖片模式或檢視切換，作品內頁使用各自的獨立編排。
- 五件作品的索引包含動態預覽。EndoAware 並列 3:25–3:39 的線條動畫與原有巴士動畫；D&AD 設計展在台灣 2023 也同時放兩個動態預覽。Projection Method 使用「9月12日」影片與指定的燈箱照片。預覽靜音循環，只在接近畫面時播放；可用「暫停動態」按鈕停止，減少動態偏好也會停用自動播放。
- 敲敲的索引改用指定的印刷品全景與 Behance 獎座兩張照片，動畫保留在作品內頁。Fishmonger 索引使用廚師拿魚與發光招牌照片。畢業展以指定的九張海報拼圖 `poster-main` 為主圖，索引也只顯示這一張；徽章與路燈旗合圖已撤下。
- Summer 索引保留 `case-preview` 動態，並列指定的乾淨工具組照片 `toolkit-clean`；作品內頁主圖也使用同一張照片，取代原本有文字覆蓋的 `pdf-01`。
- Downtown Grocer 索引使用 `01` 收銀台與 `06` 白牆上的圓形笑臉招牌；撤下的是 `03` 夜間發光、有文字的招牌與 `09` 禮盒照片。
- 每件作品內頁由 `content/project-layouts.json` 手動安排。完整主圖之後，以各段說明搭配等寬雙圖、海報組、四格動畫或單張圖片；書封、海報與寬幅照片各有一致的尺寸上限。Innovation Twenty 以粉紅海報為主圖，其餘四張海報並排。每張圖片都有對應說明，不再依圖片序號自動錯開大小。
- 最新 PDF 精選優先，補充素材依作品需要安排。先前去背的圖片已還原背景；原始圖片、來源資料與本機 `_archive/` 備份保留。
- About 的開場短文放在 `about.json` 的 `editorial`，既有完整簡歷仍可展開閱讀。設計實務、研究、TEDx、合作品牌、獲獎、教學交流與報導分段編排；手機將照片與短介紹並列。`selected_recognition` 決定先呈現的獎項，其餘歷年紀錄可展開。
- About 有照片的獎項、經歷與報導，滑鼠移入時顯示跟隨游標的預覽；展開照片時不重複浮出，離開、捲動或按 Escape 即收起。手機以展開按鈕看照片。圖片來源在各項 `gallery`，預覽與展開圖由 `build_about_images.py` 壓縮，不改動原始照片。
- HNZ「共同的結構」雙圖設定 `equal_height: true`，桌面依原圖比例分配欄寬，讓兩張照片等高、圖說對齊；手機維持直向閱讀。

## 發佈

確認預覽沒問題後 commit、push 到 GitHub，GitHub Pages 會自動更新網站。
