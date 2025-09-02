#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import json, re, shutil, threading, traceback, webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
ROOT_LABELS = {"bookmark_bar": "Bookmarks Bar","other": "Other Bookmarks","synced": "Mobile Bookmarks"}
_NAT_SPLIT = re.compile(r'(\d+)')
@dataclass
class SortOptions: numbers_first_titles: bool = False
def _natural_key(s: str) -> Tuple[Tuple[int, object], ...]:
    s_cf = (s or "").casefold(); parts = _NAT_SPLIT.split(s_cf); key: List[Tuple[int, object]] = []
    for p in parts:
        if not p: continue
        key.append((1, int(p)) if p.isdigit() else (0, p))
    return tuple(key)
def _leading_digit_class(name: str) -> int:
    if not name: return 1
    n = name.lstrip(); i = 0
    while i < len(n) and n[i].isdigit(): i += 1
    return 0 if i > 0 else 1
def load_bookmarks(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8"); data = json.loads(text)
    if not isinstance(data, dict) or "roots" not in data or not isinstance(data["roots"], dict):
        raise ValueError("Invalid structure: missing 'roots' dict at top level.")
    return data
def sort_children(children: List[Dict[str, Any]], opts: SortOptions) -> Tuple[List[Dict[str, Any]], bool]:
    if not children: return [], False
    def key(n: Dict[str, Any]):
        t = str(n.get("type","")).lower(); name = n.get("name") or ""; url = n.get("url") or ""
        lead_class = _leading_digit_class(name) if opts.numbers_first_titles else 1
        return (0 if t=="folder" else 1, lead_class, _natural_key(name), _natural_key(url))
    out = sorted(children, key=key); return out, (out != children)
def _compute_reorder_count(before, after):
    b=[id(x) for x in before]; a=[id(x) for x in after]
    moves=sum(1 for i in range(min(len(b),len(a))) if b[i]!=a[i]); moves+=abs(len(b)-len(a)); return moves
def walk_and_sort(node, path_stack, opts, changes_log):
    folders=bookmarks=0; changed_any=False
    if str(node.get("type","")).lower()=="folder":
        folders+=1; before=list(node.get("children") or []); sorted_children,changed_here=sort_children(before,opts)
        if changed_here:
            node["children"]=sorted_children
            changes_log.append({"path":"/"+"/".join(path_stack),"reordered":_compute_reorder_count(before,sorted_children),"total_children":len(sorted_children)})
            changed_any=True
        else: node["children"]=before
        for child in node.get("children", []):
            if str(child.get("type","")).lower()=="folder":
                name=child.get("name") or ""; f,b,c=walk_and_sort(child, path_stack+[name], opts, changes_log)
                folders+=f; bookmarks+=b; changed_any=changed_any or c
            else: bookmarks+=1
    else: bookmarks+=1
    return folders, bookmarks, changed_any
def sort_all_roots(data, opts):
    changes_log=[]; folders=bookmarks=0; changed_any=False; roots=data.get("roots",{})
    for key in ("bookmark_bar","other","synced"):
        if key in roots and isinstance(roots[key], dict):
            display=ROOT_LABELS.get(key,key); f,b,c=walk_and_sort(roots[key],[display],opts,changes_log)
            folders+=f; bookmarks+=b; changed_any=changed_any or c
    return folders, bookmarks, changed_any, changes_log
def save_bookmarks(data, path): path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
def generate_html_report(data, out_path, changes_log, totals):
    import html as _html
    def esc(s:str)->str: return _html.escape(s or "", quote=True)
    def li_for(node):
        if str(node.get("type","")).lower()=="folder":
            name=esc(node.get("name") or ""); kids=node.get("children") or []; inner="".join(li_for(child) for child in kids)
            return f'<li><span class="folder">📁 {name}</span><ul>{inner}</ul></li>'
        else:
            name=esc(node.get("name") or ""); url=esc(node.get("url") or "")
            return f'<li><span class="url">🔗 <a href="{url}">{name or url}</a></span></li>'
    sections=[]; roots=data.get("roots",{})
    for key in ("bookmark_bar","other","synced"):
        if key in roots:
            label=ROOT_LABELS.get(key,key); sections.append(f"<h2>{label}</h2><ul class='tree'>{li_for(roots[key])}</ul>")
    changed_rows="\n".join(f"<tr><td><code>{esc(ch['path'])}</code></td><td>{ch['reordered']} / {ch['total_children']}</td></tr>" for ch in changes_log if ch["reordered"]>0) or '<tr><td colspan="2">None</td></tr>'
    style="<style>body{font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;}h1{margin-bottom:.25rem}.subtitle{color:#555;margin-bottom:1rem}.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.5rem 1rem;padding:.75rem;background:#f7f7f9;border:1px solid #e5e5ef;border-radius:8px;margin-bottom:1rem}.tree{list-style-type:none;padding-left:1rem}.tree ul{list-style-type:none;padding-left:1rem;margin:.35rem 0}.folder{font-weight:600}.url a{text-decoration:none}.url a:hover{text-decoration:underline}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:6px 8px}th{background:#f0f0f5;text-align:left}</style>"
    html=f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>Chrome Bookmarks Sort Preview</title>{style}</head><body><h1>Chrome Bookmarks Sort Preview</h1><div class="subtitle">Folders-first (A→Z), then bookmarks (A→Z) — by name (natural digits). URL tie-break for equal names.</div><div class="summary"><div><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div><div><strong>Folders:</strong> {totals["folders"]}</div><div><strong>Bookmarks:</strong> {totals["bookmarks"]}</div><div><strong>Folders Reordered:</strong> {sum(1 for ch in changes_log if ch["reordered"]>0)}</div></div>' + "".join(sections) + f'<h2>Changed Folders</h2><table><thead><tr><th>Folder Path</th><th>Reordered</th></tr></thead><tbody>{changed_rows}</tbody></table></body></html>'
    out_path.write_text(html, encoding="utf-8")
class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Chrome Bookmarks Sorter"); self.geometry("780x600"); self.minsize(720,540)
        self.var_input=tk.StringVar(); self.var_mode=tk.StringVar(value="inplace"); self.var_output=tk.StringVar()
        self.var_backup=tk.BooleanVar(value=True); self.var_dryrun=tk.BooleanVar(value=False)
        self.var_report=tk.StringVar(); self.var_numbers_first=tk.BooleanVar(value=False); self._build_ui()
    def _build_ui(self):
        pad={"padx":10,"pady":6}; frame=ttk.Frame(self); frame.pack(fill="x",**pad)
        ttk.Label(frame,text="Input Bookmarks JSON:").grid(row=0,column=0,sticky="w")
        ttk.Entry(frame,textvariable=self.var_input,width=70).grid(row=1,column=0,columnspan=2,sticky="we",pady=(0,4))
        ttk.Button(frame,text="Browse…",command=self._pick_input).grid(row=1,column=2,sticky="e")
        modef=ttk.LabelFrame(self,text="Output Mode"); modef.pack(fill="x",**pad)
        ttk.Radiobutton(modef,text="In-place (create backup)",variable=self.var_mode,value="inplace",command=self._refresh_state).grid(row=0,column=0,sticky="w",padx=8,pady=4)
        ttk.Checkbutton(modef,text="Backup (timestamped .bak)",variable=self.var_backup).grid(row=0,column=1,sticky="w",padx=8,pady=4)
        ttk.Radiobutton(modef,text="Write to file",variable=self.var_mode,value="output",command=self._refresh_state).grid(row=1,column=0,sticky="w",padx=8,pady=4)
        ttk.Entry(modef,textvariable=self.var_output,width=60).grid(row=1,column=1,sticky="we",padx=8,pady=4)
        ttk.Button(modef,text="Browse…",command=self._pick_output).grid(row=1,column=2,sticky="e",padx=8,pady=4)
        optf=ttk.LabelFrame(self,text="Options"); optf.pack(fill="x",**pad)
        ttk.Checkbutton(optf,text="Dry-run (do not write JSON)",variable=self.var_dryrun).grid(row=0,column=0,sticky="w",padx=8,pady=4)
        ttk.Label(optf,text="HTML Report (optional):").grid(row=1,column=0,sticky="w",padx=8,pady=4)
        ttk.Entry(optf,textvariable=self.var_report,width=60).grid(row=1,column=1,sticky="we",padx=8,pady=4)
        ttk.Button(optf,text="Browse…",command=self._pick_report).grid(row=1,column=2,sticky="e",padx=8,pady=4)
        ttk.Checkbutton(optf,text="Numbers-first titles (if name starts with digits)",variable=self.var_numbers_first).grid(row=2,column=0,columnspan=3,sticky="w",padx=8,pady=4)
        actf=ttk.Frame(self); actf.pack(fill="x",**pad)
        self.btn_run=ttk.Button(actf,text="Run Sort",command=self._on_run); self.btn_run.pack(side="left")
        ttk.Button(actf,text="Open Report",command=self._open_report).pack(side="left",padx=8)
        ttk.Button(actf,text="Help",command=self._show_help).pack(side="right")
        logf=ttk.LabelFrame(self,text="Output"); logf.pack(fill="both",expand=True,**pad)
        self.txt=tk.Text(logf,height=16,wrap="word"); self.txt.pack(fill="both",expand=True,padx=8,pady=8); self._refresh_state()
    def _pick_input(self):
        p=filedialog.askopenfilename(title="Select Chrome Bookmarks JSON",filetypes=[("Bookmarks file","Bookmarks"),("JSON","*.json"),("All files","*.*")])
        if p: self.var_input.set(p)
    def _pick_output(self):
        p=filedialog.asksaveasfilename(title="Save sorted JSON as…",defaultextension=".json",filetypes=[("JSON","*.json"),("All files","*.*")])
        if p: self.var_output.set(p)
    def _pick_report(self):
        p=filedialog.asksaveasfilename(title="Save HTML report as…",defaultextension=".html",filetypes=[("HTML","*.html"),("All files","*.*")])
        if p: self.var_report.set(p)
    def _refresh_state(self): pass
    def _append(self,s:str): self.txt.insert("end",s+"\n"); self.txt.see("end"); self.update_idletasks()
    def _open_report(self):
        rpt=self.var_report.get().strip()
        if not rpt: messagebox.showinfo("No report path","Specify a report path first (Options → HTML Report)."); return
        p=Path(rpt).expanduser()
        if p.exists(): webbrowser.open(p.as_uri())
        else: messagebox.showwarning("Not found",f"Report file not found:\n{p}")
    def _show_help(self):
        messagebox.showinfo("Help","1) Choose your Chrome 'Bookmarks' JSON file (see chrome://version for Profile Path).\n2) Pick In-place (backup is recommended) or write to a new file.\n3) Optional: Dry-run + HTML report to preview before writing.\n4) Click Run Sort. When done, check the Output pane.\n\nTip: Close Chrome when doing in-place writes so it won't overwrite your changes.\nIf Sync reorders things, Pause Sync or Reset Sync, then re-enable after verifying.")
    def _on_run(self):
        t=threading.Thread(target=self._run_worker,daemon=True); self.btn_run.config(state="disabled"); t.start()
    def _run_worker(self):
        try:
            self._append("=== Chrome Bookmarks Sort ===")
            input_path=Path(self.var_input.get().strip()).expanduser()
            if not input_path.exists(): messagebox.showerror("Input not found",f"File not found:\n{input_path}"); return
            mode=self.var_mode.get()
            out_path=Path(self.var_output.get().strip()).expanduser() if mode=="output" else None
            dry_run=self.var_dryrun.get()
            report_path=Path(self.var_report.get().strip()).expanduser() if self.var_report.get().strip() else None
            backup=self.var_backup.get() if mode=="inplace" else False
            opts=SortOptions(numbers_first_titles=self.var_numbers_first.get())
            self._append(f"Loading: {input_path}"); data=load_bookmarks(input_path); target=json.loads(json.dumps(data))
            folders,bookmarks,changed_any,changes_log=sort_all_roots(target,opts)
            if report_path:
                try:
                    report_path.parent.mkdir(parents=True,exist_ok=True); generate_html_report(target,report_path,changes_log,{"folders":folders,"bookmarks":bookmarks})
                    self._append(f"Report written: {report_path}")
                except Exception as e: self._append(f"Report failed: {e}")
            changed_folders=sum(1 for ch in changes_log if ch["reordered"]>0)
            total_reorders=sum(ch["reordered"] for ch in changes_log)
            self._append(f"Folders visited:   {folders}"); self._append(f"Bookmarks visited: {bookmarks}")
            self._append(f"Folders changed:   {changed_folders}"); self._append(f"Total reorders:    {total_reorders}")
            if changed_folders:
                self._append("Changed folders:")
                for ch in changes_log:
                    if ch["reordered"]>0: self._append(f"  {ch['path']}: {ch['reordered']} / {ch['total_children']}")
            if dry_run: self._append("Dry-run: no JSON written."); return
            if mode=="output":
                if not out_path: messagebox.showerror("Missing output","Choose an output file when 'Write to file' is selected."); return
                out_path.parent.mkdir(parents=True,exist_ok=True); save_bookmarks(target,out_path); self._append(f"Sorted JSON written to: {out_path}")
            elif mode=="inplace":
                if backup:
                    try:
                        ts=datetime.now().strftime("%Y-%m-%d_%H%M%S"); bak_path=input_path.with_name(f"{input_path.name}.{ts}.bak")
                        shutil.copyfile(input_path,bak_path); self._append(f"Backup created: {bak_path}")
                    except Exception as e: self._append(f"Backup failed: {e}")
                save_bookmarks(target,input_path); self._append(f"In-place sort complete: {input_path}")
            else: self._append("No write mode selected (this should not happen).")
        except Exception as e:
            self._append("ERROR:\n"+ "".join(traceback.format_exc())); messagebox.showerror("Error",str(e))
        finally: self.btn_run.config(state="normal")
if __name__=="__main__": App().mainloop()
