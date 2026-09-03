# Templates

PostScript templates the PDF renderer can use, one `.ps` file each. Unlike the rest of `Resources/`, a file here is not a source document to extract facts from — it is part of how artifacts are produced.

A template here appears in the dashboard's template pickers as `vault:<file name without .ps>`, alongside the built-in designs. Pick one per application; leaving the picker on "Default" renders exactly as the application always has.

A template must declare which document it is for and must honour the prologue contract:

```postscript
% ce-kind: resume
% ce-param: left 54
```

`% ce-kind:` is `resume` or `cover-letter`; a file without it is ignored. `% ce-param:` lines declare layout numbers — margins, column positions, section order, sizes — that the renderer uses in place of its defaults. The full contract and every parameter are documented in the skill's `references/document-generation.md`.

A broken template is refused with the missing piece named; it is never rewritten to fit.

A `.ps` file is a program, and rendering runs it in Ghostscript on this machine. Treat a template from someone else the way you would treat any other program you were sent.
