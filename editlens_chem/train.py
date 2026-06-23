"""EditLens-Chem training (HPC / GPU). NOT run on the authoring machine.

Multi-task fine-tune (per PROTOCOL.md): RoBERTa-large with two heads on ~300-word
chunks -- (a) edit-extent regression in [0,1], (b) binary AI-touched presence. Optional
domain-adversarial year term (gradient-reversal) to strip period information and blunt
the style-drift confound (PROTOCOL.md S5).

Chunks inherit their variant's labels (whole-passage edits -> noisy for partial edits;
acknowledged in the protocol). Splits come from build_dataset.py (group-by-passage).

  # one grouped CV fold held out as validation:
  python editlens_chem/train.py --mode cv --val-fold 0 --base FacebookAI/roberta-large
  # leave-one-generator-out (the cross-generator generalization run):
  python editlens_chem/train.py --mode logo --holdout-generator gptoss-20b
  # ablation control: same architecture, but train on NON-chem edits (path provided)
  python editlens_chem/train.py --mode cv --val-fold 0 --manifest <nonchem_manifest>

Outputs a checkpoint + the val/test chunk-level predictions for evaluate.py.
"""
import argparse
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

TOK = re.compile(r"\S+")


def chunk_words(text, size=300, stride=250):
    w = text.split()
    if len(w) <= size:
        return [text]
    return [" ".join(w[i:i + size]) for i in range(0, max(1, len(w) - size + 1), stride)]


def load_manifest(path):
    return [json.loads(l) for l in open(path)]


def build_chunk_examples(rows):
    """explode variant rows into chunk-level (text, extent, presence, group, model, year)."""
    out = []
    for r in rows:
        for ch in chunk_words(r["text"]):
            out.append({"text": ch, "extent": r["extent"], "presence": r["presence"],
                        "passage": r["id"], "model": r["model"], "year": r["year"]})
    return out


def split_rows(rows, mode, val_fold, holdout_generator, splits):
    """return (train_rows, heldout_rows). Held-out = the generalization target."""
    pass_fold = {}  # passage -> cv fold, recomputed deterministically to match builder
    rng = np.random.default_rng(splits["seed"])
    passages = sorted({r["id"] for r in rows})
    rng.shuffle(passages)
    for i, p in enumerate(passages):
        pass_fold[p] = i % splits["cv_folds"]
    if mode == "cv":
        tr = [r for r in rows if pass_fold[r["id"]] != val_fold]
        ho = [r for r in rows if pass_fold[r["id"]] == val_fold]
    elif mode == "logo":
        # test = held-out generator's non-original variants; train = everything else
        ho = [r for r in rows if r["model"] == holdout_generator]
        tr = [r for r in rows if r["model"] != holdout_generator]
    else:
        raise ValueError(mode)
    return tr, ho


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(HERE, "manifest.jsonl"))
    ap.add_argument("--splits", default=os.path.join(HERE, "splits.json"))
    ap.add_argument("--mode", choices=["cv", "logo"], default="cv")
    ap.add_argument("--val-fold", type=int, default=0)
    ap.add_argument("--holdout-generator", default=None)
    ap.add_argument("--base", default="FacebookAI/roberta-large")
    ap.add_argument("--adversarial-year", action="store_true",
                    help="gradient-reversal year head to strip period signal (PROTOCOL S5)")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--limit", type=int, default=0,
                    help="cap train/heldout variant rows for a smoke test (0 = no cap)")
    ap.add_argument("--out", default=os.path.join(HERE, "runs"))
    a = ap.parse_args()

    rows = load_manifest(a.manifest)
    splits = json.load(open(a.splits))
    tr_rows, ho_rows = split_rows(rows, a.mode, a.val_fold, a.holdout_generator, splits)
    if a.limit:
        tr_rows = tr_rows[:a.limit]
        # keep heldout small but mixed (originals give the FPR negatives downstream)
        ho_rows = ([r for r in ho_rows if r["presence"] == 0][:a.limit // 4]
                   + [r for r in ho_rows if r["presence"] == 1][:a.limit // 4])
    tag = a.mode + (f"_fold{a.val_fold}" if a.mode == "cv" else f"_holdout-{a.holdout_generator}")
    print(f"[{tag}] train variants={len(tr_rows)} heldout variants={len(ho_rows)}")
    tr = build_chunk_examples(tr_rows)
    ho = build_chunk_examples(ho_rows)
    print(f"chunks: train={len(tr)} heldout={len(ho)}")

    # ---- model: RoBERTa-large encoder + regression head (+ presence head) ----------
    import torch
    from torch import nn
    from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
    from torch.utils.data import DataLoader, Dataset

    tok = AutoTokenizer.from_pretrained(a.base)

    class DS(Dataset):
        def __init__(self, ex): self.ex = ex
        def __len__(self): return len(self.ex)
        def __getitem__(self, i): return self.ex[i]

    def collate(batch):
        enc = tok([b["text"] for b in batch], truncation=True, max_length=512,
                  padding=True, return_tensors="pt")
        enc["extent"] = torch.tensor([b["extent"] for b in batch], dtype=torch.float)
        enc["presence"] = torch.tensor([b["presence"] for b in batch], dtype=torch.float)
        return enc

    class Net(nn.Module):
        def __init__(self, base):
            super().__init__()
            self.enc = AutoModel.from_pretrained(base)
            h = self.enc.config.hidden_size
            self.extent = nn.Linear(h, 1)
            self.presence = nn.Linear(h, 1)
        def forward(self, input_ids, attention_mask, **_):
            pooled = self.enc(input_ids=input_ids, attention_mask=attention_mask
                              ).last_hidden_state[:, 0]
            return self.extent(pooled).squeeze(-1), self.presence(pooled).squeeze(-1)

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    net = Net(a.base).to(dev)
    dl = DataLoader(DS(tr), batch_size=16, shuffle=True, collate_fn=collate)
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr)
    sched = get_linear_schedule_with_warmup(opt, int(0.06 * len(dl) * a.epochs),
                                            len(dl) * a.epochs)
    mse, bce = nn.MSELoss(), nn.BCEWithLogitsLoss()
    net.train()
    for ep in range(a.epochs):
        for step, enc in enumerate(dl):
            enc = {k: v.to(dev) for k, v in enc.items()}
            ext_pred, pres_pred = net(**enc)
            loss = mse(torch.sigmoid(ext_pred), enc["extent"]) + bce(pres_pred, enc["presence"])
            loss.backward(); opt.step(); sched.step(); opt.zero_grad()
            if step % 200 == 0:
                print(f"ep{ep} step{step}/{len(dl)} loss {loss.item():.4f}", flush=True)

    # ---- score held-out chunks, save predictions for evaluate.py -------------------
    net.eval()
    preds = []
    with torch.no_grad():
        for enc in DataLoader(DS(ho), batch_size=32, collate_fn=collate):
            ec = {k: v.to(dev) for k, v in enc.items() if k in ("input_ids", "attention_mask")}
            ext_pred, pres_pred = net(**ec)
            preds.extend(torch.sigmoid(ext_pred).cpu().tolist())
    for r, p in zip(ho, preds):
        r["pred_extent"] = p
    os.makedirs(a.out, exist_ok=True)
    outp = os.path.join(a.out, f"heldout_pred_{tag}.jsonl")
    with open(outp, "w") as f:
        for r in ho:
            f.write(json.dumps({k: r[k] for k in
                    ("passage", "model", "year", "extent", "presence", "pred_extent")}) + "\n")
    torch.save(net.state_dict(), os.path.join(a.out, f"editlens_chem_{tag}.pt"))
    print(f"wrote {outp} + checkpoint")


if __name__ == "__main__":
    main()
