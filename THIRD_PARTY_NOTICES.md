# Exposure Zone Monitoring - Third-Party Notices

## Project Licence

The repository's [LICENSE](LICENSE) identifies **AGPL-3.0-or-later**. The [GNU AGPL text](https://www.gnu.org/licenses/agpl-3.0.html) governs the source licence. Dependency and model terms remain separate. This document is an upstream-reference inventory and release-review checklist, not a complete copy of every bundled copyright/licence notice or a legal compliance certification.

The product is **Exposure Zone Monitoring**; its repository remains `dropsforum/redzone-ai-monitor`. On publication, the requested public **v1.2.0-rc.1 AGPL evaluation preview** will distribute corresponding application/build source at the [exact release tag](https://github.com/dropsforum/redzone-ai-monitor/tree/v1.2.0-rc.1), together with upstream licence/source references and the [Qt replacement/rebuild/re-sign route](docs/desktop-releases.md#replacing-qt-libraries-and-rebuilding). Public tag/binary availability is not yet confirmed. Production/operational licensing suitability is a separate external decision; it is not presented as an unresolved choice of licence for this public AGPL preview. Distribution obligations still apply, and source links alone are not a blanket compliance certificate.

Packaging includes full GNU AGPL/GPL/LGPL licence texts explicitly, including where Qt wheel contents omit them. Maintainers must verify these texts, applicable copyright/dependency notices and matching source references in both final renamed artifacts. Inclusion of licence texts is not a blanket compliance certificate. Legacy session/cache folder names are intentionally retained for compatibility and history continuity, not a different product or licence.

## Native Dependencies

Versions below are source requirements where pinned, not a verified inventory of published binaries. The release coordinator must capture actual resolved versions and bundled/transitive components in build evidence and preserve their applicable notices and licence texts.

| Component | Source requirement / role | Upstream licence and authoritative reference |
| --- | --- | --- |
| Python | Native interpreter/runtime | PSF License Version 2 and incorporated-component terms: [Python history and licence](https://docs.python.org/3/license.html) |
| Ultralytics | `8.4.146`; model loading, inference and tracking | AGPL-3.0 or commercial/Enterprise terms: [official licensing](https://www.ultralytics.com/license), [upstream licence](https://github.com/ultralytics/ultralytics/blob/main/LICENSE) |
| YOLO26n weights | Default `yolo26n-seg.pt` or detection option `yolo26n.pt`; separately downloaded on first use with pinned SHA-256 | Ultralytics model terms apply too: [official licensing](https://www.ultralytics.com/license), [official v8.4.0 assets](https://github.com/ultralytics/assets/releases/tag/v8.4.0) |
| PySide6 / Shiboken6 / Qt | PySide6 `6.11.1`; native UI and shared libraries | LGPLv3/GPLv3 community or commercial options, depending on component/distribution: [Qt for Python licensing](https://doc.qt.io/qtforpython-6/commercial/index.html), [Qt third-party licences](https://doc.qt.io/qtforpython-6/licenses.html) |
| PyTorch / torchvision | Mac `torch==2.12.0`, `torchvision==0.27.0`; Windows `2.12.0+cpu` / `0.27.0+cpu`; MPS/CPU inference | BSD-style with component notices: [PyTorch licence](https://github.com/pytorch/pytorch/blob/main/LICENSE), [torchvision licence](https://github.com/pytorch/vision/blob/main/LICENSE) |
| OpenCV / opencv-python | `4.13.0.92`; capture and image processing | OpenCV Apache-2.0; wheel/bundled components have additional terms: [OpenCV licence](https://github.com/opencv/opencv/blob/4.x/LICENSE), [opencv-python licensing](https://github.com/opencv/opencv-python#licensing) |
| NumPy | `>=1.26.0,<3.0.0`; arrays | BSD-3-Clause and incorporated-component notices: [NumPy licence](https://numpy.org/doc/stable/license.html) |
| Pillow | `>=10.0.0,<13.0.0`; image processing | HPND-style PIL/Pillow terms and component notices: [Pillow licence](https://github.com/python-pillow/Pillow/blob/main/LICENSE) |
| pygame | `2.6.1`; alert audio | LGPL; retain applicable pygame/SDL notices: [pygame official documentation](https://www.pygame.org/docs/) |
| PyInstaller | `6.21.0`; build/bundling tool | GPL-2.0 with a custom bundling exception; some files Apache-2.0: [PyInstaller licence and exception](https://pyinstaller.org/en/v6.21.0/license.html) |

Other direct and transitive requirements (including LAP, PyYAML, python-dateutil, Qt plugins, SDL, numerical libraries and media codecs) must be inventoried from the actual build. This table is not a substitute for their licence texts. The web integration also has separate npm/ONNX Runtime Web dependencies; native notices do not establish web redistribution compliance.

## Production and Operational Licensing Gate

Ultralytics offers AGPL-3.0 and commercial licensing paths for its code and models. The requested public preview uses the open-source AGPL path with corresponding source and upstream references. A first-use download rather than bundled weights does not remove model terms or settle all distribution obligations. Licensing suitability for a proposed production or operational deployment, particularly proprietary integration, remains an **external gate for that deployment**: assess the intended use and obligations or obtain appropriate commercial terms. Public preview publication is not operational approval.

Neither "free for all commercial use" nor "every enterprise use always requires a paid licence" is asserted here. Assess the actual distribution, integration and use against the [official Ultralytics terms](https://www.ultralytics.com/license) and [AGPL](https://www.gnu.org/licenses/agpl-3.0.html); obtain qualified advice or clarification from the licensor where needed. A public repository and a model download are not, by themselves, evidence of compliance.

## Qt Shared Libraries and User Rights

The native packages bundle dynamically linked PySide6/Qt shared libraries in PyInstaller onedir layouts. The [replacement/rebuild instructions](docs/desktop-releases.md#replacing-qt-libraries-and-rebuilding) explain replacing compatible libraries or rebuilding with modified wheels, and re-signing a personal Mac copy without the distributor's key. For the applicable LGPL route, preserve licence/copyright notices, provide corresponding library source or a compliant source offer (including changes), and enable recipients to replace/relink libraries and run the modified result. Do not restrict reverse engineering needed to debug those modifications. References: [Qt LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations), [Qt for Python source/build guidance](https://doc.qt.io/qtforpython-6/), [official Qt for Python source distributions](https://download.qt.io/official_releases/QtForPython/), [official Qt source distributions](https://download.qt.io/official_releases/qt/), [LGPLv3 text](https://www.gnu.org/licenses/lgpl-3.0.html).

Some Qt modules have GPL-only community terms; audit the shipped modules rather than assuming every Qt component is LGPL. Maintainers must match upstream source versions and notices to the actual bundled libraries, preserve required licence texts and review the documented replacement route against the final artifacts. The upstream references and dynamic packaging design are not a blanket certification that every redistribution or modification complies.

## Distribution Review

PyInstaller's exception permits bundling applications without imposing PyInstaller's GPL on the entire generated bundle, but it does not waive dependency or project obligations. See [the official exception](https://pyinstaller.org/en/v6.21.0/license.html).

Before release, retain all required dependency notices and licence texts in the actual packages, reconcile them with resolved versions and transitive native libraries, and provide the required source/installation information. Verify that no model weights or private data were packaged. Signing, notarization, build success and an evaluation label do not replace licensing review. No blanket commercial-use permission or legal warranty is provided.
