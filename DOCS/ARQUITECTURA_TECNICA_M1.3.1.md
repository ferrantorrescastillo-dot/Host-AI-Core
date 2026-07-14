# M1.3.1 — Arquitectura técnica

`ImportadorInteligenteRecetasM131` transforma texto, DOCX, PDF o XLSX en un `BorradorRecetaM131` común. El borrador conserva origen, nombre, rendimiento, ingredientes, elaboración y bloqueos. Solo cuando no hay bloqueos se convierte en payload para `ResolutorRecetasM13`.

Regla de catálogo: `M.P` es materia prima y puede proponerse como ingrediente. `A.P` es aperitivo/producto compuesto y queda fuera de la vinculación automática de ingredientes base. La resolución explícita de productos compuestos se desarrollará más adelante.

M1.3.1 no crea artículos faltantes ni resuelve conflictos anidados; genera bloqueos trazables para M1.3.2.
