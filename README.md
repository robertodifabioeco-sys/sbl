# Sito SBL – Milton Friedman Society

Sito statico bilingue (IT/EN) di friedmansociety.com, generato con Python a partire dai contenuti in `content/`.

## Struttura

- `content/articles_raw.json`: gli articoli scaricati dal vecchio sito Wix (testo originale, blocchi, immagini)
- `content/tr/<slug>.json`: traduzione di ogni articolo nell'altra lingua, più autore, categoria e sommario IT/EN
- `content/overrides.json`: correzioni a mano (categoria, autore, titolo, blocchi da togliere, `"cover": true` per forzare la copertina grafica)
- `content/site.json`: tutti i testi dell'interfaccia in italiano e in inglese, i social, gli indirizzi delle pagine
- `content/events.json`: le foto e le didascalie degli eventi
- `content/thinkers.json`: i pensatori, con citazioni e licenze delle immagini
- `src/`: CSS, JavaScript, font, immagini sorgente
- `tools/templates/`: i modelli delle pagine
- `tools/build.py`: genera il sito in `dist/`
- `dist/`: il sito pronto da pubblicare (non si modifica a mano)

## Comandi

```
python tools/build.py                 # genera il sito in dist/
python tools/check_links.py           # verifica che nessun link interno sia rotto
python -m http.server 8765 --directory dist   # anteprima su http://127.0.0.1:8765
```

Dipendenze: Python 3, `pip install pillow jinja2 beautifulsoup4 fonttools brotli`.

## Lingue e indirizzi

- Italiano alla radice: `/`, `/articoli/`, `/eventi/`, `/pensatori/`, `/chi-siamo/`, `/contatti/`
- Inglese sotto `/en/`: `/en/articles/`, `/en/events/`, `/en/thinkers/`, `/en/about/`, `/en/contact/`
- Ogni articolo esiste in entrambe le lingue; quella tradotta mostra un avviso con il link all'originale
- I vecchi indirizzi Wix (`/post/...`, `/articles`, `/about-us`...) reindirizzano alle pagine nuove, così i link già condivisi e Google non si rompono

## Aggiungere un articolo nuovo

Per ora si passa da Jarvis: gli si dà il testo (Word o Google Doc), autore, categoria e immagine. Lui lo aggiunge a `content/`, prepara la traduzione, rigenera e pubblica. Se manca l'immagine, il sito genera da solo una copertina grafica con i colori SBL.

## Immagini e licenze

I ritratti dei pensatori vengono da Wikimedia Commons, sono di pubblico dominio o hanno licenza libera; i crediti stanno nella pagina `/crediti/`. Il ritratto di Mises è CC BY-SA 3.0, quindi il credito va mantenuto.
