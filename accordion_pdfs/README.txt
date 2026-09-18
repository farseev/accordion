Put the accordion score PDFs in THIS folder.

The Score Library page (library.html) looks for each score at
    accordion_pdfs/<filename>.pdf
relative to the site root — e.g. accordion_pdfs/Albenis_I__Asturija.pdf

Copy the contents of
    https://github.com/farseev/accordion/tree/main/accordion_pdfs
into this folder, keeping the file names exactly as they are.
743 scores are listed; every filename in scores-data.js must match a file here.

Nothing else needs changing. If you ever host the PDFs somewhere else, add
    <script>window.ACCSG_PDFBASE="https://your-host/path/";</script>
before scores.js in library.html (and the six <lang>-library.html files).
