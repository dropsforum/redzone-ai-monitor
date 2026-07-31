# YOLO26 Model Operations

This project uses the official `yolo26n.pt` checkpoint with **Ultralytics
8.4.112**. The browser production path is the checked-in application code
using ONNX Runtime Web and a locally supplied ONNX artifact. LiteRT/WebGPU and
CoreML FP16 are experimental benchmark candidates only; they must not become
defaults based on vendor speed claims alone.

## Reproducible exports

Create an environment with the pinned exporter:

```bash
python -m pip install ultralytics==8.4.112 onnx
```

The helper prints its settings without importing Ultralytics:

```bash
python scripts/export_yolo26n.py --format onnx --dry-run
```

Browser ONNX export, including YOLO26 end-to-end output, uses 640 input,
opset 17, batch 1, static input, and no graph simplification:

```bash
python scripts/export_yolo26n.py \
  --format onnx \
  --weights yolo26n.pt \
  --output-dir public/models \
  --force
```

The resulting model is expected to have input `(1, 3, 640, 640)` and final
detection output `(1, 300, 6)` containing `xyxy`, confidence, and class ID.
This end-to-end output does not receive a second NMS pass.

LiteRT and CoreML exports default to the external user cache so that no model
binary is accidentally added to this public repository:

```bash
python scripts/export_yolo26n.py --format litert --weights yolo26n.pt
python scripts/export_yolo26n.py --format coreml --weights yolo26n.pt
```

LiteRT is exported as FP32 with `end2end=False`; the traditional head lets the
official browser package keep inference on its WebGPU delegate and perform
postprocessing outside the model. LiteRT uses FP16 at runtime through a
compatible GPU delegate rather than a separate FP16 export. CoreML uses
`quantize=16` with `end2end=False` for the experimental FP16 artifact so
Ultralytics handles the traditional detection head's postprocessing.

Run the experimental Mac backend against the external CoreML package with:

```bash
python run_ai_app.py \
  --backend coreml \
  --model ~/Library/Caches/redzone-ai-monitor/yolo26n-exports/yolo26n.mlpackage
```

If `--model` is omitted, the app checks that cache path or
`REDZONE_COREML_MODEL`. It does not fall back to PyTorch while reporting itself
as CoreML.

## Verified export record

The commands above were executed on 2026-07-31 with Ultralytics `8.4.112`.
The source `yolo26n.pt` checkpoint SHA-256 was
`9b09cc8bf347f0fc8a5f7657480587f25db09b34bf33b0652110fb03a8ad4fef`.

| Artifact | Settings | Size | SHA-256 |
| --- | --- | ---: | --- |
| `yolo26n.onnx` | `imgsz=640`, opset 17, static batch 1, `end2end=True`, no simplify | 9,895,498 bytes | `e3499344c85da34d3f17119fb6a78b170f64f5ec139f92e112a6fdc010b84486` |
| `yolo26n.tflite` | `imgsz=640`, batch 1, `end2end=False` | 9,970,397 bytes | `358c7ccc3fc035818d8a80c3d2ff0db239e10679f47663d6ee53d10ca0777495` |
| `yolo26n.mlpackage` | `imgsz=640`, batch 1, `quantize=16`, `end2end=False` | 5,067,660 bytes | `5905faeb8ab9cc9e679c126709eeaae2674a0dfe800608e1dac036bb74a807c8` |

The verified ONNX graph exposes input `[1,3,640,640]` and output
`[1,300,6]`. The CoreML package loaded through the experimental detector and
completed a frame inference. These hashes describe this verification run;
artifacts remain untracked and the generated provenance manifest is stored in
the external user cache.

An unlabelled 100-frame performance smoke, after 10 warmup frames on the same
local recording, measured PyTorch/MPS at 10.89 ms median end-to-end latency and
CoreML at 7.14 ms. CoreML was about 34% faster in that narrow run and both
backends reported zero detector errors. The result is stored outside the repo
as `~/Library/Caches/redzone-ai-monitor/benchmark-smoke-mac.json`.

This is not a promotion result. The footage was not established as
representative and had no ground-truth breach labels, so breach recall, missed
breaches, and false alerts per hour remain unevaluated. PyTorch/MPS therefore
remains the production Mac default.

## Provenance and hashes

Generate a manifest for any file or package directory. Directory hashes are
deterministic over sorted relative file names and file hashes:

```bash
python scripts/generate_model_provenance.py \
  public/models/yolo26n.onnx \
  --source-model yolo26n.pt \
  --ultralytics-version 8.4.112 \
  --export-command 'python scripts/export_yolo26n.py --format onnx --weights yolo26n.pt --output-dir public/models --force'
```

The default manifest path is outside the repository. Add one `--export-command`
argument for each command used when producing a set of artifacts. Do not put
absolute local paths, credentials, or private footage names in a committed
manifest.

## Benchmark capture

Create a blank result template outside the repository:

```bash
python scripts/create_benchmark_template.py
```

Record the baseline and candidate on the same representative footage, after
the same warmup count. Capture preprocessing, inference, postprocessing and
end-to-end latency, observed FPS, breach recall, false alerts per hour and
missed breaches. A candidate may become a default only when it is at least 20%
faster at median end-to-end latency, loses no more than one percentage point of
breach recall, does not increase missed breaches or false alerts, and passes
packaging and fallback checks.

No footage, screenshots, clips, model binaries, or benchmark output files are
stored by these scripts. The existing `.gitignore` excludes
`public/models/*.onnx`; LiteRT, CoreML, provenance, and benchmark files default
to the user cache outside the repository. Keep any manually selected
repository-local output outside tracked paths unless an ignore rule is added
in a separate change.

References: [Ultralytics export guide](https://docs.ultralytics.com/modes/export/),
[LiteRT integration](https://docs.ultralytics.com/integrations/litert/), and
[CoreML integration](https://docs.ultralytics.com/integrations/coreml/).
