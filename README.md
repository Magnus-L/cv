# Magnus Lodefalk — CV

LaTeX sources for the three CV versions. On every push to `main`, a GitHub Action
compiles all three with [Tectonic](https://tectonic-typesetting.github.io) and publishes
the PDFs to GitHub Pages at stable URLs.

**Live:** https://magnus-l.github.io/cv/

| File | Output | Use |
|------|--------|-----|
| `Lodefalk_CV_Short.tex` | [Lodefalk_CV_Short.pdf](https://magnus-l.github.io/cv/Lodefalk_CV_Short.pdf) | 3-page short CV |
| `Lodefalk_CV.tex` | [Lodefalk_CV.pdf](https://magnus-l.github.io/cv/Lodefalk_CV.pdf) | standard academic CV |
| `Lodefalk_CV_Comprehensive.tex` | [Lodefalk_CV_Comprehensive.pdf](https://magnus-l.github.io/cv/Lodefalk_CV_Comprehensive.pdf) | full record |

## Updating

Edit a `.tex` file, then commit and push:

```bash
git add . && git commit -m "Update CV" && git push
```

The live PDFs refresh automatically in ~2 minutes. Point any external page
(personal website, lab site, ORU profile) at the stable URLs above — they never change.
